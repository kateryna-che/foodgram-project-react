from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription, User


class UserGetSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and obj.following.filter(user=request.user).exists())


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1, max_value=32767)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class IngredientGetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    amount = serializers.CharField(read_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGetSerializer(serializers.ModelSerializer):
    author = UserGetSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngredientGetSerializer(read_only=True, many=True,
                                          source='ingredients_recipe')
    image = Base64ImageField()
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'tags', 'name', 'image', 'text',
                  'cooking_time', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart')


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        allow_empty=False
    )
    ingredients = IngredientRecipeSerializer(many=True,
                                             source='ingredients_recipe')
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1, max_value=32767)

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'name', 'image',
                  'text', 'cooking_time', 'ingredients')

    def validate_tags(self, value):
        if len(value) < 1:
            raise serializers.ValidationError(
                'Необходимо выбрать хотя бы один тег'
            )
        tag_ids = set()
        for tag in value:
            if tag.id in tag_ids:
                raise serializers.ValidationError(
                    'Теги должны быть уникальными'
                )
            tag_ids.add(tag.id)
        return value

    def validate_ingredients(self, value):
        if len(value) < 1:
            raise serializers.ValidationError(
                'Необходимо выбрать как минимум один ингредиент'
            )
        ingredient_ids = set()
        for ingredient in value:
            if ingredient['id'] in ingredient_ids:
                raise serializers.ValidationError(
                    'Нельзя добавить два одинаковых ингредиента в рецепт.'
                )
            ingredient_ids.add(ingredient['id'])
        return value

    @staticmethod
    def create_ingredients(recipe, ingredients):
        ingredient_instances = [
            IngredientRecipe(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ]
        IngredientRecipe.objects.bulk_create(ingredient_instances)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients_recipe')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients_recipe')
        instance.tags.set(tags)
        IngredientRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeGetSerializer(instance, context=self.context).data


class SmallRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )
    user = serializers.PrimaryKeyRelatedField(
        default=serializers.CurrentUserDefault(),
        queryset=User.objects.all()
    )

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author'],
                message='Подписка невозможна')
        ]

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError('Нельзя подписаться на себя!')
        return data


class SubscribeListSerializer(UserGetSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count')

    class Meta(UserGetSerializer.Meta):
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        recipes_limit = self.context.get('recipes_limit', 3)
        queryset = obj.recipes.all()
        if recipes_limit is not None:
            queryset = queryset[:recipes_limit]
        return RecipeGetSerializer(
            queryset,
            many=True,
            context=self.context
        ).data


class BaseRelationshipCreateSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'

    def to_representation(self, instance):
        return SmallRecipeSerializer(
            instance.recipe,
            context=self.context
        ).data


class FavoriteCreateSerializer(BaseRelationshipCreateSerializer):
    class Meta(BaseRelationshipCreateSerializer.Meta):
        model = Favorite
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном'
            )
        ]


class ShoppingCartCreateSerializer(BaseRelationshipCreateSerializer):
    class Meta(BaseRelationshipCreateSerializer.Meta):
        model = ShoppingCart
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в списке покупок'
            )
        ]

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination, RecipesPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateSerializer,
                          RecipeGetSerializer, SmallRecipeSerializer,
                          SubscribeListSerializer, SubscribeSerializer,
                          TagSerializer)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [IsAuthorOrReadOnly, ]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeGetSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated, ], url_path='favorite')
    def add_to_favorite(self, request, pk=None):
        recipe = self.get_object()

        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(user=request.user, recipe=recipe)

            if created:
                serializer = SmallRecipeSerializer(recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'detail': 'Рецепт уже добавлен в избранное'}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            try:
                favorite = Favorite.objects.get(user=request.user, recipe=recipe)
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Favorite.DoesNotExist:
                return Response({'detail': 'Рецепт не найден в избранном'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated, ], url_path='shopping_cart')
    def add_to_shopping_cart(self, request, pk=None):
        recipe = self.get_object()

        if request.method == 'POST':
            shopping_cart, created = ShoppingCart.objects.get_or_create(user=request.user, recipe=recipe)

            if created:
                serializer = SmallRecipeSerializer(recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'detail': 'Рецепт уже добавлен в список покупок'}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            try:
                shopping_cart = ShoppingCart.objects.get(user=request.user, recipe=recipe)
                shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ShoppingCart.DoesNotExist:
                return Response({'detail': 'Рецепт не найден в списке покупок'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, ], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_recipes = Recipe.objects.filter(shopping_cart__user=user)
        ingredients_summary = {}
        for recipe in shopping_cart_recipes:
            ingredient_recipes = recipe.ingredients_recipe.all()
            for ingredient_recipe in ingredient_recipes:
                ingredient = ingredient_recipe.ingredient
                ingredient_key = (ingredient.name, ingredient.measurement_unit)
                if ingredient_key in ingredients_summary:
                    ingredients_summary[ingredient_key] += 1
                else:
                    ingredients_summary[ingredient_key] = 1
        content = "Список покупок:\n\n"
        for ingredient, amount in ingredients_summary.items():
            ingredient_name, ingredient_unit = ingredient
            content += f"{ingredient_name} - {amount} {ingredient_unit}\n"
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class SubscriptionsListView(generics.ListAPIView):
    serializer_class = SubscribeListSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(following__user=user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            results = response.data['results']
            results_with_recipes = []
            recipes_limit = int(request.GET.get('recipes_limit', 0))
            for user_data in results:
                user = user_data['id']
                recipes = Recipe.objects.filter(author=user)
                if recipes_limit > 0:
                    recipes = recipes[:recipes_limit]
                user_data['recipes'] = RecipeGetSerializer(recipes, many=True).data
                results_with_recipes.append(user_data)
            response.data['results'] = results_with_recipes
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SubscribeView(APIView):
    serializer_class = SubscribeSerializer

    def post(self, request, id, *args, **kwargs):
        author = get_object_or_404(User, id=id)
        data = {'user': request.user.id, 'author': author}
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        subscribed_user = User.objects.get(id=id)
        serializer = SubscribeListSerializer(subscribed_user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id, *args, **kwargs):
        author = get_object_or_404(User, id=id)
        Subscription.objects.filter(user=request.user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter

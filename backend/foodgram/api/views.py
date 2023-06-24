from django.db import models
from django.db.models import Exists, F, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (FavoriteCreateSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeGetSerializer,
                          ShoppingCartCreateSerializer,
                          SubscribeListSerializer,
                          SubscribeSerializer, TagSerializer)
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription, User


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [IsAuthorOrReadOnly, ]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(recipe=OuterRef('pk'),
                                            user=self.request.user)
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(recipe=OuterRef('pk'),
                                                user=self.request.user)
                )
            )
        else:
            queryset = queryset.annotate(
                is_favorited=models.Value(
                    False, output_field=models.BooleanField()
                ),
                is_in_shopping_cart=models.Value(
                    False, output_field=models.BooleanField()
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeGetSerializer
        return RecipeCreateSerializer

    @staticmethod
    def create_relation(serializer, recipe_pk, request):
        data = {
            'user': request.user.pk,
            'recipe': recipe_pk
        }
        serializer = serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_relation(model, recipe_pk, request):
        get_object_or_404(model, user=request.user, recipe=recipe_pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, ],
            url_path='favorite')
    def add_to_favorite(self, request, pk=None):
        recipe = self.get_object()
        serializer = FavoriteCreateSerializer
        return self.create_relation(serializer, recipe.pk, request)

    @add_to_favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        recipe = self.get_object()
        return self.delete_relation(Favorite, recipe.pk, request)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, ],
            url_path='shopping_cart')
    def add_to_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        serializer = ShoppingCartCreateSerializer
        return self.create_relation(serializer, recipe.pk, request)

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self.delete_relation(ShoppingCart, recipe.pk, request)

    @staticmethod
    def generate_shopping_list(queryset):
        content = "Список покупок:\n\n"
        for ingredient in queryset:
            ingredient_name = ingredient['ingredient_name']
            amount = ingredient['amount']
            measurement_unit = ingredient['measurement_unit']
            content += f"{ingredient_name} - {amount} {measurement_unit}\n"
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated, ],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_recipes = ShoppingCart.objects.filter(
            user=user
        ).values('recipe')
        ingredient_summary = IngredientRecipe.objects.filter(
            recipe__in=shopping_cart_recipes
        ).values(
            ingredient_name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount')).order_by('ingredient_name')
        return self.generate_shopping_list(ingredient_summary)


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
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SubscribeView(APIView):
    serializer_class = SubscribeSerializer

    def post(self, request, id, *args, **kwargs):
        author = get_object_or_404(User, id=id)
        data = {'user': request.user.id, 'author': author}
        serializer = self.serializer_class(data=data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id, *args, **kwargs):
        get_object_or_404(Subscription, user=request.user,
                          author__id=id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter

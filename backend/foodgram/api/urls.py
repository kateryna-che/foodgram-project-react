from django.urls import include, path
from rest_framework import routers

from .views import (
    IngredientViewSet,
    RecipeViewSet,
    SubscribeView,
    SubscriptionsListView,
    TagViewSet,
    UserViewSet,
)

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')

# Registered the way djoser.urls registers its own UserViewSet, so the
# routes and their names stay the same. The users/ routes go after
# users/subscriptions/, which would otherwise match users/<id>/.
users_router = routers.DefaultRouter()
users_router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('users/subscriptions/', SubscriptionsListView.as_view(),
         name='subscriptions'),
    path('users/<int:id>/subscribe/', SubscribeView.as_view(),
         name='subscribe'),
    path('', include(users_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

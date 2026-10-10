import pytest
from rest_framework import status

from factories import make_recipe
from recipes.models import Favorite, ShoppingCart

pytestmark = pytest.mark.django_db

RELATIONS = [('favorite', Favorite), ('shopping_cart', ShoppingCart)]
DOWNLOAD_URL = '/api/recipes/download_shopping_cart/'


def relation_url(recipe, action):
    return f'/api/recipes/{recipe.id}/{action}/'


@pytest.mark.parametrize('action, model', RELATIONS)
def test_add_recipe(user_client, user, recipe, action, model):
    response = user_client.post(relation_url(recipe, action))

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['id'] == recipe.id
    assert set(data) == {'id', 'name', 'image', 'cooking_time'}
    assert model.objects.filter(user=user, recipe=recipe).exists()


@pytest.mark.parametrize('action, model', RELATIONS)
def test_cannot_add_recipe_twice(user_client, user, recipe, action, model):
    model.objects.create(user=user, recipe=recipe)

    response = user_client.post(relation_url(recipe, action))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert model.objects.filter(user=user, recipe=recipe).count() == 1


@pytest.mark.parametrize('action, model', RELATIONS)
def test_anonymous_user_cannot_add_recipe(anon_client, recipe, action,
                                          model):
    response = anon_client.post(relation_url(recipe, action))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not model.objects.exists()


@pytest.mark.parametrize('action, model', RELATIONS)
def test_remove_recipe(user_client, user, recipe, action, model):
    model.objects.create(user=user, recipe=recipe)

    response = user_client.delete(relation_url(recipe, action))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not model.objects.exists()


@pytest.mark.parametrize('action, model', RELATIONS)
def test_remove_recipe_that_was_not_added(user_client, recipe, action,
                                          model):
    response = user_client.delete(relation_url(recipe, action))

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_relations_are_personal(another_client, user, recipe):
    """Another user's favorites do not mark the recipe for this user."""
    Favorite.objects.create(user=user, recipe=recipe)
    ShoppingCart.objects.create(user=user, recipe=recipe)

    response = another_client.get(f'/api/recipes/{recipe.id}/')

    data = response.json()
    assert data['is_favorited'] is False
    assert data['is_in_shopping_cart'] is False


def test_download_shopping_cart_sums_ingredients(user_client, user, tag,
                                                 flour, salt):
    pancakes = make_recipe(user, [tag], [(flour, 200)], name='Блины')
    bread = make_recipe(user, [tag], [(flour, 300), (salt, 5)], name='Хлеб')
    # Not in the cart: its 100 g of salt must not be counted.
    make_recipe(user, [tag], [(salt, 100)], name='Рассол')
    ShoppingCart.objects.create(user=user, recipe=pancakes)
    ShoppingCart.objects.create(user=user, recipe=bread)

    response = user_client.get(DOWNLOAD_URL)

    assert response.status_code == status.HTTP_200_OK
    assert response['Content-Type'].startswith('text/plain')
    assert 'attachment' in response['Content-Disposition']
    content = response.content.decode()
    assert 'Мука - 500 г' in content
    assert 'Соль - 5 г' in content
    assert 'Соль - 105 г' not in content


def test_download_shopping_cart_requires_authentication(anon_client):
    response = anon_client.get(DOWNLOAD_URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

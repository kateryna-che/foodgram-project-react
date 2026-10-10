import pytest
from rest_framework import status

from factories import make_recipe
from recipes.models import Favorite, IngredientRecipe, Recipe

pytestmark = pytest.mark.django_db

RECIPES_URL = '/api/recipes/'


def detail_url(recipe):
    return f'{RECIPES_URL}{recipe.id}/'


def test_recipes_list_is_public_and_paginated(anon_client, recipe):
    response = anon_client.get(RECIPES_URL)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['count'] == 1
    item = data['results'][0]
    assert item['name'] == recipe.name
    assert item['is_favorited'] is False
    assert item['is_in_shopping_cart'] is False


def test_recipes_list_page_size_limit(anon_client, user, tag, flour):
    for number in range(3):
        make_recipe(user, [tag], [(flour, 100)], name=f'Рецепт {number}')

    response = anon_client.get(RECIPES_URL, {'limit': 2})

    data = response.json()
    assert data['count'] == 3
    assert len(data['results']) == 2


def test_recipe_detail(anon_client, recipe, user, tag, flour):
    response = anon_client.get(detail_url(recipe))

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['author']['username'] == user.username
    assert [item['slug'] for item in data['tags']] == [tag.slug]
    assert data['ingredients'] == [{
        'id': flour.id,
        'name': flour.name,
        'measurement_unit': flour.measurement_unit,
        'amount': '200',
    }]


def test_create_recipe(user_client, user, recipe_payload, flour):
    response = user_client.post(RECIPES_URL, recipe_payload, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    recipe = Recipe.objects.get()
    assert recipe.author == user
    assert recipe.name == recipe_payload['name']
    assert recipe.image
    ingredient = IngredientRecipe.objects.get(recipe=recipe)
    assert (ingredient.ingredient, ingredient.amount) == (flour, 150)
    data = response.json()
    assert data['name'] == recipe_payload['name']
    assert data['image']


def test_anonymous_user_cannot_create_recipe(anon_client, recipe_payload):
    response = anon_client.post(RECIPES_URL, recipe_payload, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not Recipe.objects.exists()


@pytest.mark.parametrize('field, value', [
    ('ingredients', []),
    ('ingredients', [{'id': 999, 'amount': 10}]),
    ('ingredients', [{'id': 'FLOUR', 'amount': 0}]),
    ('ingredients', [{'id': 'FLOUR', 'amount': 10},
                     {'id': 'FLOUR', 'amount': 20}]),
    ('tags', []),
    ('tags', [999]),
    ('cooking_time', 0),
    ('name', ''),
])
def test_create_recipe_validation(user_client, recipe_payload, flour,
                                  field, value):
    if field == 'ingredients':
        value = [
            {**item, 'id': flour.id if item['id'] == 'FLOUR' else item['id']}
            for item in value
        ]
    recipe_payload[field] = value

    response = user_client.post(RECIPES_URL, recipe_payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert field in response.json()
    assert not Recipe.objects.exists()


def test_duplicate_tags_are_rejected(user_client, recipe_payload, tag):
    recipe_payload['tags'] = [tag.id, tag.id]

    response = user_client.post(RECIPES_URL, recipe_payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not Recipe.objects.exists()


def test_author_can_update_recipe(user_client, recipe, recipe_payload,
                                  another_tag, salt):
    recipe_payload.update({
        'name': 'Блины с солью',
        'tags': [another_tag.id],
        'ingredients': [{'id': salt.id, 'amount': 5}],
    })

    response = user_client.patch(
        detail_url(recipe), recipe_payload, format='json'
    )

    assert response.status_code == status.HTTP_200_OK
    recipe.refresh_from_db()
    assert recipe.name == 'Блины с солью'
    assert list(recipe.tags.all()) == [another_tag]
    ingredients = IngredientRecipe.objects.filter(recipe=recipe)
    assert [(item.ingredient, item.amount) for item in ingredients] == [
        (salt, 5)
    ]


@pytest.mark.parametrize('missing_field', ['tags', 'ingredients'])
def test_update_requires_tags_and_ingredients(user_client, recipe,
                                              recipe_payload, missing_field):
    del recipe_payload[missing_field]

    response = user_client.patch(
        detail_url(recipe), recipe_payload, format='json'
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert missing_field in response.json()


def test_other_user_cannot_update_recipe(another_client, recipe,
                                         recipe_payload):
    response = another_client.patch(
        detail_url(recipe), recipe_payload, format='json'
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    recipe.refresh_from_db()
    assert recipe.name == 'Блины'


def test_author_can_delete_recipe(user_client, recipe):
    response = user_client.delete(detail_url(recipe))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Recipe.objects.exists()


@pytest.mark.parametrize('client_name, expected_status', [
    ('anon_client', status.HTTP_401_UNAUTHORIZED),
    ('another_client', status.HTTP_403_FORBIDDEN),
])
def test_only_author_can_delete_recipe(request, recipe, client_name,
                                       expected_status):
    client = request.getfixturevalue(client_name)

    response = client.delete(detail_url(recipe))

    assert response.status_code == expected_status
    assert Recipe.objects.filter(id=recipe.id).exists()


def test_filter_by_author(anon_client, recipe, another_user, tag, flour):
    make_recipe(another_user, [tag], [(flour, 100)], name='Хлеб')

    response = anon_client.get(RECIPES_URL, {'author': another_user.id})

    assert [item['name'] for item in response.json()['results']] == ['Хлеб']


def test_filter_by_tags(anon_client, recipe, user, another_tag, flour):
    make_recipe(user, [another_tag], [(flour, 100)], name='Суп')

    response = anon_client.get(RECIPES_URL, {'tags': 'lunch'})

    assert [item['name'] for item in response.json()['results']] == ['Суп']


def test_filter_is_favorited(user_client, user, recipe, tag, flour):
    make_recipe(user, [tag], [(flour, 100)], name='Хлеб')
    Favorite.objects.create(user=user, recipe=recipe)

    response = user_client.get(RECIPES_URL, {'is_favorited': 1})

    results = response.json()['results']
    assert [item['name'] for item in results] == [recipe.name]
    assert results[0]['is_favorited'] is True

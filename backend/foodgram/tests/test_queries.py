"""The list endpoints make a fixed number of database queries.

Every test runs with one and with three authors, and the recipes have as
many tags and ingredients, but expects the same number of queries: a
query per object, the N+1 problem, makes the larger case fail.
"""
import pytest
from rest_framework import status

from factories import make_recipe, make_user
from recipes.models import Ingredient, Recipe, Tag
from users.models import Subscription

pytestmark = pytest.mark.django_db

RECIPES_URL = '/api/recipes/'
SUBSCRIPTIONS_URL = '/api/users/subscriptions/'

RECIPES_PER_AUTHOR = 3
RECIPES_LIMIT = 2
PAGE_SIZE = 6

# The tag choices of RecipeFilter, the count for the pagination, the page
# of recipes, then their authors, tags and ingredients.
RECIPES_LIST_QUERIES = 6
# The tag choices of RecipeFilter, the recipe, its author, tags and
# ingredients.
RECIPE_DETAIL_QUERIES = 5
# The count for the pagination, the page of authors and their recipes.
SUBSCRIPTIONS_QUERIES = 3


@pytest.fixture(params=[1, 3], ids=['1 author', '3 authors'])
def size(request):
    return request.param


@pytest.fixture
def authors(user, size):
    """size authors, all followed by user, with RECIPES_PER_AUTHOR recipes
    each; every recipe has size tags and size ingredients."""
    tags = [
        Tag.objects.create(name=f'Тег {number}', color='#E26C2D',
                           slug=f'tag-{number}')
        for number in range(size)
    ]
    ingredients = [
        (Ingredient.objects.create(name=f'Ингредиент {number}',
                                   measurement_unit='г'), 100)
        for number in range(size)
    ]
    authors = []
    for number in range(size):
        author = make_user(f'author{number}')
        for recipe_number in range(RECIPES_PER_AUTHOR):
            make_recipe(author, tags, ingredients,
                        name=f'Рецепт {number}-{recipe_number}')
        Subscription.objects.create(user=user, author=author)
        authors.append(author)
    return authors


@pytest.mark.parametrize('client_name', ['anon_client', 'user_client'])
def test_recipes_list(request, client_name, authors, size,
                      django_assert_num_queries):
    client = request.getfixturevalue(client_name)

    with django_assert_num_queries(RECIPES_LIST_QUERIES):
        response = client.get(RECIPES_URL)

    assert response.status_code == status.HTTP_200_OK
    results = response.json()['results']
    assert len(results) == min(size * RECIPES_PER_AUTHOR, PAGE_SIZE)
    for item in results:
        assert len(item['tags']) == size
        assert len(item['ingredients']) == size
        assert item['author']['is_subscribed'] is (
            client_name == 'user_client'
        )


def test_recipe_detail(user_client, authors, size,
                       django_assert_num_queries):
    recipe = Recipe.objects.first()

    with django_assert_num_queries(RECIPE_DETAIL_QUERIES):
        response = user_client.get(f'{RECIPES_URL}{recipe.id}/')

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data['tags']) == size
    assert len(data['ingredients']) == size
    assert data['author']['is_subscribed'] is True


def test_subscriptions_list(user_client, authors, size,
                            django_assert_num_queries):
    with django_assert_num_queries(SUBSCRIPTIONS_QUERIES):
        response = user_client.get(SUBSCRIPTIONS_URL,
                                   {'recipes_limit': RECIPES_LIMIT})

    assert response.status_code == status.HTTP_200_OK
    results = response.json()['results']
    assert len(results) == size
    for item in results:
        assert item['is_subscribed'] is True
        assert item['recipes_count'] == RECIPES_PER_AUTHOR
        assert len(item['recipes']) == RECIPES_LIMIT

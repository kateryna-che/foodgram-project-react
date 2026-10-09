import pytest
from rest_framework.test import APIClient

from factories import IMAGE, make_recipe, make_user
from recipes.models import Ingredient, Tag


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Keep the images uploaded by the tests out of the project folder."""
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def user(db):
    return make_user('chef')


@pytest.fixture
def another_user(db):
    return make_user('baker')


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def user_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def another_client(another_user):
    client = APIClient()
    client.force_authenticate(user=another_user)
    return client


@pytest.fixture
def tag(db):
    return Tag.objects.create(name='Завтрак', color='#E26C2D',
                              slug='breakfast')


@pytest.fixture
def another_tag(db):
    return Tag.objects.create(name='Обед', color='#49B64E', slug='lunch')


@pytest.fixture
def flour(db):
    return Ingredient.objects.create(name='Мука', measurement_unit='г')


@pytest.fixture
def salt(db):
    return Ingredient.objects.create(name='Соль', measurement_unit='г')


@pytest.fixture
def recipe(user, tag, flour):
    return make_recipe(user, [tag], [(flour, 200)])


@pytest.fixture
def recipe_payload(tag, flour):
    return {
        'tags': [tag.id],
        'ingredients': [{'id': flour.id, 'amount': 150}],
        'name': 'Оладьи',
        'image': IMAGE,
        'text': 'Замесить тесто и пожарить.',
        'cooking_time': 20,
    }

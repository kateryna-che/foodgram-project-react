import pytest
from rest_framework import status

from recipes.models import Ingredient

pytestmark = pytest.mark.django_db

TAGS_URL = '/api/tags/'
INGREDIENTS_URL = '/api/ingredients/'


def test_tags_list_is_public(anon_client, tag):
    response = anon_client.get(TAGS_URL)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {'id': tag.id, 'name': tag.name, 'color': tag.color,
         'slug': tag.slug},
    ]


def test_tag_detail(anon_client, tag):
    response = anon_client.get(f'{TAGS_URL}{tag.id}/')

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['slug'] == tag.slug


def test_missing_tag_returns_404(anon_client):
    response = anon_client.get(f'{TAGS_URL}999/')

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_tags_are_read_only(user_client):
    response = user_client.post(
        TAGS_URL, {'name': 'Ужин', 'color': '#8775D2', 'slug': 'dinner'}
    )

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_ingredients_search_by_name_start(anon_client):
    Ingredient.objects.create(name='Сахар', measurement_unit='г')
    Ingredient.objects.create(name='Соль', measurement_unit='г')
    Ingredient.objects.create(name='Кленовый сахар', measurement_unit='г')

    response = anon_client.get(INGREDIENTS_URL, {'name': 'Сах'})

    assert response.status_code == status.HTTP_200_OK
    assert [item['name'] for item in response.json()] == ['Сахар']


def test_ingredients_are_read_only(user_client):
    response = user_client.post(
        INGREDIENTS_URL, {'name': 'Перец', 'measurement_unit': 'г'}
    )

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

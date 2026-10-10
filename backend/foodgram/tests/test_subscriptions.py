import pytest
from rest_framework import status

from factories import make_recipe
from users.models import Subscription

pytestmark = pytest.mark.django_db

SUBSCRIPTIONS_URL = '/api/users/subscriptions/'


def subscribe_url(author_id):
    return f'/api/users/{author_id}/subscribe/'


def test_subscribe(user_client, user, another_user, tag, flour):
    make_recipe(another_user, [tag], [(flour, 100)])

    response = user_client.post(subscribe_url(another_user.id))

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['username'] == another_user.username
    assert data['is_subscribed'] is True
    assert data['recipes_count'] == 1
    assert Subscription.objects.filter(
        user=user, author=another_user
    ).exists()


def test_cannot_subscribe_to_yourself(user_client, user):
    response = user_client.post(subscribe_url(user.id))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not Subscription.objects.exists()


def test_cannot_subscribe_twice(user_client, user, another_user):
    Subscription.objects.create(user=user, author=another_user)

    response = user_client.post(subscribe_url(another_user.id))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Subscription.objects.count() == 1


def test_subscribe_to_missing_user(user_client):
    response = user_client.post(subscribe_url(999))

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_anonymous_user_cannot_subscribe(anon_client, another_user):
    response = anon_client.post(subscribe_url(another_user.id))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_unsubscribe(user_client, user, another_user):
    Subscription.objects.create(user=user, author=another_user)

    response = user_client.delete(subscribe_url(another_user.id))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Subscription.objects.exists()


def test_unsubscribe_without_subscription(user_client, another_user):
    response = user_client.delete(subscribe_url(another_user.id))

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_subscriptions_list(user_client, user, another_user, tag, flour):
    for number in range(3):
        make_recipe(another_user, [tag], [(flour, 100)],
                    name=f'Рецепт {number}')
    Subscription.objects.create(user=user, author=another_user)

    response = user_client.get(SUBSCRIPTIONS_URL, {'recipes_limit': 2})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['count'] == 1
    author = data['results'][0]
    assert author['username'] == another_user.username
    assert author['is_subscribed'] is True
    assert author['recipes_count'] == 3
    assert len(author['recipes']) == 2
    assert set(author['recipes'][0]) == {'id', 'name', 'image',
                                         'cooking_time'}


def test_subscriptions_list_requires_authentication(anon_client):
    response = anon_client.get(SUBSCRIPTIONS_URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_profile_shows_subscription(user_client, user, another_user):
    Subscription.objects.create(user=user, author=another_user)

    response = user_client.get(f'/api/users/{another_user.id}/')

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['is_subscribed'] is True

import pytest
from rest_framework import status

from factories import PASSWORD
from users.models import User

pytestmark = pytest.mark.django_db

USERS_URL = '/api/users/'
ME_URL = '/api/users/me/'
LOGIN_URL = '/api/auth/token/login/'
SET_PASSWORD_URL = '/api/users/set_password/'


def items(data):
    """The list endpoints may or may not be paginated."""
    return data['results'] if isinstance(data, dict) else data


def test_register_user(anon_client):
    payload = {
        'email': 'new@example.com',
        'username': 'newcomer',
        'first_name': 'New',
        'last_name': 'Comer',
        'password': PASSWORD,
    }

    response = anon_client.post(USERS_URL, payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['email'] == payload['email']
    assert data['username'] == payload['username']
    assert 'password' not in data
    assert User.objects.get(email=payload['email']).check_password(PASSWORD)


def test_register_requires_unique_email(anon_client, user):
    payload = {
        'email': user.email,
        'username': 'someone_else',
        'first_name': 'Some',
        'last_name': 'One',
        'password': PASSWORD,
    }

    response = anon_client.post(USERS_URL, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'email' in response.json()


def test_login_with_token_and_get_me(anon_client, user):
    response = anon_client.post(
        LOGIN_URL, {'email': user.email, 'password': PASSWORD}
    )
    assert response.status_code == status.HTTP_200_OK
    token = response.json()['auth_token']

    anon_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    response = anon_client.get(ME_URL)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['email'] == user.email
    assert data['is_subscribed'] is False


def test_login_with_wrong_password(anon_client, user):
    response = anon_client.post(
        LOGIN_URL, {'email': user.email, 'password': 'wrong-password'}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_me_requires_authentication(anon_client):
    response = anon_client.get(ME_URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_users_list_is_public(anon_client, user):
    response = anon_client.get(USERS_URL)

    assert response.status_code == status.HTTP_200_OK
    usernames = [item['username'] for item in items(response.json())]
    assert user.username in usernames


def test_set_password(user_client, user):
    new_password = 'An0ther-Passw0rd!'

    response = user_client.post(
        SET_PASSWORD_URL,
        {'current_password': PASSWORD, 'new_password': new_password},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    user.refresh_from_db()
    assert user.check_password(new_password)


def test_set_password_checks_current_password(user_client, user):
    response = user_client.post(
        SET_PASSWORD_URL,
        {'current_password': 'wrong-password',
         'new_password': 'An0ther-Passw0rd!'},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    user.refresh_from_db()
    assert user.check_password(PASSWORD)

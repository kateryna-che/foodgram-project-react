# Foodgram Recipe Platform

Foodgram is a recipe-sharing web application with a REST API. Users can publish recipes, add recipes to favorites, follow authors, generate shopping lists from selected recipes, and download the shopping list as a text file.

This repository is kept as a portfolio backend project: it shows a Django REST Framework application packaged with Docker and prepared for deployment behind Nginx and Gunicorn.

## Main features

- User registration and authentication
- Recipe creation, editing, and deletion
- Recipe images and ingredient lists
- Favorite recipes
- Author subscriptions
- Shopping cart based on selected recipes
- Downloadable shopping list
- API documentation
- Docker-based local launch
- CI/CD workflow with GitHub Actions

## Tech stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- Docker
- Docker Compose
- Nginx
- Gunicorn
- GitHub Actions

## Local setup

Clone the repository:

```bash
git clone git@github.com:kateryna-che/foodgram-project-react.git
cd foodgram-project-react
```

Create an environment file:

```bash
cd infra
touch .env
```

Example `.env` file:

```env
DJANGO_KEY=your-django-secret-key
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

Start the containers from the `infra/` directory:

```bash
docker-compose up -d
```

Run migrations, create a superuser, collect static files, and load ingredients:

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --no-input
docker-compose exec web python manage.py load_ingredients
```

## Deployment notes

The project is prepared for deployment with Docker Compose, Nginx, Gunicorn, PostgreSQL, and GitHub Actions.

Required GitHub Actions secrets for deployment:

```text
DOCKER_USERNAME
DOCKER_PASSWORD
USER
HOST
PASSPHRASE
SSH_KEY
TELEGRAM_TO
TELEGRAM_TOKEN
DB_ENGINE
DB_NAME
POSTGRES_USER
POSTGRES_PASSWORD
DB_HOST
DB_PORT
```

On push to the main deployment branch, the workflow can run code checks, build and publish Docker images, deploy the project, and send a Telegram notification.

## Project status

Portfolio project. Demo deployment is not currently maintained.

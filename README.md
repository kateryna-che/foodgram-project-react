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
- uv
- pytest, pytest-django

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
DEBUG=False
ALLOWED_HOSTS=localhost 127.0.0.1
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

## Local development with uv

The backend dependencies are managed with [uv](https://docs.astral.sh/uv/):
`backend/pyproject.toml` lists the direct dependencies, and `backend/uv.lock`
pins the exact versions and hashes of the whole dependency tree. The Docker
image, CI and a local environment are all installed from the same lockfile.

Install uv (other methods are listed in the
[installation guide](https://docs.astral.sh/uv/getting-started/installation/)):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Create the virtual environment in `backend/.venv` and install the runtime
dependencies together with the `dev` group (flake8, pytest, pytest-django).
If Python 3.14 is not installed, uv downloads it:

```bash
cd backend
uv sync
```

Commands run inside the environment through `uv run`, without activating
it. To start the API on SQLite, create `backend/foodgram/.env`:

```env
DJANGO_KEY=your-django-secret-key
DEBUG=True
DATABASES=sqlite
```

and run from `backend/foodgram`:

```bash
cd foodgram
uv run python manage.py migrate
uv run python manage.py load_ingredients
uv run python manage.py runserver
```

To change the dependencies, edit them through uv and commit the updated
`pyproject.toml` and `uv.lock` together:

```bash
uv add <package>                     # runtime dependency
uv add --dev <package>               # development dependency
uv lock --upgrade-package <package>  # upgrade one locked package
```

## Running the tests

The API is covered by tests written with pytest, pytest-django and the DRF
test client: registration and token login, tags and ingredient search,
creating, editing and deleting recipes with their validation and access
rules, filters, favorites, the shopping cart and its download, and
subscriptions.

Install the dependencies with uv (see
[Local development with uv](#local-development-with-uv)) and run the tests
and flake8 from `backend/foodgram`:

```bash
cd backend
uv sync
cd foodgram
uv run pytest
uv run flake8
```

The tests need the same environment variables as the project (see the
`.env` examples above). Set `DATABASES=sqlite` to run them on SQLite instead
of PostgreSQL.

On every push and pull request GitHub Actions installs the dependencies with
`uv sync --locked` (the job fails if `uv.lock` is out of date with
`pyproject.toml`), runs flake8, checks that the migrations match the models,
and runs the tests against PostgreSQL.

## Deployment notes

The project is prepared for deployment with Docker Compose, Nginx, Gunicorn, PostgreSQL, and GitHub Actions.

Required GitHub Actions secrets for deployment:

```text
DJANGO_KEY
ALLOWED_HOSTS
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

Building the Docker image, deploying and the Telegram notification run only
when the workflow is started by hand from the Actions tab (`workflow_dispatch`),
after the tests pass.

## Project status

Portfolio project. Demo deployment is not currently maintained.

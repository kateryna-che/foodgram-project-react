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

Start the containers from the `infra/` directory with Docker Compose v2
(the `docker compose` plugin):

```bash
docker compose up -d
```

Run migrations, create a superuser, collect static files, and load ingredients:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py collectstatic --no-input
docker compose exec web python manage.py load_ingredients
```

The site is served on <http://localhost/>, the API documentation on
<http://localhost/api/docs/>.

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

## Deployment

The project is prepared for deployment with Docker Compose, Nginx, Gunicorn,
PostgreSQL, and GitHub Actions.

Building the Docker images, deploying and the Telegram notification run only
when the workflow is started by hand from the Actions tab (`workflow_dispatch`),
after the tests pass. The backend and the frontend images are pushed to Docker
Hub with the commit SHA as their tag; `latest` is moved only by runs on `main`,
and only `main` is deployed. The deploy job runs in the `production` GitHub
environment, where protection rules such as required reviewers and
environment secrets can be added.

The frontend image is built in two stages: Node 24 LTS installs the
dependencies from `yarn.lock` with `--frozen-lockfile` and builds the app with
`react-scripts` 5, and the final image holds only the built files on
`busybox`. When the stack starts, the frontend container copies them to
`../frontend/build`, which nginx serves.

The actions in the workflow are pinned to commit SHAs. Dependabot opens one
pull request a month that moves them to new releases.

### Server requirements

- Docker Engine with the Compose plugin v2.20 or newer (`docker compose`).
  The standalone `docker-compose` v1 is not used.
- The SSH user can run `sudo docker` without a password.

The deploy job copies `infra/docker-compose.yml`, `infra/nginx.conf` and
`docs/` of the deployed commit to `~/foodgram/` on the server, keeping the
repository layout, and runs Docker Compose in `~/foodgram/infra`. The frontend
container puts the built frontend into `~/foodgram/frontend/build`.

The Compose project is called `foodgram`, so its volumes are
`foodgram_db_data`, `foodgram_static_value` and `foodgram_media_value`
whatever directory it is started from.

### GitHub Actions secrets

```text
DJANGO_KEY
ALLOWED_HOSTS
DOCKER_USERNAME
DOCKER_PASSWORD
USER
HOST
PASSPHRASE
SSH_KEY
SSH_FINGERPRINT
TELEGRAM_TO
TELEGRAM_TOKEN
DB_ENGINE
DB_NAME
POSTGRES_USER
POSTGRES_PASSWORD
DB_HOST
DB_PORT
```

`SSH_FINGERPRINT` is optional but recommended: with it the deploy job checks
the host key of the server instead of trusting any host. Get it on the server:

```bash
ssh-keygen -l -f /etc/ssh/ssh_host_ed25519_key.pub | cut -d ' ' -f2
```

The deploy job writes the values to `~/foodgram/infra/.env` in single
quotes, readable only by the SSH user, so they may contain `$`, spaces and
other special characters, but not a single quote (`'`).

### What the deploy job does

1. Copies the compose file, `nginx.conf` and the API docs to `~/foodgram/`.
2. Writes `.env` with the secrets and `FOODGRAM_TAG`, the SHA of the deployed
   commit, which selects the backend and the frontend images.
3. Dumps the database to `~/foodgram/backups/` if it is running. The 10
   newest dumps are kept.
4. Pulls the images.
5. Runs `migrate` and `collectstatic` in one-off containers of the new image.
   If either fails, the job stops and the previous release keeps running.
6. Starts the new release with `docker compose up -d`; nginx is restarted
   together with the backend container. The job then waits for the backend
   healthcheck and fails if the backend does not become healthy within two
   minutes.
7. Keeps the 5 newest backend and frontend images for a rollback and removes
   older ones and dangling layers.

The Telegram message reports both a successful deploy and a failed run on
`main`, with a link to the run.

### Runtime settings

- gunicorn starts `WEB_CONCURRENCY` workers, 3 by default in the image. For
  a local run the number can be changed in `infra/.env`.
- nginx and Django accept request bodies up to 10 MB. Recipe images are sent
  base64-encoded inside the JSON body, a third larger than the file.
- Every container keeps at most three 10 MB log files
  (`docker compose logs` reads them).
- `docker compose ps` shows the health of `db` and `web`.

### Rolling back

Every pushed image is tagged with the SHA of its commit (see the tags on
Docker Hub or the history of the workflow runs). If the release being rolled
back added migrations, revert them first, while its image is still running:

```bash
cd ~/foodgram/infra
sudo docker compose exec web python manage.py migrate <app> <previous-migration>
```

Then set `FOODGRAM_TAG` in `.env` to the SHA of the earlier commit and
recreate the backend and frontend containers:

```bash
sed -i "s/^FOODGRAM_TAG=.*/FOODGRAM_TAG='<commit-sha>'/" .env
sudo docker compose up -d
sudo docker compose up -d --wait web
```

The next deploy writes the tag of the deployed commit to `.env` again.

If the migrations can not be reverted, restore the dump that the deploy took
before them. This replaces the whole database. `POSTGRES_USER` and `DB_NAME`
are the values from `.env`:

```bash
cd ~/foodgram/infra
ls -1 ../backups/
sudo docker compose down
sudo docker volume rm foodgram_db_data
sudo docker compose up -d --wait db
sudo docker compose exec -T db pg_restore -U "$POSTGRES_USER" -d "$DB_NAME" \
  --no-owner --single-transaction < ../backups/foodgram-<date>.dump
sudo docker compose up -d
```

The dumps are stored on the same server, so they protect against a bad
release, not against losing the server; copy them elsewhere for that.

### Moving an existing server to this setup

Before this setup the server ran `docker-compose` v1 with the compose file in
the home directory, PostgreSQL 13 and a backend container running as root.
The volumes of that stack are named after the home directory (for example
`ubuntu_db_data`), so the new stack does not see them. Move the data once,
around the first deploy, as described below.

The same commands work on a development machine without `sudo`. There the
old volumes are named after the `infra` directory (`infra_db_data`,
`infra_media_value`), the old stack is stopped with
`docker compose -p infra down` from `infra/`, and `docker compose up -d`
takes the place of the deploy workflow.

1. Stop the old stack, keeping its volumes (no `-v`), and install the Compose
   plugin (on Ubuntu with the Docker apt repository it is the
   `docker-compose-plugin` package):

   ```bash
   cd ~
   sudo docker-compose down
   sudo apt-get install docker-compose-plugin
   ```

2. Find the old volumes and note their names:

   ```bash
   sudo docker volume ls
   ```

3. Set the variables used below. `POSTGRES_USER` and `DB_NAME` are the values
   from the old `.env`:

   ```bash
   OLD_DB_VOLUME=ubuntu_db_data
   OLD_MEDIA_VOLUME=ubuntu_media_value
   OLD_STATIC_VOLUME=ubuntu_static_value
   POSTGRES_USER=postgres
   DB_NAME=postgres
   ```

#### PostgreSQL 13 to 16

The PostgreSQL 16 image can not start on a data directory created by
PostgreSQL 13, so the database is moved with `pg_dump` and `pg_restore`.

1. Dump the database from the old volume with a temporary PostgreSQL 13
   container:

   ```bash
   sudo docker run -d --name foodgram-pg13 \
     -v "$OLD_DB_VOLUME":/var/lib/postgresql/data postgres:13-alpine
   until sudo docker exec foodgram-pg13 pg_isready -h 127.0.0.1 -U "$POSTGRES_USER"; do sleep 1; done
   sudo docker exec foodgram-pg13 pg_dump -U "$POSTGRES_USER" -d "$DB_NAME" \
     --format=custom > ~/foodgram-pg13.dump
   sudo docker rm -f foodgram-pg13
   ```

   If the old volume is already called `foodgram_db_data`, copy it to a
   backup volume and remove it, otherwise PostgreSQL 16 will not start:

   ```bash
   sudo docker volume create foodgram_db_data_pg13
   sudo docker run --rm -v foodgram_db_data:/from:ro -v foodgram_db_data_pg13:/to \
     alpine cp -a /from/. /to/
   sudo docker volume rm foodgram_db_data
   ```

2. Run the deploy workflow. It starts the new stack with an empty
   PostgreSQL 16 database.

3. Recreate the database volume and restore the dump into it, then apply the
   migrations that are newer than the dump and start the stack:

   ```bash
   cd ~/foodgram/infra
   sudo docker compose down
   sudo docker volume rm foodgram_db_data
   sudo docker compose up -d --wait db
   sudo docker compose exec -T db pg_restore -U "$POSTGRES_USER" -d "$DB_NAME" \
     --no-owner --single-transaction < ~/foodgram-pg13.dump
   sudo docker compose run --rm web python manage.py migrate --noinput
   sudo docker compose up -d
   ```

   `--single-transaction` restores everything or nothing; `--no-owner` makes
   `POSTGRES_USER` the owner of the restored tables.

4. Check that the data is there, for example:

   ```bash
   sudo docker compose exec db psql -U "$POSTGRES_USER" -d "$DB_NAME" \
     -c 'SELECT count(*) FROM recipes_recipe;'
   ```

#### Media files and the non-root container

The backend now runs as the user `app` with UID and GID 10001. Copy the
uploaded files to the new media volume and give them to that user:

```bash
sudo docker run --rm -v "$OLD_MEDIA_VOLUME":/from:ro -v foodgram_media_value:/to \
  alpine sh -c 'cp -a /from/. /to/ && chown -R 10001:10001 /to'
```

The static files are collected again by every deploy, so the old static
volume is not needed. If the stack keeps using volumes created while the
container ran as root, change their owner the same way:

```bash
sudo docker run --rm -v foodgram_static_value:/static -v foodgram_media_value:/media \
  alpine chown -R 10001:10001 /static /media
```

When the site works, remove the old volumes (keep `~/foodgram-pg13.dump`
for a while):

```bash
sudo docker volume rm "$OLD_DB_VOLUME" "$OLD_MEDIA_VOLUME" "$OLD_STATIC_VOLUME"
```

## Project status

Portfolio project. Demo deployment is not currently maintained.

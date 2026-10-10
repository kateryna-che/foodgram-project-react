ARG PYTHON_IMAGE=python:3.14-slim

# Build stage: uv installs the locked runtime dependencies into /app/.venv.
FROM ${PYTHON_IMAGE} AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Final stage: the same base image with only the virtual environment and
# the code, without uv and its cache.
FROM ${PYTHON_IMAGE}

# The application runs as an unprivileged user with a fixed UID/GID, so
# the ownership of the static and media volumes stays predictable.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app \
        --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin app

WORKDIR /app

# The virtual environment and the code stay owned by root, read-only for
# the app user.
COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

COPY foodgram/ .

# collectstatic and uploads write here. Docker copies the ownership of
# these directories into a new empty named volume mounted over them.
RUN mkdir -p /app/static /app/media \
    && chown app:app /app/static /app/media

USER app

EXPOSE 8000

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]

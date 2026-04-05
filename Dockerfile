FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/app \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/

RUN addgroup -S app && adduser -S -G app -h /home/app app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project --no-editable

COPY --chown=app:app src ./src
COPY --chown=app:app locales ./locales
COPY --chown=app:app migrations ./migrations
RUN uv sync --frozen --no-dev --no-editable \
    && uv run pybabel compile -d locales \
    && chown -R app:app /app

USER app

ENTRYPOINT [ "/app/.venv/bin/python", "-m", "main" ]

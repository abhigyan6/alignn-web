FROM ghcr.io/astral-sh/uv:0.13.6 AS uv
FROM python:3.12-slim-bookworm
COPY --from=uv /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends libmagic1 curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --locked --no-dev
COPY alembic.ini ./
COPY migrations ./migrations
RUN useradd --create-home alignn
USER alignn
ENV PATH="/app/.venv/bin:$PATH"
CMD ["sh", "-c", "exec uvicorn alignn.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]

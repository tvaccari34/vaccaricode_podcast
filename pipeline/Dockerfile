# Build context is the REPOSITORY ROOT (see deploy/docker-compose.yml) so the image can bundle
# both the pipeline source and db/migrations.
FROM python:3.12-slim

# ffmpeg is needed later for episode audio assembly (task group 4, VPS side).
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pipeline/pyproject.toml ./pipeline/pyproject.toml
COPY pipeline/src ./pipeline/src
RUN pip install --no-cache-dir ./pipeline

# Migrations live alongside the app so `boosternews-migrate` can find them.
COPY db ./db
ENV MIGRATIONS_DIR=/app/db/migrations
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "boosternews"]

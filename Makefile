# Convenience wrapper. Always run Compose from the repo root with the single root .env so that
# ${VAR} interpolation AND container env_file both read the same file.
# (Intended for the Linux VPS / home host; on Windows use the explicit docker compose commands
# shown in README.md.)

ENV_FILE ?= .env
VPS  := docker compose --env-file $(ENV_FILE) -f deploy/docker-compose.yml
HOME := docker compose --env-file $(ENV_FILE) -f deploy/compose.home.yml

.PHONY: help up up-infra migrate listmonk-install down logs ps home-up home-logs home-down test lint

help:
	@echo "VPS:  up-infra | migrate | listmonk-install | up | down | logs | ps"
	@echo "Home: home-up | home-logs | home-down"
	@echo "Dev:  test | lint"

up-infra:           ## start postgres + minio
	$(VPS) up -d postgres minio

migrate:            ## apply database migrations (one-shot)
	$(VPS) run --rm migrate

listmonk-install:   ## initialize Listmonk's schema (idempotent — safe to re-run)
	$(VPS) run --rm listmonk ./listmonk --install --yes --idempotent --config /listmonk/config.toml

web-build:          ## build the Astro static site (queries Postgres) into web/dist
	$(VPS) run --rm web-build

dashboard:          ## start the review dashboard (http://localhost:8080)
	$(VPS) up -d dashboard

publish:            ## publish approved drafts, then rebuild the site
	$(VPS) run --rm pipeline python -m boosternews publish --all
	$(VPS) run --rm web-build

worker:             ## build+run the GPU sound-worker on this machine (needs NVIDIA GPU + voice sample)
	$(VPS) --profile worker up -d --build sound-worker

worker-logs:
	$(VPS) --profile worker logs -f sound-worker

scheduler:          ## run the orchestration scheduler (ingest/extract/publish loop)
	$(VPS) --profile scheduler up -d scheduler

scheduler-logs:
	$(VPS) --profile scheduler logs -f scheduler

up:                 ## start the full VPS stack
	$(VPS) up -d

down:               ## stop the VPS stack
	$(VPS) down

logs:               ## follow pipeline logs
	$(VPS) logs -f pipeline

ps:
	$(VPS) ps

home-up:            ## start the home GPU sound-worker
	$(HOME) up -d

home-logs:
	$(HOME) logs -f sound-worker

home-down:
	$(HOME) down

test:               ## run pipeline tests
	cd pipeline && pytest -q

lint:               ## ruff + black check
	cd pipeline && ruff check . && black --check .

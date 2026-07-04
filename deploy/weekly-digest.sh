#!/usr/bin/env bash
# Weekly newsletter digest. Runs `boosternews digest` as an ephemeral Swarm job: aggregates the
# last 7 days of posts into one Listmonk campaign per language. Created as a draft unless
# NEWSLETTER_DIGEST_AUTOSEND=true in .env. Scheduled via cron (Mondays).
set -uo pipefail
REPO=/root/vaccaricode_podcast
cd "$REPO"
source deploy/swarm-run.sh
swarm_run bn-digest -- --env-file "$REPO/.env" boosternews/pipeline:local python -m boosternews digest

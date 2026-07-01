#!/bin/bash
# Runs once, on first initialization of the Postgres data volume.
# Creates a separate database for Listmonk on the same Postgres instance.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE ${LISTMONK_DB}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${LISTMONK_DB}')\gexec
EOSQL

echo "Ensured Listmonk database '${LISTMONK_DB}' exists."

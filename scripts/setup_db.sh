#!/usr/bin/env bash
# One-time database setup. Creates the app role + database, enables pgvector,
# and loads the schema. Run from the project root:
#
#   bash scripts/setup_db.sh
#
# Requires a local PostgreSQL with the `postgres` superuser reachable via
# `sudo -u postgres psql` (the default on Debian/Ubuntu installs).

set -euo pipefail

DB_NAME="${PGDATABASE:-ragdb}"
DB_USER="${PGUSER:-raguser}"
DB_PASS="${PGPASSWORD:-ragpass}"

echo ">> Creating role '$DB_USER' (if missing)…"
sudo -u postgres psql -v ON_ERROR_STOP=1 -tc \
  "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1 \
  || sudo -u postgres psql -v ON_ERROR_STOP=1 -c \
       "CREATE ROLE \"$DB_USER\" LOGIN PASSWORD '$DB_PASS';"

echo ">> Creating database '$DB_NAME' (if missing)…"
sudo -u postgres psql -v ON_ERROR_STOP=1 -tc \
  "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1 \
  || sudo -u postgres psql -v ON_ERROR_STOP=1 -c \
       "CREATE DATABASE \"$DB_NAME\" OWNER \"$DB_USER\";"

echo ">> Enabling pgvector + loading schema…"
sudo -u postgres psql -v ON_ERROR_STOP=1 -d "$DB_NAME" -f db/schema.sql

echo ">> Granting table privileges to '$DB_USER'…"
sudo -u postgres psql -v ON_ERROR_STOP=1 -d "$DB_NAME" -c \
  "GRANT ALL ON ALL TABLES IN SCHEMA public TO \"$DB_USER\";
   GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO \"$DB_USER\";"

echo ">> Done. Database '$DB_NAME' is ready for user '$DB_USER'."

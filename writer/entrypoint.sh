#!/bin/bash

export DATASTORE_DATABASE_PORT="${DATASTORE_DATABASE_PORT:-5432}"

# TODO: read optional ports from env variables: db_port and redis_port
wait-for-it --timeout=10 "$DATASTORE_DATABASE_HOST:$DATASTORE_DATABASE_PORT"
wait-for-it --timeout=10 "$MESSAGE_BUS_HOST:$MESSAGE_BUS_PORT"

# Create schema in postgresql
export PGPASSWORD="$DATASTORE_DATABASE_PASSWORD"
psql -1 -h "$DATASTORE_DATABASE_HOST" -p "$DATASTORE_DATABASE_PORT" -U "$DATASTORE_DATABASE_USER" -d "$DATASTORE_DATABASE_NAME" -f shared/postgresql_backend/schema.sql

exec "$@"

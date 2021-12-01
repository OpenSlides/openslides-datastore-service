#!/bin/bash

case $DATASTORE_ENABLE_DEV_ENVIRONMENT in
    1|on|On|ON|true|True|TRUE)  export PGPASSWORD="openslides";;
    *)                          export PGPASSWORD="$(cat "$DATASTORE_DATABASE_PASSWORD_FILE")";;
esac
psql -1 -h "$DATASTORE_DATABASE_HOST" -p "$DATASTORE_DATABASE_PORT" -U "$DATASTORE_DATABASE_USER" \
        -d "$DATASTORE_DATABASE_NAME" -f datastore/shared/postgresql_backend/schema.sql

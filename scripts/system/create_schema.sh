#!/bin/bash

psql -1 -h "$DATASTORE_DATABASE_HOST" -p "$DATASTORE_DATABASE_PORT" -U "$DATASTORE_DATABASE_USER" \
        -d "$DATASTORE_DATABASE_NAME" -f datastore/shared/postgresql_backend/schema.sql

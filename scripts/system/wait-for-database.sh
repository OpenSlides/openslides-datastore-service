#!/bin/bash

source export-database-variables.sh

until pg_isready -h "$DATASTORE_DATABASE_HOST" -p "$DATASTORE_DATABASE_PORT"; do
  echo "Waiting for Postgres server '$DATASTORE_DATABASE_HOST' to become available..."
  sleep 3
done


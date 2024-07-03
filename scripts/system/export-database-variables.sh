#!/bin/bash

case $OPENSLIDES_DEVELOPMENT in
    1|on|On|ON|true|True|TRUE)  export OPENSLIDES_ENVIRONMENT=dev;;
    *)                          export OPENSLIDES_ENVIRONMENT=prod;;
esac

export DATABASE_HOST=${DATABASE_HOST:-postgres}
export DATABASE_PORT=${DATABASE_PORT:-5432}
export DATABASE_NAME=${DATABASE_NAME:-openslides}
export DATABASE_USER=${DATABASE_USER:-openslides}
export DATABASE_PASSWORD_FILE=${DATABASE_PASSWORD_FILE:-/run/secrets/postgres_password}

if [ "$OPENSLIDES_ENVIRONMENT" = "dev" ]; then
    export PGPASSWORD="openslides"
fi

if [ "$OPENSLIDES_ENVIRONMENT" = "prod" ]; then
    export DATASTORE_TRIM_COLLECTIONFIELD_TABLES=1
fi

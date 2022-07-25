#!/bin/bash

set -e

DATASTORE_DATABASE_HOST=${DATASTORE_DATABASE_HOST:-postgres}
DATASTORE_DATABASE_PORT=${DATASTORE_DATABASE_PORT:-5432}
DATASTORE_DATABASE_USER=${DATASTORE_DATABASE_USER:-openslides}
DATASTORE_DATABASE_NAME=${DATASTORE_DATABASE_NAME:-openslides}
PGPASSWORD=${DATASTORE_DATABASE_PASSWORD}
[ -z "$PGPASSWORD" ] || export PGPASSWORD
PSQL="psql -h $DATASTORE_DATABASE_HOST -p $DATASTORE_DATABASE_PORT -U $DATASTORE_DATABASE_USER -d $DATASTORE_DATABASE_NAME"

if [ $# -eq 0 ]; then
    echo "No file to import from is given (use - to read from stdin)."
    exit 1
fi

SRC=
[ "$1" = "-" ] ||
  SRC="$1"

# wait for potentially restarted postgres to become ready
until $PSQL -c '\q' >/dev/null 2>&1; do
  echo "waiting for $DATASTORE_DATABASE_HOST ..." && sleep 1
done
cat $SRC | $PSQL

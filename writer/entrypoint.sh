#!/bin/bash

source wait-for-message-bus.sh
source wait-for-database.sh

# Create schema in postgresql
export PGPASSWORD="$DATASTORE_DATABASE_PASSWORD"
psql -1 -h "$DATASTORE_DATABASE_HOST" -p "$DATASTORE_DATABASE_PORT" -U "$DATASTORE_DATABASE_USER" \
        -d "$DATASTORE_DATABASE_NAME" -f shared/postgresql_backend/schema.sql

if [ -n "$COMMAND" ]; then
    if [ -f "cli/$COMMAND.py" ]; then
        echo "executing $COMMAND"
        python "cli/$COMMAND.py"
    else
        echo "Error: unknown command $COMMAND"
    fi
fi

exec "$@"
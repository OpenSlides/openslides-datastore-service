#!/bin/bash

source wait-for-message-bus.sh
source wait-for-database.sh

# Create schema in postgresql
./create_schema.sh

if [ -n "$COMMAND" ]; then
    if [ -f "cli/$COMMAND.py" ]; then
        echo "executing $COMMAND"
        python "cli/$COMMAND.py"
    else
        echo "Error: unknown command $COMMAND"
    fi
fi

if [ "$OPENSLIDES_ENVIRONMENT" = "prod" ] && [ -n "$DATASTORE_TRIM_COLLECTIONFIELD_TABLES" ]; then
    printenv > /app/environment
    echo "Starting cron..."
    cron
fi

exec "$@"

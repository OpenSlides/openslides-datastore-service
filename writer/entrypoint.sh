#!/bin/bash

source wait-for-message-bus.sh
source wait-for-database.sh

# Create schema in postgresql
./create_schema.sh

if [ "$OPENSLIDES_ENVIRONMENT" = "prod" ] && [ -n "$DATASTORE_TRIM_COLLECTIONFIELD_TABLES" ]; then
    printenv > /app/environment
    echo "Starting cron..."
    cron
fi

exec "$@"

#!/bin/bash


if [ -v MESSAGE_BUS_HOST -a -v USE_REDIS ]; then
    test -n "$MESSAGE_BUS_HOST" || (echo "MESSAGE_BUS_HOST not set" && exit)
    test -n "$MESSAGE_BUS_PORT" || (echo "MESSAGE_BUS_PORT not set" && exit)
    wait-for-it --timeout=15 "$MESSAGE_BUS_HOST:$MESSAGE_BUS_PORT"
fi

# only wait for postgres if it was started (e.g. the test setup doesn't neccessarily start the postgres server)
if [ -v DATASTORE_DATABASE_HOST ]; then
    test -n "$DATASTORE_DATABASE_PORT" || (echo "DATASTORE_DATABASE_PORT not set" && exit)
    test -n "$DATASTORE_DATABASE_USER" || (echo "DATASTORE_DATABASE_USER not set" && exit)
    test -n "$DATASTORE_DATABASE_NAME" || (echo "DATASTORE_DATABASE_NAME not set" && exit)
    test -n "$DATASTORE_DATABASE_PASSWORD" || (echo "DATASTORE_DATABASE_PASSWORD not set" && exit)

    wait-for-it --timeout=15 "$DATASTORE_DATABASE_HOST:$DATASTORE_DATABASE_PORT"

    # Create schema in postgresql
    export PGPASSWORD="$DATASTORE_DATABASE_PASSWORD"
    psql -1 -h "$DATASTORE_DATABASE_HOST" -p "$DATASTORE_DATABASE_PORT" -U "$DATASTORE_DATABASE_USER" \
            -d "$DATASTORE_DATABASE_NAME" -f shared/postgresql_backend/schema.sql
fi

if [ "$MODULE" = "writer" -a "$COMMAND" = "create_example_data" ]; then
    echo "creating example data"
    python cli/create_initial_data.py
fi

exec "$@"

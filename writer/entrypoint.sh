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

exec "$@"
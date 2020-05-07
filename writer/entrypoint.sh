#!/bin/bash

source wait-for-message-bus.sh
source wait-for-database.sh

if [ "$COMMAND" = "create_example_data" ]; then
    echo "creating example data"
    python cli/create_initial_data.py
fi

exec "$@"
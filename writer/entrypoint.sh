#!/bin/bash

source wait-for-message-bus.sh
source wait-for-database.sh

# Create schema in postgresql
./create_schema.sh

exec "$@"
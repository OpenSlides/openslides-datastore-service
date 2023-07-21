#!/bin/bash

set -e

if [ $# -eq 0 ]; then
    echo "No file to export to is given."
    exit 1
fi

pg_dump -c --if-exists -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U "$DATABASE_USER" -d "$DATABASE_NAME" > $1

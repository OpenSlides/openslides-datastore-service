#!/bin/bash

cd $(dirname $0);
source export-database-variables.sh
export PYTHONPATH=/app/
/usr/local/bin/python /app/cli/trim_collectionfield_tables.py

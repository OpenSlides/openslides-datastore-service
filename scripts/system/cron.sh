#!/bin/bash

set -a

cd $(dirname $0)
source /app/environment
/usr/local/bin/python /app/cli/trim_collectionfield_tables.py

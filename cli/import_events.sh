#!/bin/bash

set -e

if [ $# -eq 0 ]; then
  echo "No file to import from is given (use - to read from stdin)."
  exit 1
fi

SRC=
[ "$1" = "-" ] ||
  SRC="$1"

# wait for potentially restarted postgres to become ready
source wait-for-database.sh

cat $SRC | psql -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U "$DATABASE_USER" -d "$DATABASE_NAME"

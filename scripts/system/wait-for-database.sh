#!/bin/bash

source export-database-variables.sh

until pg_isready -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U "$DATABASE_USER"; do
  echo "Waiting for Postgres server '$DATABASE_HOST' to become available..."
  sleep 3
done


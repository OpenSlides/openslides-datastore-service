#!/bin/bash
# TODO: read optional ports from env variables: db_port and redis_port
wait-for-it --timeout=10 "$db_host":5432
wait-for-it --timeout=10 "$redis_host":6379

# Create schema in postgresql
export PGPASSWORD="$db_password"
psql -h "$db_host" -U "$db_user" -d "$db_database" -f writer/postgresql_backend/schema.sql

exec $*

#!/bin/bash

psql -1 -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U "$DATABASE_USER" -d "$DATABASE_NAME" -f datastore/shared/postgresql_backend/schema.sql

#!/bin/bash

source export-database-variables.sh
source wait-for-database.sh

exec "$@"

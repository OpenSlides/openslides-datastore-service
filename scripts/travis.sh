#!/bin/bash

# helper file to execute all check commands for travis
# Docker stuff needs to be initialized
# first argument needs to be the name of the module (shared, reader, writer)

set -v

docker-compose exec $1 black --check --diff --target-version py38 $1 tests
docker-compose exec $1 isort --check-only --diff --recursive $1 tests
docker-compose exec $1 flake8 $1 tests
docker-compose exec $1 mypy $1  # separate mypy commands to avoid duplicate module error
docker-compose exec $1 mypy tests
docker-compose exec $1 pytest --cov
docker-compose down

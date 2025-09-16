#!/bin/bash

set -e

# Executes all tests for the CI/CD Pipeline. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "########################################################################"
echo "###################### Run Tests and Linters ###########################"
echo "########################################################################"

# Setup
IMAGE_TAG=openslides-datastore-tests
CHOWN="$(id -u "${USER}"):$(id -g "${USER}")"

# Safe Exit
trap 'docker compose -f dc.test.yml down' EXIT

# Execution
make build-tests
docker compose -f dc.test.yml up -d
docker compose -f dc.test.yml exec -T datastore bash -c "chown -R $CHOWN /app"
docker compose -f dc.test.yml exec -T datastore ./entrypoint.sh ./execute-ci.sh


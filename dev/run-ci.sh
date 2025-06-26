#!/bin/bash

# Executes all tests for the CI/CD Pipeline. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "########################################################################"
echo "###################### Run Tests and Linters ###########################"
echo "########################################################################"

# Parameters
PERSIST_CONTAINERS=$1

# Setup
IMAGE_TAG=openslides-datastore-tests
CATCH=0
CHOWN="$(id -u "${USER}"):$(id -g "${USER}")"

# Execution
if [ "$(docker images -q $IMAGE_TAG)" = "" ]; then make build-test || CATCH=1; fi
docker compose -f dc.test.yml up -d || CATCH=1
docker compose -f dc.test.yml exec -T datastore bash -c "chown -R $CHOWN /app" || CATCH=1
docker compose -f dc.test.yml exec -T datastore ./entrypoint.sh ./execute-ci.sh || CATCH=1

if [ -z "$PERSIST_CONTAINERS" ]; then docker compose -f dc.test.yml down || CATCH=1; fi

exit $CATCH
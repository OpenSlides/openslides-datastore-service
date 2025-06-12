#!/bin/bash

# Executes all tests. Should errors occur, CATCH will be set to 1, causing an erronous exit code.

echo "########################################################################"
echo "###################### Start full system tests #########################"
echo "########################################################################"

CATCH=0
PERSIST_CONTAINERS=$2
CHOWN=$1

# Run Tests
make build-test || CATCH=1

docker compose -f dc.test.yml up -d || CATCH=1
docker compose -f dc.test.yml exec -T datastore bash -c "chown -R $CHOWN /app" || CATCH=1
docker compose -f dc.test.yml exec datastore ./entrypoint.sh pytest || CATCH=1

if [ -z $PERSIST_CONTAINERS ]; then docker compose -f dc.test.yml down || CATCH=1; fi

exit $CATCH
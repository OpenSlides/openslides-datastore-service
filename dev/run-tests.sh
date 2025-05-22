#!/bin/bash

# Executes all tests. Should errors occur, CATCH will be set to 1, causing an erronous exit code.

echo "########################################################################"
echo "###################### Start full system tests #########################"
echo "########################################################################"

CATCH=0
PERSIST_CONTAINERS=$2
CHOWN=$1
# Run Tests
docker build -f ./Dockerfile.AIO ./ --tag openslides-datastore-test --target tests --build-arg CONTEXT=tests || CATCH=1
docker compose -f dc.test.yml up -d || CATCH=1
docker compose -f dc.test.yml exec -T datastore bash -c "chown -R $CHOWN /app" || CATCH=1
docker compose -f dc.test.yml exec datastore ./entrypoint.sh pytest || CATCH=1
if [ -z $PERSIST_CONTAINERS ]; then docker compose -f dc.test.yml down || CATCH=1; fi

# Run dev - Adapted from Makefile - This starts an interactive container shell, probably not needed
#docker build -f ./Dockerfile.AIO ./ --tag openslides-datastore-test --target tests --build-arg CONTEXT=tests || CATCH=1
#docker compose -f dc.test.yml up -d || CATCH=1
#docker compose -f dc.test.yml exec -T datastore bash -c "chown -R $CHOWN /app" || CATCH=1
#docker compose -f dc.test.yml exec datastore ./entrypoint.sh bash || CATCH=1
#if [ -z $PERSIST_CONTAINERS ]; then docker compose -f dc.test.yml down || CATCH=1; fi

# System Tests
#fst_args="-v ./system_tests/system_tests:/app/system_tests --network="host" --env-file=.env  -u $CHOWN openslides-datastore-full-system-tests"

#docker build -t openslides-datastore-full-system-tests -f system_tests/Dockerfile --build-arg CHOWN=$CHOWN . || CATCH=1
#docker run -ti ${fst_args} pytest system_tests || CATCH=1

#if [ -z $PERSIST_CONTAINERS ]; then docker stop $(docker ps -a -q --filter ancestor=openslides-datastore-full-system-tests --format="{{.ID}}") || CATCH=1; fi

exit $CATCH
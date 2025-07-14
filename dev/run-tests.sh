#!/bin/bash

# Executes all tests. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "########################################################################"
echo "###################### Run Tests and Linters ###########################"
echo "########################################################################"

# Parameters
while getopts "s" FLAG; do
    case "${FLAG}" in
    s) SKIP_BUILD=true ;;
    *) echo "Can't parse flag ${FLAG}" && break ;;
    esac
done

# Setup
IMAGE_TAG=openslides-datastore-tests
LOCAL_PWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CHOWN="$(id -u "${USER}"):$(id -g "${USER}")"

# Safe Exit
trap 'docker compose -f dc.test.yml down' EXIT

# Execution
if [ -z "$SKIP_BUILD" ]; then make build-test; fi
docker compose -f dc.test.yml up -d
docker compose -f dc.test.yml exec -T datastore bash -c "chown -R $CHOWN /app"
docker compose -f dc.test.yml exec datastore ./entrypoint.sh pytest

# Linters
bash "$LOCAL_PWD"/run-lint.sh
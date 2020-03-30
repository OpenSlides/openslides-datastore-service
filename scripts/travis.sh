#!/bin/bash

# helper file to execute all check commands for travis
# first argument needs to be the name of the module (shared, reader, writer)
# must not contain conditionals or loops: each line is evaluated as a single command by execute-travis.sh

set -v

black --check --diff --target-version py38 $1 tests
isort --check-only --diff --recursive $1 tests
flake8 $1 tests
# separate mypy commands to avoid duplicate module error
mypy $1
mypy tests
pytest --cov

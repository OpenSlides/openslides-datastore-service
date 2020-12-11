#!/bin/bash

# helper file to execute all check commands for CI
# must not contain conditionals or loops: each line is evaluated as a single command by execute-ci.sh

set -v

dirs=$(ls -d */)

black --check --diff --target-version py38 $dirs
isort --check-only --diff $dirs
flake8 $dirs
mypy $dirs
pytest --cov

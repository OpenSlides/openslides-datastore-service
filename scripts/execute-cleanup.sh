#!/bin/bash

printf "Black:\n"
black --target-version py310  $1
printf "\nAutoflake:\n"
autoflake --verbose --in-place --remove-all-unused-imports --ignore-init-module-imports --recursive $1
printf "\nIsort:\n"
isort $1
printf "\nFlake8:\n"
flake8 $1
printf "\nmypy:\n"
mypy $1
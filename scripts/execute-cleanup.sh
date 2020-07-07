#!/bin/bash

printf "Black:\n"
black $1
printf "\nIsort:\n"
isort $1
printf "\nFlake8:\n"
flake8 $1
printf "\nmypy:\n"
mypy $1
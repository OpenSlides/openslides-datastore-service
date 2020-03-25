#!/bin/bash

dirs=$(ls -d */)

printf "Black:\n"
black $dirs
printf "\nIsort:\n"
isort -rc $dirs
printf "\nFlake8:\n"
flake8 $dirs
printf "\nmypy:\n"
mypy $dirs
#!/bin/bash

dirs=$(ls -d */)

printf "Black:\n"
black $dirs
printf "\nIsort:\n"
isort -rc $dirs
printf "\nFlake8:\n"
flake8 $dirs
printf "\nmypy:\n"
# mypy needs to fix the dirs separately to not complain about multiple modules with the same name
for dir in $dirs; do
    mypy $dir
done

#!/bin/bash
printf "Black:\n"
black writer/ tests/
printf "\nIsort:\n"
isort -rc writer/ tests/
printf "\nFlake8:\n"
flake8 writer/ tests/
printf "\nmypy:\n"
mypy writer/ tests/
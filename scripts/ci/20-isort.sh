#!/bin/bash

set -e

isort --check-only --diff $(ls -d */)

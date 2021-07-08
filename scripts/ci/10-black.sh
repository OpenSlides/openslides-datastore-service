#!/bin/bash

set -e

black --check --diff --target-version py38 $(ls -d */)

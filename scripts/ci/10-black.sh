#!/bin/bash

set -e

black --check --diff --target-version py310 $(ls -d */)

#!/bin/bash

set -e

flake8 $(ls -d */)

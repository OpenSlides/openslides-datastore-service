# Basic repository layout

- /reader: the reader module
- /writer: the writer module
- /shared: the shared module. Contains classes and constants used by both the reader and the writer
- /scripts: useful scripts
- /requirements: the requirements for testing and in general

# Makefile setup
Since reader, writer and shared mostly need the same commands, the main Makefile contains those. If you issue commands in a subfolder, they are forwarded to the root Makefile. The following commands are available from the root directory:

The following commands are available from the root directory:

Utility:
- `make run-cleanup`: runs the cleanup script in all modules
- `make run-travis`: runs the travis script in all modules
- `make run-tests`: runs the tests of all modules


Development environment:
- `make build-dev`: builds all development images
- `make run-dev`: runs the development environment
- `make run-dev-verbose`: same as `make run-dev`, but doesn't detach the containers so the output is directly visible and the process can be stopped with CTRL+C.
- `make run-dev-manually`: starts the development environment without any services like postgres or redis. These have to be running for this command to succeed.
- `make stop-dev`: stops all dev containers

All these commands are also avaible inside the modules and only affect the current module there. Additional commands available inside the modules (primarily for testing purposes):

- `make run-bash`, `make run-tests-interactive`: opens a bash console in the container, so tests/cleanup can be run interactively
- `make run-coverage`: creates a coverage report for all tests.  The needed coverage to pass is defined in `.coveragerc`.

The following commands are only available in the `reader` and `writer`, since `shared` is no real module and has no integration/system tests:

- `make run-system-tests`: runs only the system tests

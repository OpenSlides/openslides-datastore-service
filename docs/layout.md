# Basic repository layout

- `/datastore`: Main python module
- `/datastore/reader`: the reader module
- `/datastore/writer`: the writer module
- `/datastore/shared`: the shared module. Contains classes and constants used by both the reader and the writer
- `/tests`: All tests.
- `/scripts`: useful scripts
- `/requirements`: the requirements for testing and in general
- `/system_tests`: tests for reader and writer in conjunction. Since these don't belong to any module or docker container, they cannot import anything from the other modules. They run in their own docker container and send requests to the host machine to test the full stack.

# Makefile setup
Since reader, writer and shared mostly need the same commands, the main Makefile contains those. If you issue commands in the subfolders `reader` or `writer`, they are forwarded to the root Makefile. The following commands are available from the root directory:

The following commands are available from the root directory:

Full system tests:
- `make run-full-system-tests`: starts the local productive setup and executes the full system tests. These test the reader and writer in conjunction. Requires that the dev environment is up and running and listening on the default ports. Prod environment does not work since the `truncate_db` route is not available there.
- `make run-full-system-tests-interactive`: start a bash inside the full system test docker container for repeated usage.
- `make run-full-system-tests-cleanup`: cleans up the full system tests.
- `make run-full-system-tests-check`: runs the ci utilities for the full system tests.

Utility:
- `make run-cleanup`: runs the cleanup script in all modules
- `make run-ci`: runs the ci script in all modules
- `make run-tests`: runs the tests of all modules
- `make run-system-tests`: runs only the system tests

Development environment:
- `make build-dev`: builds all development images
- `make run-dev-standalone`: runs the development environment
- `make run-dev-verbose`: same as `make run-dev-standalone`, but doesn't detach the containers so the output is directly visible and the process can be stopped with CTRL+C.
- `make stop-dev`: stops all dev containers

All these commands are also available inside the modules and only affect the current module there. Additional commands available inside the modules (primarily for testing purposes):

- `make run-bash`, `make run-dev`: opens a bash console in the container, so tests/cleanup can be run interactively
- `make run-coverage`: creates a coverage report for all tests. The needed coverage to pass is defined in `scripts/.coveragerc`.

# OpenSlides datastore service

Service for OpenSlides which wraps the database. Includes reader and writer functionality. For available methods see [the specs](https://github.com/OpenSlides/OpenSlides/blob/openslides4-dev/docs/interfaces/datastore-service.txt). For an extensive documentation, see TODO.

## Structure

- /reader: the reader module
- /writer: the writer module
- /shared: the shared module. Contains classes and constants used by both the reader and the writer
- /scripts: useful scripts
- /requirements: the requirements for testing and in general

## Makefile

Since reader, writer and shared mostly need the same commands, the main Makefile contains those. If you issue commands in a subfolder, they are forwarded to the root Makefile. The following commands are available from the root directory:

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

(Local) Productive environment:
- `make build-prod`: builds all productive images from the local files
- `make run-prod`: runs the productive environment. See below for details.
- `make run-prod-verbose` same as `run-prod`, but doesn't detach the containers so the output is directly visible and the process can be stopped with CTRL+C
- `make stop-prod`: stops all prod containers

"Real" productive environment:
While the local environment runs directly on the local files, this is not the typical use case; by default, we want to use the files of a specific commit or branch because that's tested in combination with all other services. The commands with a suffix like `-dev` or `-prod` are specifically for this: They ignore all local files and pull the code directly from the given repository.
- `make build`: builds all productive images from the remote files
- `make run`: runs the productive environment. See below for details.
- `make run-verbose` same as `run-prod`, but doesn't detach the containers so the output is directly visible and the process can be stopped with CTRL+C
- `make stop-prod`: stops all prod containers

All these commands are also avaible inside the modules and only affect the current module there. Additional commands available inside the modules (primarily for testing purposes):

- `make run-bash`, `make run-tests-interactive`: opens a bash console in the container, so tests/cleanup can be run interactively
- `make run-coverage`: creates a coverage report for all tests.  The needed coverage to pass is defined in `.coveragerc`.

The following commands are only available in the `reader` and `writer`, since `shared` is no real module and has no integration/system tests:

- `make run-integration-unit-tests`: runs only the integration and unit tests. Saves time and resources since no database and message bus has to be started.
- `make run-system-tests`: runs only the system tests
- `make run-coverage-integration-unit`: creates a coverage report for only the integration and unit tests
- `make run-integration-unit-tests-interactive`: opens a bash console in the container, but with no connected database or message bus, so only integration and unit tests can be executed


## Productive environment

`make run[-prod]` starts the reader and writer together with postgres and redis so that the datastore can be used in conjunction with other services. By default the writer listens on port 9011 and the reader on 9010, postgres on port 5432 and redis on 6379. Postgres and redis port can be configured via the environment variables `DATASTORE_DATABASE_PORT` and `MESSAGE_BUS_PORT`, reader and writer port via `OPENSLIDES_DATASTORE_%SERVICE%_PORT` (`%SERVICE%` \in {`READER`, `WRITER`}). 

### Curl example

After you started the productive environment, you can issue requests e.g. via curl. First, create a model:

    curl --header "Content-Type: application/json" -d '{"user_id": 1, "information": {}, "locked_fields": {}, "events": [{"type": "create", "fqid": "a/1", "fields": {"f": 1}}]}' http://localhost:9011/internal/datastore/writer/write

Then you can get that model with:

    curl --header "Content-Type: application/json" -d '{"fqid": "a/1"}' http://localhost:9010/internal/datastore/reader/get

All other commands work analogous to this.

## Development

Since the folder structure inside the docker container differs from the real one, IDEs like VS Code can't follow the imports correctly. To solve that, if you use VS Code, you need to create a `.env` file preferably in the `.vscode` folder (adjust your settings variable `python.envFile` accordingly) with the following entry:

    PYTHONPATH=shared:reader:writer

Since `docker-compose` uses the `.env` file in the root of the repository, this file should not also be used by VS Code, so it has to be placed elsewhere.

For other IDEs there are probably similar solutions. Feel free to add them here for your IDE.

# OpenSlides datastore service

Service for OpenSlides which wraps the database. Includes reader and writer functionality. For available methods see [the specs](https://github.com/OpenSlides/OpenSlides/blob/openslides4-dev/docs/interfaces/datastore-service.txt). For an extensive documentation, see TODO.

## Structure

- /reader: the reader module
- /writer: the writer module
- /shared: the shared module. Contains classes and constants used by both the reader and the writer
- /scripts: useful scripts
- /requirements: the requirements for testing and in general

## Setup

Since reader, writer and shared mostly need the same commands, the main Makefile contains those. Still, most of the commands need to be issued when in the respective subdirectory since the Makefile there sets the right environment variables. Exceptions to this are the following commands, which are available in the main folder:

- `run-cleanup`, `run-tests`, `run-travis`: runs the corresponding command in all three modules
- `build-dev`: build the dev images for reader and writer (shared has no dev image since it's included in both the reader and the writer)
- `run-prod`: see below

## Productive start

`run-prod` starts the reader and writer together with postgres and redis so that the datastore can be used in conjunction with other services. By default the writer listens on port 8000 and the reader on 8001, postgres on port 5432 and redis on 6379. Postgres and redis port can be configured via the environment variables `DATASTORE_DATABASE_PORT` and `MESSAGE_BUS_PORT`, reader and writer port in `dc.prod.yml`. If you need other ports or another setup, you can copy this file into your project and adjust it to your needs.

### Curl example

After you started the productive environment, you can issue requests e.g. via curl. First, create a model:

    curl --header "Content-Type: application/json" -d '{"user_id": 1, "information": {}, "locked_fields": {}, "events": [{"type": "create", "fqid": "a/1", "fields": {"f": 1}}]}' http://localhost:8000/internal/datastore/writer/write

Then you can get that model with:

    curl --header "Content-Type: application/json" -d '{"fqid": "a/1"}' http://localhost:8001/internal/datastore/reader/get

All other commands work analogous to this.

## Other commands

- `run-bash`: starts the module's container and enters an interactive bash where you can issue commands inside the container. Useful for development if you need to repeatedly test and clean up.
- `run-cleanup`: executes `cleanup.sh` which in turn runs `black`, `isort`, `flake8` and `mypy`.
- `run-tests`: executes `pytest`
- `run-coverage`: runs tests and creates a coverage report in `htmlcov`. The needed coverage to pass is defined in `.coveragerc`.

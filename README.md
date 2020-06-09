# OpenSlides datastore service

Service for OpenSlides which wraps the database, which includes reader and writer functionality. For available methods see [the specs](https://github.com/OpenSlides/OpenSlides/blob/openslides4-dev/docs/interfaces/datastore-service.txt). For an overview of the core concepts see [here](docs/concepts.md) and as a starting point for developing begin with the [basic repository layout](docs/layout.md).

## Usage
A Makefile is used to encapsulate all docker related commands. It is recommended to use the docker setup to run the datastore, so you need `make`, `docker` and `docker-compose` installed on your system as the only requirements.

The following commands are available from the root directory:

(Local) Productive environment:
- `make build-prod`: builds all productive images from the local files
- `make run-prod`: runs the productive environment. See below for details
- `make run-prod-verbose` same as `run-prod`, but doesn't detach the containers so the output is directly visible and the process can be stopped with CTRL+C
- `make stop-prod`: stops all prod containers, if they were stared in detached mode

"Real" productive environment:
While the local environment runs directly on the local files, this is not the typical use case; by default, we want to use the files of a specific git commit, tag or branch because that's tested in combination with all other services. The commands with a suffix like `-dev` or `-prod` are specifically for this: They ignore all local files and pull the code directly from the given repository.
- `make build`: builds all productive images from the remote files
- `make run`: runs the productive environment. See below for details
- `make run-verbose` same as `run-prod`, but doesn't detach the containers so the output is directly visible and the process can be stopped with CTRL+C
- `make stop-prod`: stops all prod containers

## Example data

To load [example data](https://github.com/OpenSlides/OpenSlides/blob/openslides4-dev/docs/example-data.json) into the container the environment variable `COMMAND` must be set to `create_example_data` inside the writer container.

## Productive environment

`make run[-prod]` starts the reader and writer together with postgres and redis so that the datastore can be used in conjunction with other services. By default the writer listens on port 8000 and the reader on 8001, postgres on port 5432 and redis on 6379. Postgres and redis port can be configured via the environment variables `DATASTORE_DATABASE_PORT` and `MESSAGE_BUS_PORT`, reader and writer port in `dc.prod.yml`. 

### Curl example

After you started the productive environment, you can issue requests e.g. via curl. First, create a model:

    curl --header "Content-Type: application/json" -d '{"user_id": 1, "information": {}, "locked_fields": {}, "events": [{"type": "create", "fqid": "a/1", "fields": {"f": 1}}]}' http://localhost:8000/internal/datastore/writer/write

Then you can get that model with:

    curl --header "Content-Type: application/json" -d '{"fqid": "a/1"}' http://localhost:8001/internal/datastore/reader/get

All other commands work analogous to this.

## Development

Please refer to the [development documentation](docs/development.md).

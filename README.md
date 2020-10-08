# OpenSlides datastore service

Service for OpenSlides which wraps the database, which includes reader and writer functionality. For available methods see [the specs](https://github.com/OpenSlides/OpenSlides/blob/openslides4-dev/docs/interfaces/datastore-service.txt). For an overview of the core concepts see [here](docs/concepts.md) and as a starting point for developing begin with the [basic repository layout](docs/layout.md).

## Usage
A Makefile is used to encapsulate all docker related commands. It is recommended to use the docker setup to run the datastore, so you need `make`, `docker` and `docker-compose` installed on your system as the only requirements.

For the productive mode two images `openslides-datastore-reader` and `openslides-datastore-writer` must be build via Make:

    make build

You can run the datastore (with or without logs) and stop it:

    make run
    make stop
    # with logs:
    make run-verbose  # Ctrl+C to quit

If you want to include the Datastore in other projects (e.g. as a dependency for testing), refer to the [development documentation](docs/development.md).

## Initial data

To create initial data, see [development documentation](docs/development.md#Commands).

### Curl example

After you started the productive environment, you can issue requests e.g. via curl. First, create a model:

    curl http://localhost:9011/internal/datastore/writer/write -H "Content-Type: application/json" -d '{"user_id": 1, "information": {}, "locked_fields": {}, "events": [{"type": "create", "fqid": "a/1", "fields": {"f": 1}}]}' 

Then you can get that model with:

    curl http://localhost:9010/internal/datastore/reader/get -H "Content-Type: application/json" -d '{"fqid": "a/1"}' 

All other commands work analogous to this.

## Development

Please refer to the [development documentation](docs/development.md).

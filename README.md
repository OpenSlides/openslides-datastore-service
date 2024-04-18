# OpenSlides datastore service

Service for OpenSlides which wraps the database, which includes reader and writer functionality. For an overview of the core concepts and available methods see [the wiki](https://github.com/OpenSlides/OpenSlides/wiki/Datastore-Service). As a starting point for developing begin with the [basic repository layout](docs/layout.md).

## Usage
A Makefile is used to encapsulate all docker related commands. It is recommended to use the docker setup to run the datastore, so you need `make`, `docker` and `docker compose` installed on your system as the only requirements.

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

For useful tools, take a look at the [CLI](cli/README.md).

## Configuration

The datastore can be configured with the following environment variables:
- `DATASTORE_MIN_CONNECTIONS`: The minimum amount of connections to the database that will be created. Default: 2
- `DATASTORE_MAX_CONNECTIONS`: The maximum amount of connections to the database that will be created. If this is set to 1, only one connection can access the database at a time. The writer always runs in single-access mode, so no write errors occur. Default: 5
- `DATASTORE_MAX_RETRIES`: The amount of times a request to the database is retried before giving up. Minimum: 1, Default: 5
- `DATASTORE_RETRY_TIMEOUT`: How long to wait before retrying a request to the database, in sec as float. Set 0 to disable waiting
  between requests. Default: 0.4
- `DATASTORE_TRIM_COLLECTIONFIELD_TABLES`: Whether or not to enable the automatic collectionfield
  table trimming via cronjob to improve performance. Default: 0
- `OPENSLIDES_DEVELOPMENT`: If set to a truthy value, the datastore runs in development mode (see [development docs](docs/development.md)
  for the implications).
- `DATASTORE_LOG_LEVEL`: Set the log level for the datastore. If not provided, it defaults to `DEBUG` in development
  mode and `INFO` otherwise.
- `DATABASE_HOST`: Host of the underlying database. Default: `postgres`
- `DATABASE_PORT`: Port of the underlying database. Default: `5432`
- `DATABASE_NAME`: Name of the underlying database. Default: `openslides`
- `DATABASE_USER`: User to use to login to the database. Default: `openslides`
- `DATABASE_PASSWORD_FILE`: Secret file provided by the docker setup which contains the password for the
  datastore. In development mode, this is not needed and the password defaults to `openslides`. In productive mode, this
  is the only allowed way to provide the database password to the application.

# Development

## Source code layout

See [basic repository layout](docs/layout.md).

## Using the Datastore in other services

If you want to do system tests in your service and need the datastore, use the `dc.external.yml`. It is completely independent from the local code. Just merge it with your service's docker-compose file and you can test everything in conjunction. It uses the productive setup, so no hot reload or similar is used, but runs the datastore in dev mode, so dev utils like `truncate_db` (see below) are available. You have to add the reader/writer as a dependency to your service(s) and add them to the `datastore` network.

## Initial data creation

You can issue commands to the datastore on startup via the docker variable `COMMAND` (has to be given as a build argument to the docker file). Currently only commands for the writer are supported.

- `create_initial_data`: this will load the file given in the environment variable `DATASTORE_INITIAL_DATA_FILE`, which may be a relative or absolute path to a file inside the docker container or an URL to a web resource (e.g. the [OpenSlides 4 example data](https://raw.githubusercontent.com/OpenSlides/OpenSlides/openslides4-dev/docs/example-data.json)) and write it to the datastore. If any data is present already, the command will fail. Note that if a path is given, the respective file has to be mounted to this place in the container; if an URL is given, the internet has to be accessible from inside the docker container (which means that in a setup with isolated networks e.g. as in the main repository, this option will not work).

The script is also available from inside the container under `cli/create_initial_data.py`. Example setup to load initial data:

- set `COMMAND=create_initial_data` and `DATASTORE_INITIAL_DATA_FILE=https://raw.githubusercontent.com/OpenSlides/OpenSlides/openslides4-dev/docs/example-data.json` <b>inside the docker container</b>, e.g. in your `docker-compose` file.

This will not work if the database is not empty. In this case, you can make use of the `truncate_db` route (see below). Example:

    make run-dev
    curl --header "Content-Type: application/json" -d '' http://localhost:9011/internal/datastore/writer/truncate_db
    docker-compose -f dc.dev.yml exec writer ./entrypoint.sh bash
    export DATASTORE_INITIAL_DATA_FILE=https://raw.githubusercontent.com/OpenSlides/OpenSlides/openslides4-dev/docs/example-data.json
    python cli/create_initial_data.py
    exit

## Development-exclusive tools

If the variable `DATASTORE_ENABLE_DEV_ENVIRONMENT` is set inside the docker container, the datastore runs in development mode. This is the case by default if you use the `dc.dev.yml` setup (see the `environment` section for the `writer`). Again, this currently has only an influence on the writer.

In development mode, the route `truncate_db` is available in the writer. <b>This will truncate the entire database and erase all data without confirmation, so use with caution.</b> Example curl call:

    curl --header "Content-Type: application/json" -d '' http://localhost:9011/internal/datastore/writer/truncate_db

## IDE setup

Since the folder structure inside the docker container differs from the real one, IDEs like VS Code can't follow the imports correctly. To solve that, if you use VS Code, you need to create a `.env` file preferably in the `.vscode` folder (adjust your settings variable `python.envFile` accordingly) with the following entry:

    PYTHONPATH=shared:reader:writer

Since `docker-compose` uses the `.env` file in the root of the repository, this file should not also be used by VS Code, so it has to be placed elsewhere.

For other IDEs there are probably similar solutions. Feel free to add them here for your IDE.
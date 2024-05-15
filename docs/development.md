# Development

## Source code layout

See [basic repository layout](layout.md).

## Using the Datastore in other services

If you want to do system tests in your service and need the datastore, use the `dc.external.yml`. It is completely independent from the local code. Just merge it with your service's docker compose file and you can test everything in conjunction. It uses the productive setup, so no hot reload or similar is used, but runs the datastore in dev mode, so dev utils like `truncate_db` (see below) are available. You have to add the reader/writer as a dependency to your service(s) and add them to the `datastore` network.

## Development-exclusive tools

If the variable `OPENSLIDES_DEVELOPMENT` is set inside the docker container, the datastore runs in development mode. This is the case by default if you use the `dc.dev.yml` setup (see the `environment` section for the `writer`). Again, this currently has only an influence on the writer.

In development mode, all passwords (e.g. for the database) default to `openslides`.

In development mode, the route `truncate_db` is available in the writer. <b>This will truncate the entire database and erase all data without confirmation, so use with caution.</b> Example curl call:

    curl --header "Content-Type: application/json" -d '' http://localhost:9011/internal/datastore/writer/truncate_db

## IDE setup

Since the folder structure inside the docker container differs from the real one, IDEs like VS Code can't follow the imports correctly. To solve that, if you use VS Code, you need to create a `.env` file preferably in the `.vscode` folder (adjust your settings variable `python.envFile` accordingly) with the following entry:

    PYTHONPATH=shared:reader:writer

Since `docker compose` uses the `.env` file in the root of the repository, this file should not also be used by VS Code, so it has to be placed elsewhere.

For other IDEs there are probably similar solutions. Feel free to add them here for your IDE.

## Locking mechanisms

See [Locking](locking.md).

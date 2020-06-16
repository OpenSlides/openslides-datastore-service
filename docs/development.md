# Development

## Source code layout

See [basic repository layout](docs/layout.md).

## IDE setup

Since the folder structure inside the docker container differs from the real one, IDEs like VS Code can't follow the imports correctly. To solve that, if you use VS Code, you need to create a `.env` file preferably in the `.vscode` folder (adjust your settings variable `python.envFile` accordingly) with the following entry:

    PYTHONPATH=shared:reader:writer

Since `docker-compose` uses the `.env` file in the root of the repository, this file should not also be used by VS Code, so it has to be placed elsewhere.

For other IDEs there are probably similar solutions. Feel free to add them here for your IDE.

## Commands

You can issue commands to the datastore on startup via the docker variable `COMMAND` (has to be given as a build argument to the docker file). Currently only commands for the writer are supported.

- `create_example_data`: this will fetch the [OpenSlides 4 example data](https://raw.githubusercontent.com/OpenSlides/OpenSlides/openslides4-dev/docs/example-data.json) and write it to the datastore. If any data is present already, the command will fail.

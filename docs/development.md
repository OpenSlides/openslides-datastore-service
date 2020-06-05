# Development

## Source code layout

See [basic repository layout](docs/layout.md).

## IDE setup

Since the folder structure inside the docker container differs from the real one, IDEs like VS Code can't follow the imports correctly. To solve that, if you use VS Code, you need to create a `.env` file preferably in the `.vscode` folder (adjust your settings variable `python.envFile` accordingly) with the following entry:

    PYTHONPATH=shared:reader:writer

Since `docker-compose` uses the `.env` file in the root of the repository, this file should not also be used by VS Code, so it has to be placed elsewhere.

For other IDEs there are probably similar solutions. Feel free to add them here for your IDE.
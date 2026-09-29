# alma Backend

The backend exposes is built with Python 3.11, FastAPI, Strawberry and SQLAlchemy.

Running `make start-services` from the repository root starts a containerised backend
that is good enough for frontend development. The instructions below are for
working on the backend itself.

## Configuration

The alma backend is configured with environment variables. To configure the
development instance edit the file `backend/env_file`. Settings can be found in `settings.py`.

If it does not already exist, run

    $ make backend/env_file

in the top-level directory.

## Development Setup

From the backend directory, create the project environment and install the
project plus its dev dependencies with uv:

    $ UV_PROJECT_ENVIRONMENT=venv VIRTUAL_ENV=venv uv sync --python=3.11


Install the GDAL package. The version of this package depends on the version of
the gdal library installed on your computer:

    $ sudo apt-get install libgdal-dev python3.11-dev
    $ UV_PROJECT_ENVIRONMENT=venv VIRTUAL_ENV=venv uv pip install GDAL=="$(gdal-config --version).*"

Note: We use `venv` directory for the project. If you use `direnv` to
manage your virtualenv, make sure it points to the same location. This is
required for the pyright pre-commit hook. Add this line to the top of your
`.envrc`, before the `layout python ...` line:

    export VIRTUAL_ENV=venv

## Run tests

Set up test database:

    $ make setup-test-db

Run tests against the docker test db:

    $ UV_PROJECT_ENVIRONMENT=venv VIRTUAL_ENV=venv uv run pytest

Run the tests themselves inside a docker container (used in CI):

    $ make docker-tests

## Update the graphql schema

    $ UV_PROJECT_ENVIRONMENT=venv VIRTUAL_ENV=venv uv run make graphql-schema

This is also done automatically by `pre-commit`.


## Additional documentation

- [Documentation on creating reports](./docs/README.reports.md)
- [Documentation on monitoring](./docs/README.monitoring.md)

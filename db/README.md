# alma Database

This folder contains the schema, migrations (managed with
[Flyway](https://flywaydb.org/)) and fixture data for the alma PostgreSQL /
PostGIS database.

If you run `make start-services` from the repository root, the database is
created and migrated automatically. The instructions below
are only needed if you want to work directly on the database or import a
specific dataset.

## Bring up an empty, migrated database

```bash
docker compose up -d db
make db-migrate
```

To inspect the database with a client such as DBeaver, connect to `localhost`,
port `5435`, database `alma`, and password `alma`.

## Importing data (geOps internal)

The steps below rely on a data dump that is only accessible to geOps
developers.

1. `docker compose up -d db`
2. `make db-migrate`
3. `touch ~/.netrc` and fill in credentials for the internal source
4. `make db-fetch-source`
5. `make db-import-non-anonymized`

## Makefile targets

Run database migrations:

    $ make db-migrate

Download data dump from altlast demo instance (requires credentials in `~/.netrc`):

    $ make db-fetch-source

Or import production data

    $ make db-import-non-anonymized

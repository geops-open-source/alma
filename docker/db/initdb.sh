#!/bin/bash

set -eu -o pipefail

# Create database users and schema/db
# See postgres docker docs for more info: https://hub.docker.com/_/postgres ("Initialization scripts")

# Important: If this script fails - for whatever reason:
# Postgres only executes scripts in docker-entrypoint-initdb.d on first start (when data is empty)
# So the container will exit, restart and then NOT run this again, effectively starting postgres
# without having added these users. So check the log of container if you cannot log in :)

# Important: This script is safe to be run manually/multiple times

# Create a user if it does not exist
create_user() { # (username, password)
    psql --quiet -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        DO
        \$\$
        BEGIN
        IF EXISTS (
            SELECT FROM pg_catalog.pg_roles
            WHERE  rolname = '$1') THEN
            RAISE NOTICE 'Role "$1" already exists, skipping.';
        ELSE
            CREATE ROLE $1 LOGIN PASSWORD '$2';
        END IF;
        END
        \$\$;
EOSQL
}

# Create a database if it does not exist with the specified owner_user
create_database() { # (database_name, owner_name)
    # db_link_exec needed as "CREATE DATABASE cannot be executed from a function"
    psql --quiet -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE EXTENSION IF NOT EXISTS dblink;
        DO
        \$\$
        BEGIN
        IF EXISTS (
            SELECT FROM pg_catalog.pg_database
            WHERE  datname = '$1') THEN
            RAISE NOTICE 'Database "$1" already exists, skipping.';
        ELSE
            PERFORM dblink_exec('', 'CREATE DATABASE $1 OWNER $2 encoding="utf8";');
        END IF;
        END
        \$\$;
EOSQL
}

# Create schema if not exists with specified owner
create_schema() { # database_name, schema_name, owner_name
    psql --quiet -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$1" <<-EOSQL
        CREATE SCHEMA IF NOT EXISTS $2 AUTHORIZATION $3;
EOSQL
}

# Grant all read operations to a user
allow_read() { # (database_name, schema_name, username)
    psql --quiet --username "$POSTGRES_USER" --dbname "$1" <<-EOSQL
        GRANT CONNECT ON DATABASE $1 TO $3;
        GRANT USAGE ON SCHEMA $2 TO $3;
        GRANT SELECT ON ALL TABLES IN SCHEMA $2 TO $3;
        ALTER DEFAULT PRIVILEGES IN SCHEMA $2 GRANT SELECT ON TABLES TO $3;
EOSQL
}

enable_extension() { # (database_name, extension_name)
    psql --quiet --username "$POSTGRES_USER" --dbname $1 <<-EOSQL
        CREATE EXTENSION IF NOT EXISTS $2;
EOSQL
}

if [ -z ${POSTGRES_NAGIOS_PASSWORD+x} ]
then echo "POSTGRES_NAGIOS_PASSWORD is unset, skipping!"
else create_user nagios $POSTGRES_NAGIOS_PASSWORD
fi

echo "NOTICE: SUCCESS: Created all postgres user accounts and grants"

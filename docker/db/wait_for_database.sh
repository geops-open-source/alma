#!/bin/bash
set -u -o pipefail

# Wait for PostgreSQL to accept connections
until pg_isready -U $POSTGRES_USER; do
    echo "Waiting for database to become ready ..."
    sleep 2
done

ARG BUILD_ENV="prod"

FROM postgres:18.3-bookworm AS build_base

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-18-postgis-3 \
        postgresql-18-postgis-3-scripts \
        postgresql-server-dev-18 \
        build-essential \
        pgxnclient \
    && rm -rf /var/lib/apt/lists/*

RUN pgxn install postgresql_anonymizer

FROM build_base AS build_prod
ONBUILD RUN mkdir /include
ONBUILD COPY db/include/ /include

FROM build_base AS build_review
ONBUILD RUN mkdir /include
ONBUILD COPY db/include/ /include
ONBUILD COPY ./db/data/alma_demo.dump /include
#checkov:skip=CKV_DOCKER_7: checkov cannot resolve the BUILD_ENV variable
FROM build_${BUILD_ENV}

COPY docker/db/wait_for_database.sh /usr/local/bin/
COPY docker/db/load_database_dump.sh /usr/local/bin/
COPY docker/db/initdb.sh /docker-entrypoint-initdb.d/
COPY docker/db/create_roles.sql /docker-entrypoint-initdb.d/

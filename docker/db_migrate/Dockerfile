FROM flyway/flyway:12

ENV FLYWAY_URL jdbc:postgresql://db:5432/alma
ENV FLYWAY_LOCATIONS filesystem:/sql
ENV FLYWAY_DEFAULT_SCHEMA meta

RUN mkdir /sql
COPY db/migrations/ /sql

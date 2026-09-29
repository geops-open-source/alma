alter table documents.asset add created_at timestamp with time zone not null;
alter table documents.asset add modified_at timestamp with time zone not null;

comment on column documents.asset.created_at is 'Erstelldatum der Datei';
comment on column documents.asset.modified_at is 'Zuletzt bearbeitet';


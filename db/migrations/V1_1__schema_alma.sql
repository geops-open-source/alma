create schema alma;

comment on schema alma is 'Main alma schema. Holds information on sites and their attributes.';

create schema alma_admin;
comment on schema alma_admin is 'Schema for admin settings and functions.';


create extension if not exists postgis with schema public;
create extension if not exists btree_gist with schema public; -- For exclude constraints

create schema alma_external;
comment on schema alma_external is 'Schema to store and update external data and data sources.';

create schema alma_export;
comment on schema alma_export is 'Schema for exports. Like INTERLIS, Reports and WMS/WFS.';

create schema documents;
comment on schema documents is 'Schema for documents uploaded.'

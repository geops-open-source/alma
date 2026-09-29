create table alma.h_gem (
    h_gem_id integer not null,
    bfs_nummer integer,
    gemeinde varchar(100) not null,
    wkb_geometry public.geometry,
    h_kanton integer default 15,
    c_kanton varchar(8),
    erfassungs_datum timestamp without time zone default now(),
    erfasser text,
    mutations_datum timestamp without time zone default now(),
    mutierer text,
    constraint pk_h_gem_h_gem_id primary key(h_gem_id),
    constraint h_gem_check check ((h_gem_id = bfs_nummer))
);


create index h_gem_geom_id on alma.h_gem using gist (wkb_geometry);

comment on table alma.h_gem is 'Gemeindegrenzen';
comment on column alma.h_gem.h_gem_id is 'primary key';
comment on column alma.h_gem.bfs_nummer is 'BfS-Nummer';
comment on column alma.h_gem.gemeinde is 'Gemeindename';
comment on column alma.h_gem.h_kanton is 'Codeliste Kanton';
comment on column alma.h_gem.c_kanton is 'Code Kanton';
comment on column alma.h_gem.erfassungs_datum is 'Datum der Erfassung';
comment on column alma.h_gem.erfasser is 'Erfasser';
comment on column alma.h_gem.mutations_datum is 'Datum der letzten Aenderung';
comment on column alma.h_gem.mutierer is 'Bearbeiter der letzten Aenderung';
comment on column alma.h_gem.wkb_geometry is 'Geometrie der Gemeinde.';


create table alma.h_ort (
    h_ort_id integer not null,
    h_gem_id integer,
    ortsname varchar(100),
    postleitzahl varchar,
    erfassungs_datum timestamp DEFAULT now() NULL,
    erfasser text,
    mutations_datum timestamp default now(),
    mutierer text,
    wkb_geometry public.geometry,
    lang text,
    constraint pk_h_ort_h_ort_id primary key (h_ort_id)
);
create index idx_h_ort_h_gem_id on alma.h_ort using btree (h_gem_id);
create index idx_h_ort_h_gem_id_ortsname on alma.h_ort using btree (h_gem_id, ortsname);
create index idx_h_ort_h_ort_id on alma.h_ort using btree (h_ort_id);


comment on table alma.h_ort is 'Ortschaften';
comment on column alma.h_ort.h_ort_id is 'primary key';
comment on column alma.h_ort.h_gem_id is 'Zugehoerige Gemeinde';
comment on column alma.h_ort.ortsname is 'Name des Ortes';
comment on column alma.h_ort.postleitzahl is 'Postleitzahl';
comment on column alma.h_ort.erfassungs_datum is 'Datum der Erfassung';
comment on column alma.h_ort.erfasser is 'Erfasser';
comment on column alma.h_ort.mutations_datum is 'Datum der letzten Aenderung';
comment on column alma.h_ort.mutierer is 'Bearbeiter der letzten Aenderung';
comment on column alma.h_ort.wkb_geometry is 'Geometrie des Ortes.';
comment on column alma.h_ort.lang is 'Sprache des Ortes.';


create table alma._kantone (
    ktnr integer not null,
    gdekt text,
    gdektna text,
    constraint pk__kantone_ktnr primary key (ktnr)
);

comment on table alma._kantone is 'Kantone';
comment on column alma._kantone.ktnr is 'Nummer des Kantons';
comment on column alma._kantone.gdekt is 'Kantonskuerzel';
comment on column alma._kantone.gdektna is 'Ausgeschriebener Name des Kantons';

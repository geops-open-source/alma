create table alma_export.interlis_cod_mapping (
    ili_code character varying(8) not null
    , ili_c_cli_id integer not null
    , code character varying(8) not null
    , c_cli_id integer not null
);

comment on table alma_export.interlis_cod_mapping is 'Zuordnung der alma Codes zu den INTERLIS Codes. Beispiel: c_cli_id = 63 zu c_cli_id = 20063, beinhaltet den Langen Codetext für INTERLIS';


create table alma_export.interlis_cod_long (
    code character varying(8) not null
    , c_cli_id integer not null
    , code_long text not null
);

comment on table alma_export.interlis_cod_long is 'Langtexte zu den INTERLIS Codes';


create table alma_export.interlis_settings (
    key character varying(40) not null
    , value text
);

comment on table alma_export.interlis_settings is 'Einstellungen und Parameter für die INTERLIS Exporte';


create table alma_export.interlis_task_mapping (
    ili_code character varying(8) not null
    , ili_c_cli_id integer not null
    , pro_uid character varying(32)
    , tas_uid character varying(32)
    , a4w_code character varying(20)
);

comment on table alma_export.interlis_task_mapping is 'Mapping für die Zuordnung von INTERLIS-Exporten zu Prozessen und Tasks';


create table alma_export.interlis_language_ordering (
    language_ordering_id integer not null
    , lang character varying not null
    , sort_key integer not null
);

comment on table alma_export.interlis_language_ordering is 'Reihenfolge der Sprachparameter';


create table alma_export.interlis_oereb_weitere_dokumente (
    dokument_tid text not null
    , beschreibung text not null
    , url_de text
    , url_fr text
    , url_it text
    , rechtsstatus text
    , publiziert_ab date
    , titel_de character varying(255)
    , titel_fr character varying(255)
    , titel_it character varying(255)
    , titel_rm character varying(255)
    , auszugindex integer
);

comment on table alma_export.interlis_oereb_weitere_dokumente is 'Weitere Rechtsgrundlagen für den OEREB-Export';


create table alma_export.interlis_symbol (
    code text not null,
    c_cli_id integer,
    symbol text not null,
    thema text,
    def_code text,
    artcodeliste text,
    url_verweiswms text,
    legende_status text,
    geometrytype text,
    export text
);

comment on table alma_export.interlis_symbol is 'Legenden und weitere amtsspezifische Informationen zur Altlasten-Beurteilung nach ÖREB Kataster';

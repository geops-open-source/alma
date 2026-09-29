create sequence alma_export.bafu_mapserver_id
    start with 1
    increment by 1
    no minvalue
    no maxvalue
    cache 1;
    
    
    
create table alma_export.wfs_bafu (
    mapserver_id integer default nextval('alma_export.bafu_mapserver_id'::regclass) not null,
    vflz_id integer,
    staonr character varying(50),
    staobezeichnung character varying,
    staotyp text,
    vollzug character varying(40),
    gemeinde_bfs integer,
    gemeinde character varying(100),
    kanton character varying(8),
    x_koordinate integer,
    y_koordinate integer,
    wkb_geometry public.geometry,
    betrieb_branchen text,
    betrieb_zeitraum text,
    ablag_zeitraum text,
    ablag_gesamtvol double precision,
    ablag_stoffe text,
    unfall_zeitpunkt text,
    unfall_stoffe text,
    vorkommnisse text,
    beurteilung text,
    umweltschutzmassnahmen text,
    gefaehrdete_umweltbereiche text,
    festgestellte_einwirkungen text,
    gewaesserschutzbereich text,
    gewaesserschutzzone text,
    ersteintrag_datum text,
    publikation_datum text,
    untersuchungsstand text,
    sanierungsziele text,
    priorisierung_sanierung smallint,
    priorisierung_untersuchung smallint,
    locale text
);

comment on table alma_export.wfs_bafu is 'Daten für den WFS Export ans BAFU in deutsch, französisch und italienisch. Die Aktualisierung erfolgt über die Funktion alma_export.bafu_update_data().';




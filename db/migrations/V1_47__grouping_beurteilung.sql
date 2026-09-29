alter table alma.cod_kbsinfo add column h_bewe_gruppe integer not null default 1031;
alter table alma.cod_kbsinfo add column c_bewe_gruppe character varying(8) not null default 'sonstige';

alter table alma.cod_kbsinfo add constraint fki_cod_bewegruppe_c_bere_gruppe foreign key (c_bewe_gruppe, h_bewe_gruppe) references alma.cod(code, c_cli_id) on delete cascade;

comment on column alma.cod_kbsinfo.h_bewe_gruppe is 'foreign key: Codeliste Beurteilung Gruppierung';
comment on column alma.cod_kbsinfo.c_bewe_gruppe is 'foreign key: Code Beurteilung Gruppierung';


-- delete from alma.cod where c_cli_id = 25001;
-- delete from alma.translations where msgid like 'code:25001:%';


create temporary table noga_import_raw (
    code text,
    parentcode text,
    name_de text,
    name_fr text,
    name_it text,
    name_rm text,
    name_en text,
    description_de text,
    description_fr text,
    description_it text,
    description_rm text,
    description_en text
);

\copy noga_import_raw (code, parentcode, name_de, name_fr, name_it, name_rm, name_en, description_de, description_fr, description_it, description_rm, description_en) from '/include/noga_codes.csv' with (format csv, header true, encoding 'UTF8');

insert into alma.c_cli (c_cli_id, c_status)
values (25001, true)
on conflict do nothing;

insert into alma.translations (msgid, msgstr, locale)
values
    ('codelist:25001', 'Branchencodes nach NOGA', 'de'),
    ('codelist:25001', 'Codes de branche selon NOGA', 'fr'),
    ('codelist:25001', 'Codici di settore secondo NOGA', 'it')
on conflict do nothing;

create temporary table noga_resolved as
select
    25001::integer as c_cli_id,
    r.code,
    r.name_de,
    r.name_fr,
    r.name_it
from (
    select distinct on (trim(code))
        trim(code) as code,
        nullif(trim(name_de), '') as name_de,
        nullif(trim(name_fr), '') as name_fr,
        nullif(trim(name_it), '') as name_it
    from noga_import_raw
    where nullif(trim(code), '') is not null
    order by trim(code),
             nullif(trim(name_de), '') desc,
             nullif(trim(name_fr), '') desc,
             nullif(trim(name_it), '') desc
) r;

insert into alma.cod (c_cli_id, code, sort_key, c_status)
select
    c_cli_id,
    code,
    row_number() over (order by code)::smallint as sort_key,
    true
from noga_resolved
on conflict (c_cli_id, code) do update
set
    c_status = excluded.c_status,
    sort_key = excluded.sort_key;

-- Keep existing German text when already present.
with prepared as (
    select
        c_cli_id,
        code,
        code || ' - ' || name_de as msgstr
    from noga_resolved
    where name_de is not null
)
insert into alma.translations (msgid, msgstr, locale)
select
    'code:' || c_cli_id || ':' || code,
    msgstr,
    'de'
from prepared
on conflict (msgid, locale) do nothing;

-- Always refresh FR/IT from source file.
with prepared as (
    select
        c_cli_id,
        code,
        code || ' - ' || name_fr as msgstr
    from noga_resolved
    where name_fr is not null
)
insert into alma.translations (msgid, msgstr, locale)
select
    'code:' || c_cli_id || ':' || code,
    msgstr,
    'fr'
from prepared
on conflict (msgid, locale) do update
set msgstr = excluded.msgstr;

with prepared as (
    select
        c_cli_id,
        code,
        code || ' - ' || name_it as msgstr
    from noga_resolved
    where name_it is not null
)
insert into alma.translations (msgid, msgstr, locale)
select
    'code:' || c_cli_id || ':' || code,
    msgstr,
    'it'
from prepared
on conflict (msgid, locale) do update
set msgstr = excluded.msgstr;

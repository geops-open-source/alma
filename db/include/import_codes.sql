-- Import codelists (c_cli) and their translations
create temporary table codelists_import (c_cli_id integer, de text, fr text, it text);
\copy codelists_import from '/include/codelists.csv' with delimiter ';' csv header;

insert into alma.c_cli (c_cli_id, c_status)
select c_cli_id, true from codelists_import
on conflict do nothing;

insert into alma.translations (msgid, msgstr, locale)
select 'codelist:' || c_cli_id, de, 'de' from codelists_import where de is not null and de != ''
union all
select 'codelist:' || c_cli_id, fr, 'fr' from codelists_import where fr is not null and fr != ''
union all
select 'codelist:' || c_cli_id, it, 'it' from codelists_import where it is not null and it != ''
on conflict do nothing;

-- Import codes (cod) and their translations
create temporary table codes_import (c_cli_id integer, code text, sort_key smallint, bemerkungen text, c_status text, c_is_null_code text, de text, fr text, it text);
\copy codes_import from '/include/codes.csv' with delimiter ';' csv header;

insert into alma.cod (c_cli_id, code, sort_key, bemerkungen, c_status, c_is_null_code)
select c_cli_id, code, sort_key, bemerkungen, c_status::boolean, c_is_null_code::boolean from codes_import
on conflict do nothing;

insert into alma.translations (msgid, msgstr, locale)
select 'code:' || c_cli_id || ':' || code, de, 'de' from codes_import where de is not null and de != ''
union all
select 'code:' || c_cli_id || ':' || code, fr, 'fr' from codes_import where fr is not null and fr != ''
union all
select 'code:' || c_cli_id || ':' || code, it, 'it' from codes_import where it is not null and it != ''
on conflict do nothing;

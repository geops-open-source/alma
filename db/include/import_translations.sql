create temporary table translations_import (
    id text,
    de text,
    fr text,
    it text
);

\copy translations_import from '/include/translations.csv' with delimiter ';' csv header;


-- German
insert into alma.translations (msgid, msgstr, locale)
select id, de, 'de' from translations_import ti
where not exists (
    select 1 from alma.translations t where t.msgid = ti.id and t.locale = 'de'
);

update alma.translations t set msgstr = ti.de
from translations_import ti
where t.msgid = ti.id and t.locale = 'de' and t.mutations_datum is null;

-- French
insert into alma.translations (msgid, msgstr, locale)
select id, fr, 'fr' from translations_import ti
where not exists (
    select 1 from alma.translations t where t.msgid = ti.id and t.locale = 'fr'
);

update alma.translations t set msgstr = ti.fr
from translations_import ti
where t.msgid = ti.id and t.locale = 'fr' and t.mutations_datum is null;

-- Italian
insert into alma.translations (msgid, msgstr, locale)
select id, it, 'it' from translations_import ti
where not exists (
    select 1 from alma.translations t where t.msgid = ti.id and t.locale = 'it'
);

update alma.translations t set msgstr = ti.it
from translations_import ti
where t.msgid = ti.id and t.locale = 'it' and t.mutations_datum is null;



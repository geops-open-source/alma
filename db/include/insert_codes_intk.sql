insert into alma.c_cli (c_cli_id, c_status) values (400, true)
on conflict do nothing;
insert into alma.cod (c_cli_id, code, c_status) values
    (400, 'park', true),
    (400, 'garten', true),
    (400, 'kiga', true),
    (400, 'kita', true),
    (400, 'spielplatz', true),
    (400, 'badeanstalt', true),
    (400, 'hausgarten', true),
    (400, 'familiengarten', true),
    (400, 'gemeinschaftsanlage', true)
on conflict do nothing;

insert into alma.c_cli (c_cli_id, c_status) values (401, true)
on conflict do nothing;
insert into alma.cod (c_cli_id, code, c_status) values
    (401, 'privat', true),
    (401, 'oeffentlich', true)
on conflict do nothing;

insert into alma.c_cli (c_cli_id, c_status) values (402, true)
on conflict do nothing;
insert into alma.cod (c_cli_id, code, c_status) values
    (402, '1-3', true),
    (402, '4-12', true)
on conflict do nothing;

insert into alma.translations (msgid, msgstr, locale) values
    ('code:400:park', 'Parkanlage mit Spielplätzen und Rasenflächen', 'de'),
    ('code:400:garten', 'Gartenanlage', 'de'),
    ('code:400:kiga', 'Kindergarten', 'de'),
    ('code:400:kita', 'Kindertagesstätte', 'de'),
    ('code:400:spielplatz', 'Spielplatz', 'de'),
    ('code:400:badeanstalt', 'Spielwiese Badeanstalt', 'de'),
    ('code:400:hausgarten', 'Hausgarten', 'de'),
    ('code:400:familiengarten', 'Familiengarten', 'de'),
    ('code:400:gemeinschaftsanlage', 'Gemeinschaftsanlage einer Überbauung', 'de'),
    ('code:400:park', 'Parc avec aires de jeux et pelouses', 'fr'),
    ('code:400:garten', 'Jardin', 'fr'),
    ('code:400:kiga', 'Maternelle', 'fr'),
    ('code:400:kita', 'Crèche', 'fr'),
    ('code:400:spielplatz', 'Aire de jeux', 'fr'),
    ('code:400:badeanstalt', 'Pelouse de baignade', 'fr'),
    ('code:400:hausgarten', 'Jardin privé', 'fr'),
    ('code:400:familiengarten', 'Jardin familial', 'fr'),
    ('code:400:gemeinschaftsanlage', 'Installation communautaire d’un complexe résidentiel', 'fr'),
    ('code:400:park', 'Parco con aree giochi e prati', 'it'),
    ('code:400:garten', 'Giardino', 'it'),
    ('code:400:kiga', 'Scuola materna', 'it'),
    ('code:400:kita', 'Asilo nido', 'it'),
    ('code:400:spielplatz', 'Parco giochi', 'it'),
    ('code:400:badeanstalt', 'Prato balneabile', 'it'),
    ('code:400:hausgarten', 'Giardino privato', 'it'),
    ('code:400:familiengarten', 'Giardino familiare', 'it'),
    ('code:400:gemeinschaftsanlage', 'Area comune di un complesso residenziale', 'it')
on conflict do nothing;


insert into alma.translations (msgid, msgstr, locale) values
    ('code:401:privat', 'Privat', 'de'),
    ('code:401:oeffentlich', 'Öffentlich', 'de'),
    ('code:401:privat', 'Privé', 'fr'),
    ('code:401:oeffentlich', 'Public', 'fr'),
    ('code:401:privat', 'Privato', 'it'),
    ('code:401:oeffentlich', 'Pubblico', 'it')
on conflict do nothing;

insert into alma.translations (msgid, msgstr, locale) values
    ('code:402:1-3', 'Kleinkinder 1-3 Jahre', 'de'),
    ('code:402:4-12', 'Kinder 4-12 Jahre', 'de'),
    ('code:402:1-3', 'Petits enfants 1-3 ans', 'fr'),
    ('code:402:4-12', 'Enfants 4-12 ans', 'fr'),
    ('code:402:1-3', 'Bambini piccoli 1-3 anni', 'it'),
    ('code:402:4-12', 'Bambini 4-12 anni', 'it')
on conflict do nothing;


insert into alma.cod (c_cli_id, code, c_status) values
    (63, '05', true)
on conflict do nothing;

insert into alma.translations (msgid, msgstr, locale) values
    ('code:63:05', 'Kinderspielplatz/Grünfläche', 'de'),
    ('code:63:05', 'Aire de jeux/espaces verts', 'fr'),
    ('code:63:05', 'Parco giochi/spazi verdi', 'it')
on conflict do nothing;

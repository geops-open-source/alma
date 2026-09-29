UPDATE "alma_admin"."auth_user" SET "subj_id"=1 WHERE "id"=2; -- lesen-sachdaten
UPDATE "alma_admin"."auth_user" SET "subj_id"=2 WHERE "id"=3; -- lesen-geschaefte
UPDATE "alma_admin"."auth_user" SET "subj_id"=3 WHERE "id"=4; -- bearbeiten-sachdaten
UPDATE "alma_admin"."auth_user" SET "subj_id"=4 WHERE "id"=5; -- bearbeiten-geschaefte
UPDATE "alma_admin"."auth_user" SET "subj_id"=5 WHERE "id"=6; -- admin
UPDATE "alma_admin"."auth_user" SET "sub"='system-user-sub' WHERE "username"='System-User'; -- system-user

-- system-user Suchen
INSERT INTO alma_admin.search (search_id, name, user_id, is_shared, query, fields, sort_by, is_grouped)
VALUES (
    99901,
    'Bearbeitungsstand Inhaberorientierung läuft',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'System-User'),
    true,
    '[{"name": "bearbeitungsstand", "value": "code:55:BAV_105", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);


INSERT INTO alma_admin.search (
    search_id, is_temporary, name, user_id, is_shared, query, fields, sort_by, is_grouped
)
VALUES (
    99902,
    false,
    'Publizierte Standorte',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'System-User'),
    true,
    '[{"name": "publiziert", "value": "1", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);

-- Suchen lesen-sachdaten Nutzer
INSERT INTO alma_admin.search (search_id, name, user_id, is_shared, query, fields, sort_by, is_grouped)
VALUES (
    99903,
    'Bearbeitungsstand Inhaberorientierung läuft',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'lesen-sachdaten'),
    false,
    '[{"name": "bearbeitungsstand", "value": "code:55:BAV_105", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);

INSERT INTO alma_admin.search (
    search_id, is_temporary, name, user_id, is_shared, query, fields, sort_by, is_grouped
)
VALUES (
    99904,
    false,
    'Publizierte Standorte',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'lesen-sachdaten'),
    false,
    '[{"name": "publiziert", "value": "1", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);

-- Suchen lesen-geschaefte Nutzer
INSERT INTO alma_admin.search (search_id, name, user_id, is_shared, query, fields, sort_by, is_grouped)
VALUES (
    99905,
    'Bearbeitungsstand Inhaberorientierung läuft',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'lesen-geschaefte'),
    false,
    '[{"name": "bearbeitungsstand", "value": "code:55:BAV_105", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);

INSERT INTO alma_admin.search (
    search_id, is_temporary, name, user_id, is_shared, query, fields, sort_by, is_grouped
)
VALUES (
    99906,
    false,
    'Publizierte Standorte',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'lesen-geschaefte'),
    false,
    '[{"name": "publiziert", "value": "1", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);


-- Suchen bearbeiten-sachdaten Nutzer
INSERT INTO alma_admin.search (search_id, name, user_id, is_shared, query, fields, sort_by, is_grouped)
VALUES (
    99907,
    'Bearbeitungsstand Inhaberorientierung läuft',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'bearbeiten-sachdaten'),
    false,
    '[{"name": "bearbeitungsstand", "value": "code:55:BAV_105", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);

INSERT INTO alma_admin.search (
    search_id, is_temporary, name, user_id, is_shared, query, fields, sort_by, is_grouped
)
VALUES (
    99908,
    false,
    'Publizierte Standorte',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'bearbeiten-sachdaten'),
    false,
    '[{"name": "publiziert", "value": "1", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);



-- Suchen bearbeiten-geschaefte Nutzer
INSERT INTO alma_admin.search (search_id, name, user_id, is_shared, query, fields, sort_by, is_grouped)
VALUES (
    99909,
    'Bearbeitungsstand Inhaberorientierung läuft',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'bearbeiten-geschaefte'),
    false,
    '[{"name": "bearbeitungsstand", "value": "code:55:BAV_105", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);

INSERT INTO alma_admin.search (
    search_id, is_temporary, name, user_id, is_shared, query, fields, sort_by, is_grouped
)
VALUES (
    99910,
    false,
    'Publizierte Standorte',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'bearbeiten-geschaefte'),
    false,
    '[{"name": "publiziert", "value": "1", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);

-- Suchen admin Nutzer
INSERT INTO alma_admin.search (search_id, name, user_id, is_shared, query, fields, sort_by, is_grouped)
VALUES (
    99911,
    'Bearbeitungsstand Inhaberorientierung läuft',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'admin'),
    false,
    '[{"name": "bearbeitungsstand", "value": "code:55:BAV_105", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);

INSERT INTO alma_admin.search (
    search_id, is_temporary, name, user_id, is_shared, query, fields, sort_by, is_grouped
)
VALUES (
    99912,
    false,
    'Publizierte Standorte',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'admin'),
    false,
    '[{"name": "publiziert", "value": "1", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);

INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99901, 99902]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'System-User')
);


INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99903, 99904]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'lesen-sachdaten')
);


INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99905, 99906]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'lesen-geschaefte')
);

INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99907, 99908]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'bearbeiten-sachdaten')
);


INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99909, 99910]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'bearbeiten-geschaefte')
);


INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99911, 99912]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'admin')
);

-- Load initial data required for the demo instance

-- delete old data
DELETE FROM alma_admin.auth_user where username = 'test@alma-os.ch';

-- Set up test@alma-os.ch user with ADMINISTRATION role:
INSERT INTO alma_admin.auth_user (
    sub,
    username,
    role_id,
    email,
    is_sachbearbeitung
) VALUES (
    '99d3ec21-9c8e-493d-9be0-f7fdf915d925',  -- as in keycloak initial data
    'test@alma-os.ch',
    (
        SELECT id
        FROM alma_admin.auth_role
        WHERE name = 'ADMINISTRATION'
    ),
    'test@alma-os.ch',
    true
);

-- delete old data
DELETE FROM alma_admin.auth_user where username = 'test-view_vfl@alma-os.ch';

-- Set up test-view_vfl@alma-os.ch  user with LESEN_SACHDATEN role:
INSERT INTO alma_admin.auth_user (
    sub,
    username,
    role_id,
    email,
    is_sachbearbeitung
) VALUES (
    '99d3ec21-9c8e-493d-9be0-f7fdf915d926',  -- as in keycloak initial data
    'test-view_vfl@alma-os.ch',
    (
        SELECT id
        FROM alma_admin.auth_role
        WHERE name = 'LESEN_SACHDATEN'
    ),
    'test-view_vfl@alma-os.ch',
    true
);

-- delete old data
DELETE FROM alma_admin.auth_user where username = 'test-edit_vfl@alma-os.ch';

-- Set up test-edit_vfl@alma-os.ch user with BEARBEITEN_SACHDATEN role:
INSERT INTO alma_admin.auth_user (
    sub,
    username,
    role_id,
    email,
    is_sachbearbeitung
) VALUES (
    '99d3ec21-9c8e-493d-9be0-f7fdf915d927',  -- as in keycloak initial data
    'test-edit_vfl@alma-os.ch',
    (
        SELECT id
        FROM alma_admin.auth_role
        WHERE name = 'BEARBEITEN_SACHDATEN'
    ),
    'test-edit_vfl@alma-os.ch',
    true
);

-- delete old data
DELETE FROM alma_admin.auth_user where username = 'test-view_process@alma-os.ch';

-- Set up test-view_process@alma-os.ch user with LESEN_GESCHAEFTE role:
INSERT INTO alma_admin.auth_user (
    sub,
    username,
    role_id,
    email,
    is_sachbearbeitung
) VALUES (
    '99d3ec21-9c8e-493d-9be0-f7fdf915d928',  -- as in keycloak initial data
    'test-view_process@alma-os.ch',
    (
        SELECT id
        FROM alma_admin.auth_role
        WHERE name = 'LESEN_GESCHAEFTE'
    ),
    'test-view_process@alma-os.ch',
    true
);

-- delete old data
DELETE FROM alma_admin.auth_user where username = 'test-edit_process@alma-os.ch';

-- Set up test-edit_process@alma-os.ch user with BEARBEITEN_GESCHAEFTE role:
INSERT INTO alma_admin.auth_user (
    sub,
    username,
    role_id,
    email,
    is_sachbearbeitung
) VALUES (
    '99d3ec21-9c8e-493d-9be0-f7fdf915d929',  -- as in keycloak initial data
    'test-edit_process@alma-os.ch',
    (
        SELECT id
        FROM alma_admin.auth_role
        WHERE name = 'BEARBEITEN_GESCHAEFTE'
    ),
    'test-edit_process@alma-os.ch',
    true
);


insert into alma.subj(subj_id, name, vorname, taetigkeit)
values (9000000, 'Test', 'Admin', 'Demo User')
on conflict do nothing;

insert into alma.subj(subj_id, name, vorname, taetigkeit)
values (9001000, 'Test', 'Lesen Sachdaten', 'Demo User')
on conflict do nothing;

insert into alma.subj(subj_id, name, vorname, taetigkeit)
values (9002000, 'Test', 'Bearbeiten Sachdaten', 'Demo User')
on conflict do nothing;

insert into alma.subj(subj_id, name, vorname, taetigkeit)
values (9003000, 'Test', 'Lesen Geschaefte', 'Demo User')
on conflict do nothing;

insert into alma.subj(subj_id, name, vorname, taetigkeit)
values (9004000, 'Test', 'Bearbeiten Geschaefte', 'Demo User')
on conflict do nothing;

update alma_admin.auth_user set subj_id = 9000000
where email='test@alma-os.ch';

update alma_admin.auth_user set subj_id = 9001000
where email='test-view_vfl@alma-os.ch';

update alma_admin.auth_user set subj_id = 9002000
where email='test-edit_vfl@alma-os.ch';

update alma_admin.auth_user set subj_id = 9003000
where email='test-view_process@alma-os.ch';

update alma_admin.auth_user set subj_id = 9004000
where email='test-edit_process@alma-os.ch';



-- Suchen test@alma-os.ch Nutzer
INSERT INTO alma_admin.search (search_id, name, user_id, is_shared, query, fields, sort_by, is_grouped)
VALUES (
    99901,
    'Bearbeitungsstand Inhaberorientierung läuft',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test@alma-os.ch'),
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
    99902,
    false,
    'Publizierte Standorte',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test@alma-os.ch'),
    false,
    '[{"name": "publiziert", "value": "1", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);

-- Suchen test-view_vfl@alma-os.ch Nutzer
INSERT INTO alma_admin.search (search_id, name, user_id, is_shared, query, fields, sort_by, is_grouped)
VALUES (
    99903,
    'Bearbeitungsstand Inhaberorientierung läuft',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-view_vfl@alma-os.ch'),
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
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-view_vfl@alma-os.ch'),
    false,
    '[{"name": "publiziert", "value": "1", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);


-- Suchen test-edit_vfl@alma-os.ch Nutzer
INSERT INTO alma_admin.search (search_id, name, user_id, is_shared, query, fields, sort_by, is_grouped)
VALUES (
    99905,
    'Bearbeitungsstand Inhaberorientierung läuft',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-edit_vfl@alma-os.ch'),
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
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-edit_vfl@alma-os.ch'),
    false,
    '[{"name": "publiziert", "value": "1", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);



-- Suchen test-view_process@alma-os.ch Nutzer
INSERT INTO alma_admin.search (search_id, name, user_id, is_shared, query, fields, sort_by, is_grouped)
VALUES (
    99907,
    'Bearbeitungsstand Inhaberorientierung läuft',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-view_process@alma-os.ch'),
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
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-view_process@alma-os.ch'),
    false,
    '[{"name": "publiziert", "value": "1", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
);

-- Suchen test-edit_process@alma-os.ch Nutzer
INSERT INTO alma_admin.search (search_id, name, user_id, is_shared, query, fields, sort_by, is_grouped)
VALUES (
    99909,
    'Bearbeitungsstand Inhaberorientierung läuft',
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-edit_process@alma-os.ch'),
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
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-edit_process@alma-os.ch'),
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
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test@alma-os.ch')
);

INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99903, 99904]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-view_vfl@alma-os.ch')
);

INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99905, 99906]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-edit_vfl@alma-os.ch')
);

INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99907, 99908]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-view_process@alma-os.ch')
);

INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99909, 99910]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-edit_process@alma-os.ch')
);

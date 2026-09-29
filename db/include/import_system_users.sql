-- Set up screenshot@alma-os.ch user with LESEN_SACHDATEN role:
insert into alma_admin.auth_user(sub, username, email, first_name, last_name, is_system_user)
values ('99d3ec21-9c8e-493d-9be0-f7fdf915d949', 'screenshot', 'screenshot@geops.ch', '', 'Screenshot User', true)
on conflict do nothing;

update alma_admin.auth_user
set role_id = (
    select id
    from alma_admin.auth_role
    where name = 'LESEN_SACHDATEN'
)
where email = 'screenshot@geops.ch';


-- Set up monitoring@alma-os.ch user with LESEN_SACHDATEN role:
insert into alma_admin.auth_user(sub, username, email, first_name, last_name, is_system_user)
values ('99d3ec21-9c8e-493d-9be0-f7fdf915d950', 'monitoring', 'monitoring@geops.ch', '', 'Monitoring User', true)
on conflict do nothing;

update alma_admin.auth_user
set role_id = (
    select id
    from alma_admin.auth_role
    where name = 'LESEN_SACHDATEN'
)
where email = 'monitoring@geops.ch';


insert into alma_admin.auth_user (sub, username, email, first_name, last_name, is_sachbearbeitung, is_system_user)
values ('99d3ec21-9c8e-493d-9be0-f7fdf915d951', 'System User', 'system-user@geops.ch', '', 'System User', false, true)
on conflict do nothing;

update alma_admin.auth_user
set role_id = (
    select id
    from alma_admin.auth_role
    where name = 'ADMINISTRATION'
)
where username = 'System User';


insert into alma_admin.search (
    search_id, is_temporary, name, user_id, is_shared, query, fields, sort_by, is_grouped
)
values (
    77771,
    false,
    'Bearbeitungsstand Inhaberorientierung läuft', 
    (select id from alma_admin.auth_user where username = 'System User'),
    true,
    '[{"name": "bearbeitungsstand", "value": "code:55:BAV_105", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
)
on conflict do nothing;

insert into alma_admin.search (
    search_id, is_temporary, name, user_id, is_shared, query, fields, sort_by, is_grouped
)
values (
    77772,
    false,
    'Publizierte Standorte',
    (select id from alma_admin.auth_user where username = 'System User'),
    true,
    '[{"name": "publiziert", "value": "1", "__type__": "expression", "operator": "="}]'::jsonb,
    '["standortnummer", "bezeichnung", "gemeinde", "beurteilung", "standorttyp"]'::jsonb,
    '[]'::jsonb,
    false
)
on conflict do nothing;

insert into alma_admin.user_settings (user_id, key, value)
values (
    (select id from alma_admin.auth_user where username = 'System User'),
    'dashboardSavedSearches',
    '[77771,77772]'::jsonb
)
on conflict do nothing;

-- Load initial data required for the demo instance

-- Set up test@alma-os.ch user with ADMINISTRATION role:

insert into alma_admin.auth_user (sub, username, email, is_sachbearbeitung)
values ('99d3ec21-9c8e-493d-9be0-f7fdf915d925', 'test@alma-os.ch', 'test@alma-os.ch', true)
on conflict do nothing;

update alma_admin.auth_user
set role_id = (
    select id
    from alma_admin.auth_role
    where name = 'ADMINISTRATION'
)
where email = 'test@alma-os.ch';

-- Set up test-view_vfl@alma-os.ch user with LESEN_SACHDATEN role:

insert into alma_admin.auth_user (sub, username, email, is_sachbearbeitung)
values ('99d3ec21-9c8e-493d-9be0-f7fdf915d926', 'test-view_vfl@alma-os.ch', 'test-view_vfl@alma-os.ch', true)
on conflict do nothing;

update alma_admin.auth_user
set role_id = (
    select id
    from alma_admin.auth_role
    where name = 'LESEN_SACHDATEN'
)
where email = 'test-view_vfl@alma-os.ch';

-- Set up test-edit_vfl@alma-os.ch user with BEARBEITEN_SACHDATEN role:

insert into alma_admin.auth_user (sub, username, email, is_sachbearbeitung)
values ('99d3ec21-9c8e-493d-9be0-f7fdf915d927', 'test-edit_vfl@alma-os.ch', 'test-edit_vfl@alma-os.ch', true)
on conflict do nothing;

update alma_admin.auth_user
set role_id = (
    select id
    from alma_admin.auth_role
    where name = 'BEARBEITEN_SACHDATEN'
)
where email = 'test-edit_vfl@alma-os.ch';

-- Set up test-view_process@alma-os.ch user with LESEN_GESCHAEFTE role:

insert into alma_admin.auth_user (sub, username, email, is_sachbearbeitung)
values ('99d3ec21-9c8e-493d-9be0-f7fdf915d928', 'test-view_process@alma-os.ch', 'test-view_process@alma-os.ch', true)
on conflict do nothing;

update alma_admin.auth_user
set role_id = (
    select id
    from alma_admin.auth_role
    where name = 'LESEN_GESCHAEFTE'
)
where email = 'test-view_process@alma-os.ch';

-- Set up test-edit_process@alma-os.ch user with BEARBEITEN_GESCHAEFTE role:

insert into alma_admin.auth_user (sub, username, email, is_sachbearbeitung)
values ('99d3ec21-9c8e-493d-9be0-f7fdf915d929', 'test-edit_process@alma-os.ch', 'test-edit_process@alma-os.ch', true)
on conflict do nothing;

update alma_admin.auth_user
set role_id = (
    select id
    from alma_admin.auth_role
    where name = 'BEARBEITEN_GESCHAEFTE'
)
where email = 'test-edit_process@alma-os.ch';



insert into alma.subj(subj_id, name, vorname, taetigkeit)
values (9000000, 'User', 'Test', 'Test User')
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
) on conflict do nothing;

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
) on conflict do nothing;

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
) on conflict do nothing;

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
) on conflict do nothing;


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
) on conflict do nothing;

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
) on conflict do nothing;



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
) on conflict do nothing;

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
) on conflict do nothing;

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
) on conflict do nothing;

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
) on conflict do nothing;

INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99901, 99902]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test@alma-os.ch')
) on conflict do nothing;

INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99903, 99904]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-view_vfl@alma-os.ch')
) on conflict do nothing;

INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99905, 99906]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-edit_vfl@alma-os.ch')
) on conflict do nothing;

INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99907, 99908]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-view_process@alma-os.ch')
) on conflict do nothing;

INSERT INTO alma_admin.user_settings (
    key, value, user_id
)
values (
    'dashboardSavedSearches',
    '[99909, 99910]'::jsonb,
    (SELECT id FROM alma_admin.auth_user WHERE username = 'test-edit_process@alma-os.ch')
) on conflict do nothing;

INSERT INTO "alma_admin"."settings"("key","value","value_schema","category") VALUES (
    'mapLayerTree.editor',
    '[{"id": "pc6gs4h", "type": "Group", "items": [{"id": "b4c3bwj", "url": "https://wfs.geodienste.ch/planerischer_gewaesserschutz_v1_2_0/deu?", "name": "gewaesserschutzbereiche", "type": "WMS", "title": "gewaesserschutzbereiche", "opacity": 0.37, "version": 1, "visible": true}, {"id": "97n3n2j", "url": "https://wfs.geodienste.ch/planerischer_gewaesserschutz_v1_2_0/deu?", "name": "grundwasserschutzzonen", "type": "WMS", "title": "grundwasserschutzzonen", "opacity": 0.4, "version": 1, "visible": true}], "title": "geodienste.ch WMS Planerischer Gewässerschutz", "version": 1, "visible": true, "collapsed": false}, {"id": "erzq9sl", "url": "https://wfs.geodienste.ch/av_0/deu?SERVICE=WFS&REQUEST=GetFeature&VERSION=1.1.0&TYPENAMES=ms%3ARESF&SRSNAME=EPSG%3A2056", "type": "WFS", "title": "Liegenschaften", "version": 1, "visible": true, "scaleRange": "large"}, {"id": "vflzSearchLayer", "type": "Layer", "version": 1, "visible": true}]',
        $json_schema$
        {
            "$schema": "https://json-schema.org/draft-07/schema#",
            "definitions": {
                "base": {
                    "type": "object",
                    "properties": {
                        "id": { "type": "string", "minLength": 1 },
                        "opacity": { "type": "number", "minimum": 0, "maximum": 1 },
                        "scaleRange": { "enum": ["large"] },
                        "version": { "type": "integer", "minimum": 1 },
                        "visible": { "type": "boolean" }
                    },
                    "required": ["id", "type", "version"]
                },
                "layer": {
                    "allOf": [
                        { "$ref": "#/definitions/base" },
                        {
                            "type": "object",
                            "properties": {
                                "type": { "enum": ["Layer"] }
                            }
                        }
                    ]
                },
                "wfs": {
                    "allOf": [
                        { "$ref": "#/definitions/base" },
                        {
                            "type": "object",
                            "properties": {
                                "title": { "type": "string", "minLength": 1 },
                                "type": { "enum": ["WFS"] },
                                "url": { "type": "string", "minLength": 1 }
                            },
                            "required": ["title", "url"]
                        }
                    ]
                },
                "wms": {
                    "allOf": [
                        { "$ref": "#/definitions/base" },
                        {
                            "type": "object",
                            "properties": {
                                "legend": { "type": "string" },
                                "name": { "type": "string", "minLength": 1 },
                                "title": { "type": "string", "minLength": 1 },
                                "type": { "enum": ["WMS"] },
                                "url": { "type": "string", "minLength": 1 }
                            },
                            "required": ["name", "title", "url"]
                        }
                    ]
                },
                "wmts": {
                    "allOf": [
                        { "$ref": "#/definitions/base" },
                        {
                            "type": "object",
                            "properties": {
                                "dimensions": {
                                    "type": "object",
                                    "additionalProperties": { "type": "string" }
                                },
                                "format": { "type": "string", "minLength": 1 },
                                "layer": { "type": "string", "minLength": 1 },
                                "legend": { "type": "string" },
                                "matrixSet": { "type": "string", "minLength": 1 },
                                "projection": { "type": "string", "minLength": 1 },
                                "requestEncoding": { "enum": ["KVP", "REST"] },
                                "style": { "type": "string", "minLength": 1 },
                                "tileGrid": {
                                    "type": "object",
                                    "properties": {
                                        "matrixIds": {
                                            "type": "array",
                                            "items": { "type": "string", "minLength": 1 }
                                        },
                                        "origins": {
                                            "type": "array",
                                            "items": {
                                                "type": "array",
                                                "items": { "type": "number" }
                                            }
                                        },
                                        "resolutions": {
                                            "type": "array",
                                            "items": { "type": "number" }
                                        },
                                        "sizes": {
                                            "type": "array",
                                            "items": {
                                                "type": "array",
                                                "items": { "type": "number" }
                                            }
                                        }
                                    },
                                    "required": ["matrixIds", "origins", "resolutions", "sizes"],
                                    "additionalProperties": false
                                },
                                "title": { "type": "string", "minLength": 1 },
                                "type": { "enum": ["WMTS"] },
                                "url": { "type": "string", "minLength": 1 }
                            },
                            "required": [
                                "dimensions",
                                "format",
                                "layer",
                                "matrixSet",
                                "projection",
                                "requestEncoding",
                                "style",
                                "tileGrid",
                                "title",
                                "url"
                            ]
                        }
                    ]
                },
                "leafItem": {
                    "oneOf": [
                        { "$ref": "#/definitions/layer" },
                        { "$ref": "#/definitions/wfs" },
                        { "$ref": "#/definitions/wms" },
                        { "$ref": "#/definitions/wmts" }
                    ]
                },
                "group": {
                    "allOf": [
                        { "$ref": "#/definitions/base" },
                        {
                            "type": "object",
                            "properties": {
                                "collapsed": { "type": "boolean" },
                                "items": {
                                    "type": "array",
                                    "items": { "$ref": "#/definitions/leafItem" }
                                },
                                "title": { "type": "string", "minLength": 1 },
                                "type": { "enum": ["Group"] }
                            },
                            "required": ["items", "title"]
                        }
                    ]
                },
                "item": {
                    "oneOf": [
                        { "$ref": "#/definitions/layer" },
                        { "$ref": "#/definitions/wfs" },
                        { "$ref": "#/definitions/wms" },
                        { "$ref": "#/definitions/wmts" },
                        { "$ref": "#/definitions/group" }
                    ]
                }
            },
            "type": "array",
            "items": { "$ref": "#/definitions/item" }
        }
        $json_schema$,
    'USER_INITIAL'
) ON CONFLICT ("key", "category") DO UPDATE
SET "value" = EXCLUDED."value";

INSERT INTO "alma_admin"."settings"("key","value","value_schema","category") VALUES (
    'mapLayerTree.search',
    '[{"id": "pc6gs4h", "type": "Group", "items": [{"id": "b4c3bwj", "url": "https://wfs.geodienste.ch/planerischer_gewaesserschutz_v1_2_0/deu?", "name": "gewaesserschutzbereiche", "type": "WMS", "title": "gewaesserschutzbereiche", "opacity": 0.37, "version": 1, "visible": true}, {"id": "97n3n2j", "url": "https://wfs.geodienste.ch/planerischer_gewaesserschutz_v1_2_0/deu?", "name": "grundwasserschutzzonen", "type": "WMS", "title": "grundwasserschutzzonen", "opacity": 0.4, "version": 1, "visible": true}], "title": "geodienste.ch WMS Planerischer Gewässerschutz", "version": 1, "visible": true, "collapsed": false}, {"id": "erzq9sl", "url": "https://wfs.geodienste.ch/av_0/deu?SERVICE=WFS&REQUEST=GetFeature&VERSION=1.1.0&TYPENAMES=ms%3ARESF&SRSNAME=EPSG%3A2056", "type": "WFS", "title": "Liegenschaften", "version": 1, "visible": true, "scaleRange": "large"}, {"id": "vflzSearchLayer", "type": "Layer", "version": 1, "visible": true}]',
        $json_schema$
        {
            "$schema": "https://json-schema.org/draft-07/schema#",
            "definitions": {
                "base": {
                    "type": "object",
                    "properties": {
                        "id": { "type": "string", "minLength": 1 },
                        "opacity": { "type": "number", "minimum": 0, "maximum": 1 },
                        "scaleRange": { "enum": ["large"] },
                        "version": { "type": "integer", "minimum": 1 },
                        "visible": { "type": "boolean" }
                    },
                    "required": ["id", "type", "version"]
                },
                "layer": {
                    "allOf": [
                        { "$ref": "#/definitions/base" },
                        {
                            "type": "object",
                            "properties": {
                                "type": { "enum": ["Layer"] }
                            }
                        }
                    ]
                },
                "wfs": {
                    "allOf": [
                        { "$ref": "#/definitions/base" },
                        {
                            "type": "object",
                            "properties": {
                                "title": { "type": "string", "minLength": 1 },
                                "type": { "enum": ["WFS"] },
                                "url": { "type": "string", "minLength": 1 }
                            },
                            "required": ["title", "url"]
                        }
                    ]
                },
                "wms": {
                    "allOf": [
                        { "$ref": "#/definitions/base" },
                        {
                            "type": "object",
                            "properties": {
                                "legend": { "type": "string" },
                                "name": { "type": "string", "minLength": 1 },
                                "title": { "type": "string", "minLength": 1 },
                                "type": { "enum": ["WMS"] },
                                "url": { "type": "string", "minLength": 1 }
                            },
                            "required": ["name", "title", "url"]
                        }
                    ]
                },
                "wmts": {
                    "allOf": [
                        { "$ref": "#/definitions/base" },
                        {
                            "type": "object",
                            "properties": {
                                "dimensions": {
                                    "type": "object",
                                    "additionalProperties": { "type": "string" }
                                },
                                "format": { "type": "string", "minLength": 1 },
                                "layer": { "type": "string", "minLength": 1 },
                                "legend": { "type": "string" },
                                "matrixSet": { "type": "string", "minLength": 1 },
                                "projection": { "type": "string", "minLength": 1 },
                                "requestEncoding": { "enum": ["KVP", "REST"] },
                                "style": { "type": "string", "minLength": 1 },
                                "tileGrid": {
                                    "type": "object",
                                    "properties": {
                                        "matrixIds": {
                                            "type": "array",
                                            "items": { "type": "string", "minLength": 1 }
                                        },
                                        "origins": {
                                            "type": "array",
                                            "items": {
                                                "type": "array",
                                                "items": { "type": "number" }
                                            }
                                        },
                                        "resolutions": {
                                            "type": "array",
                                            "items": { "type": "number" }
                                        },
                                        "sizes": {
                                            "type": "array",
                                            "items": {
                                                "type": "array",
                                                "items": { "type": "number" }
                                            }
                                        }
                                    },
                                    "required": ["matrixIds", "origins", "resolutions", "sizes"],
                                    "additionalProperties": false
                                },
                                "title": { "type": "string", "minLength": 1 },
                                "type": { "enum": ["WMTS"] },
                                "url": { "type": "string", "minLength": 1 }
                            },
                            "required": [
                                "dimensions",
                                "format",
                                "layer",
                                "matrixSet",
                                "projection",
                                "requestEncoding",
                                "style",
                                "tileGrid",
                                "title",
                                "url"
                            ]
                        }
                    ]
                },
                "leafItem": {
                    "oneOf": [
                        { "$ref": "#/definitions/layer" },
                        { "$ref": "#/definitions/wfs" },
                        { "$ref": "#/definitions/wms" },
                        { "$ref": "#/definitions/wmts" }
                    ]
                },
                "group": {
                    "allOf": [
                        { "$ref": "#/definitions/base" },
                        {
                            "type": "object",
                            "properties": {
                                "collapsed": { "type": "boolean" },
                                "items": {
                                    "type": "array",
                                    "items": { "$ref": "#/definitions/leafItem" }
                                },
                                "title": { "type": "string", "minLength": 1 },
                                "type": { "enum": ["Group"] }
                            },
                            "required": ["items", "title"]
                        }
                    ]
                },
                "item": {
                    "oneOf": [
                        { "$ref": "#/definitions/layer" },
                        { "$ref": "#/definitions/wfs" },
                        { "$ref": "#/definitions/wms" },
                        { "$ref": "#/definitions/wmts" },
                        { "$ref": "#/definitions/group" }
                    ]
                }
            },
            "type": "array",
            "items": { "$ref": "#/definitions/item" }
        }
        $json_schema$,
    'USER_INITIAL'
) ON CONFLICT ("key", "category") DO UPDATE
SET "value" = EXCLUDED."value";

INSERT INTO alma_admin.user_settings (
    user_id, key, value
)
SELECT
    auth_user.id,
    settings.key,
    settings.value
FROM alma_admin.auth_user AS auth_user
CROSS JOIN alma_admin.settings AS settings
WHERE settings.category = 'USER_INITIAL'
ON CONFLICT DO NOTHING;

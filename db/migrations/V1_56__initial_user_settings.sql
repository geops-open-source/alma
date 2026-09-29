alter table alma_admin.settings drop constraint ck_settings_category;

alter table alma_admin.settings
add constraint ck_settings_category check (
    category in ('ADMIN', 'GENERAL', 'USER_INITIAL')
);
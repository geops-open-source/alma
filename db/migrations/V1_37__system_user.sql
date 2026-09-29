alter table alma_admin.auth_user add is_system_user boolean not null default false;

comment on column alma_admin.auth_user.is_system_user is 'Indicates if the user is a system user (not a human user). Default is false.';

update alma_admin.auth_user set is_system_user = true
where email in ('screenshot@geops.ch', 'monitoring@geops.ch');

 -- Create temporary table with user mapping
create temp table domain_data_user_mapping as
select
    domain_data_auth_user.username,
    domain_data_auth_user.id as domain_data_user_id,
    domain_data_auth_user.subj_id as domain_data_subj_id,
    user_to_keep.id as user_to_keep_id,
    user_to_keep.subj_id as user_to_keep_subj_id
from alma_admin.auth_user user_to_keep
join alma_admin.domain_data_auth_user domain_data_auth_user
on domain_data_auth_user.username = user_to_keep.username;

\echo ''
\echo 'Update subj_id in auth_user for those that exist in domain_data_auth_user'
update alma_admin.auth_user
set subj_id = domain_data_user_mapping.user_to_keep_subj_id
from domain_data_user_mapping
where subj_id = domain_data_user_mapping.domain_data_subj_id;


\echo ''
\echo 'Insert new subj records for those that do not exist in alma.subj but are assigned to users in auth_user'
insert into alma.subj (
    "name",
    vorname,
    taetigkeit,
    kuerzel,
    h_land,
    c_land,
    h_anrede,
    c_anrede,
    ident_nr,
    import_key,
    ort,
    postleitzahl,
    strasse,
    erfassungs_datum,
    erfasser,
    mutations_datum,
    mutierer
)
select
    user_data_subj."name",
    user_data_subj.vorname,
    user_data_subj.taetigkeit,
    user_data_subj.kuerzel,
    user_data_subj.h_land,
    user_data_subj.c_land,
    user_data_subj.h_anrede,
    user_data_subj.c_anrede,
    user_data_subj.ident_nr,
    user_data_subj.import_key,
    user_data_subj.ort,
    user_data_subj.postleitzahl,
    user_data_subj.strasse,
    user_data_subj.erfassungs_datum,
    user_data_subj.erfasser,
    user_data_subj.mutations_datum,
    user_data_subj.mutierer
from alma.user_data_subj user_data_subj
where subj_id in (
    select subj_id
    from alma_admin.auth_user -- only create subj that are assigned to users but do not exist in alma.subj
    where subj_id not in (
        select subj_id from alma.subj
    )
);

\echo ''
\echo 'Assign the newly created subj_id to auth_user by matching on name and vorname'
update alma_admin.auth_user
set subj_id = subj.subj_id
from alma.user_data_subj user_data_subj
join alma.subj subj on (
    subj."name" = user_data_subj."name"
    and subj.vorname = user_data_subj.vorname
)
where alma_admin.auth_user.subj_id = user_data_subj.subj_id;

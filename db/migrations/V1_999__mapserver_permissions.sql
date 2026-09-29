do $$ begin
  if not '${skipPermissionGrants}' then
    grant connect on database alma to mapserver;
    grant USAGE on schema alma_export to mapserver;
    grant USAGE on schema alma to mapserver;
    grant select on ALL TABLES in schema alma_export to mapserver;
    grant select on ALL TABLES in schema alma to mapserver;
    -- ensure SELECT privileges on future tables
    alter default privileges in schema alma_export grant select on tables to mapserver;
    alter default privileges in schema alma grant select on tables to mapserver;
  end if;
end $$;


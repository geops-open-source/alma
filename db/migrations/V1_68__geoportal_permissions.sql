do $$ begin
  if '${grantGeoportalRoPermissions}' then
        grant connect on database alma to geoportal_ro;
        grant usage on schema alma_export to geoportal_ro;
        grant select on all tables in schema alma_export to geoportal_ro;
  end if;
end $$;

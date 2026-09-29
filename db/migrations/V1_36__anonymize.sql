do $$ begin
  if not '${skipAnonymize}' then
    create extension if not exists anon cascade;

    do $permission_grants$ begin
        if not '${skipPermissionGrants}' then
            grant pg_read_all_data to anon_dumper;
            alter role anon_dumper set anon.transparent_dynamic_masking = true;
            security label for anon on role anon_dumper is 'MASKED';
        end if;
    end $permission_grants$;

    perform anon.init();

    SECURITY LABEL FOR anon ON SCHEMA alma IS 'TRUSTED';

    create function alma.transform_geometry(j geometry)
    returns geometry
    volatile
    language sql
    as $func$
    select public.st_multi(public.st_buffer(public.st_setsrid(public.st_centroid(j), 2056), 50))
    $func$;

    security label for anon on column alma.vflz.vflz_strasse is 'MASKED WITH VALUE ''Musterstrasse'' ';
    security label for anon on column alma.vflz.bezeichnung is 'MASKED WITH FUNCTION anon.lorem_ipsum( words := 2 )';
    security label for anon on column alma.vflz.message is 'MASKED WITH FUNCTION anon.lorem_ipsum( words := 4 )';

    security label for anon on column alma.vflgeo.wkb_geometry is 'MASKED WITH FUNCTION alma.transform_geometry(wkb_geometry)';

    security label for anon on column alma.intb.intb_firma_name is 'MASKED WITH FUNCTION anon.fake_company()';
    security label for anon on column alma.intb.intb_firma_strasse is 'MASKED WITH VALUE ''Musterstrasse 10'' ';
    security label for anon on column alma.intb.intb_firma_plz is 'MASKED WITH FUNCTION anon.fake_postcode()';
    security label for anon on column alma.intb.intb_firma_ort is 'MASKED WITH FUNCTION anon.fake_city()';

    security label for anon on column alma.bem.bem is 'MASKED WITH FUNCTION anon.lorem_ipsum( paragraphs := 1 )';

    security label for anon on column alma.subj.name is 'MASKED WITH FUNCTION anon.ternary(
        nullif(name, '''') is null,
        null,
        anon.fake_last_name()
    )';
    security label for anon on column alma.subj.vorname is 'MASKED WITH FUNCTION anon.ternary(
        nullif(vorname, '''') is null,
        null,
        anon.fake_first_name()
    )';
    security label for anon on column alma.subj.taetigkeit is 'MASKED WITH FUNCTION anon.ternary(
        nullif(taetigkeit, '''') is null,
        null,
        anon.fake_company()
    )';
    security label for anon on column alma.subj.kuerzel is 'MASKED WITH VALUE NULL';
    security label for anon on column alma.subj.ort is 'MASKED WITH FUNCTION anon.fake_city()';
    security label for anon on column alma.subj.postleitzahl is 'MASKED WITH FUNCTION anon.fake_postcode()';
    security label for anon on column alma.subj.strasse is 'MASKED WITH VALUE ''Musterstrasse 10''';

    security label for anon on column alma.wf_node.note is 'MASKED WITH FUNCTION anon.ternary(
        nullif(note, '''') is null,
        null, anon.lorem_ipsum( paragraphs := 1 )
    )';
  end if;
end $$;

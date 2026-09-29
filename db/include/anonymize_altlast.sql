create extension anon cascade;

select anon.init();

SECURITY LABEL FOR anon ON SCHEMA import_altlast IS 'TRUSTED';

create function import_altlast.transform_geometry(j geometry)
returns geometry
volatile
language sql
as $func$
select public.st_multi(public.st_buffer(public.st_setsrid(public.st_centroid(j), 2056), 50))
$func$;

security label for anon on column altlast.vflz.vflz_strasse is 'MASKED WITH VALUE ''Musterstrasse'' ';
security label for anon on column altlast.vflz.vflz_hausnr is 'MASKED WITH FUNCTION anon.random_int_between(1, 12)';
security label for anon on column altlast.vflz.bezeichnung is 'MASKED WITH FUNCTION anon.lorem_ipsum( words := 2 )';

security label for anon on column altlast.vflgeo.wkb_geometry is 'MASKED WITH FUNCTION import_altlast.transform_geometry(wkb_geometry)';

security label for anon on column altlast.intb.intb_firma_name is 'MASKED WITH FUNCTION anon.fake_company()';
security label for anon on column altlast.intb.intb_firma_strasse is 'MASKED WITH VALUE ''Musterstrasse 10'' ';
security label for anon on column altlast.intb.intb_firma_plz is 'MASKED WITH FUNCTION anon.fake_postcode()';
security label for anon on column altlast.intb.intb_firma_ort is 'MASKED WITH FUNCTION anon.fake_city()';

security label for anon on column altlast_hist.snapshot.reason is 'MASKED WITH FUNCTION anon.lorem_ipsum( words := 4 )';

-- Only use anon.lorem_ipsum with paragraphs, other modes (words, sentences) are very slow.
security label for anon on column altlast.bem.bem is 'MASKED WITH FUNCTION anon.lorem_ipsum( paragraphs := 1 )';

-- Create user for creating anonymized dumps
create role dump_anon login password 'dump_anon';
grant pg_read_all_data to dump_anon;
alter role dump_anon set anon.transparent_dynamic_masking = true;
security label for anon on role dump_anon is 'MASKED';

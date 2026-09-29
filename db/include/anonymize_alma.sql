-- Create user for creating anonymized dumps
create role dump_anon login password 'dump_anon';
grant pg_read_all_data to dump_anon;
alter role dump_anon set anon.transparent_dynamic_masking = true;
security label for anon on role dump_anon is 'MASKED';

\getenv anon_password POSTGRES_PASSWORD_ANON
\getenv mapserver_password POSTGRES_PASSWORD_MAPSERVER

create role anon_dumper login password :'anon_password';
create role mapserver login password :'mapserver_password';

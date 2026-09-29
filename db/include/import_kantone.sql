create temporary table kantone_import (
    ktnr integer,
    gdekt text,
    gdektna text
);

\copy kantone_import from '/include/kantone.csv' with delimiter ',' csv header;

delete from alma._kantone;

insert into alma._kantone (ktnr, gdekt, gdektna)
select ktnr, gdekt, gdektna from kantone_import;

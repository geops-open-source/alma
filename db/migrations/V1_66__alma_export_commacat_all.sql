create or replace function alma_export.commacat(acc text, instr text) returns text
    language plpgsql
as
$$
begin
    if instr is null or instr = '' then
        return coalesce(acc, '');
    elsif acc is null or acc = '' then
        return instr;
    else
        return acc || ', ' || instr;
    end if;
end;
$$;

comment on function alma_export.commacat is 'Verkettung von Werten mit Komma getrennt.';

do
$$
begin
    if to_regprocedure('alma_export.commacat_all(text)') is null then
        execute
        $agg$
            create aggregate alma_export.commacat_all(text) (
                sfunc = alma_export.commacat,
                stype = text,
                initcond = ''
            )
        $agg$;
    end if;
end;
$$;
drop function if exists alma.msgid_code(int4, varchar);

create or replace function alma.msgid_code(c_cli_id integer, code character varying)
 returns text
 language plpgsql
 stable
as $function$
-- example calls:
-- select alma.msgid_code(15, 'test'); -> code:15:test
-- select alma.msgid_code(null, 'test'); -> code::test
-- select alma.msgid_code(15, null); -> null
-- select alma.msgid_code(null, null); -> null
--
-- note that c_cli_id should never be null if code is not null. this function only handles this case to prevent complete failures on invalid data.
declare
	res text;
  begin
	res := 'code:';
	if c_cli_id is not null then
		res := res || c_cli_id;
	end if;
	res := res || ':' || code;
	return res;
  end;
$function$
;

comment on function alma.msgid_code is 'Zusammenführen der Codeparameter für den String zur Übersetzung';


drop function if exists alma.translate_code(text, text);

create or replace function alma.translate_code(message_identifier text, target_language text)
 returns text
 language plpgsql
 stable
as $function$
declare 
        qry text;
begin   
        select msgstr
        from alma.translations t
        where t.locale=target_language and t.msgid=message_identifier into qry;
        if qry is null then
                qry := message_identifier;
        end if;
    return qry;
end
$function$
;

comment on function alma.translate_code is 'Übersetzten des Codestrings in Klartext';


drop function if exists alma.bestscalefactor(geometry, float8, float8);

create or replace function alma.bestscalefactor(geom geometry, targetwidth_cm double precision, targetheight_cm double precision)
 returns integer
 language plpgsql
as $function$
declare
	ex_height double precision; -- height of the geom in projected units
	ex_width double precision; -- width of the geom in projected units
	scalefactors integer[]; -- possible scale factors
	this_sf double precision;
	w_relation double precision; -- width relation of geom and targetwidth_cm
	h_relation double precision; -- height relation of geom and targetheight_cm
	factor integer;
	s_ex double precision;
	t_cm double precision;
	i integer;
begin
    -- get the height and width of the geometry and use a default value if the size is to minimal
    -- like for example when the input geometry is a point
    select st_distance(
        st_makepoint(st_xmin(geom),st_ymin(geom))::geometry,
        st_makepoint(st_xmin(geom),st_ymax(geom))::geometry)
        into ex_height;
    if ex_height < 10 then
        ex_height := 30;
    end if;

    select st_distance(
        st_makepoint(st_xmin(geom),st_ymin(geom))::geometry,
        st_makepoint(st_xmax(geom),st_ymin(geom))::geometry)
        into ex_width;
    if ex_width < 10 then
        ex_width := 30;
    end if;

    -- legal scalefactors. this function will attempt to zoom to the closesd factor
	scalefactors := array[  100,
                            250,
                            500,
                            1000,
                            1500,
                            2000,
                            2500,
                            5000,
                            7500,
                            10000,
                            15000,
                            20000,
                            25000,
                            50000,
                            75000,
                            100000];
	factor := null;

	w_relation := ex_width/(targetwidth_cm*100.0);
	h_relation := ex_height/(targetheight_cm*100.0);

	if w_relation>h_relation then --scale by width
		s_ex := ex_width;
		t_cm := targetwidth_cm;
	else --scale by height
		s_ex := ex_height;
		t_cm := targetheight_cm;
	end if;

	for i in select generate_series(array_lower(scalefactors,1),array_upper(scalefactors,1)) loop
		this_sf := scalefactors[i]::double precision;

		if ((this_sf*(t_cm/100.0))/s_ex)>1.0  then
			if i=1 then
				factor := scalefactors[1]::integer;
			else
				factor := scalefactors[i]::integer;
			end if;
			exit;
		end if;

	end loop;

	return factor;
end
$function$
;

comment on function alma.bestscalefactor is 'Berechnung der Skala für WMS/WFS Abfragen';


drop function if exists alma.scaleextent2(geometry, float8, float8, int4);

create or replace function alma.scaleextent2(geom geometry, targetwidth_cm double precision, targetheight_cm double precision, scalefactor integer)
 returns geometry
 language plpgsql
as $function$
declare
	m_x double precision; -- multiplier in x direction for scaling
	m_y double precision; -- multiplier in y direction for scaling
	gx box2d;
	gy box2d;
	exnt geometry;
begin
	m_x := (scalefactor*(targetwidth_cm/100.0)/2);
	m_y := (scalefactor*(targetheight_cm/100.0)/2);

	gx := st_expand(st_centroid(geom),m_x)::box2d;
	gy := st_expand(st_centroid(geom),m_y)::box2d;

	exnt := st_setsrid(st_makebox2d(st_makepoint(st_xmin(gx),st_ymin(gy),0),st_makepoint(st_xmax(gx),st_ymax(gy),0))::geometry,st_srid(geom));

	return exnt;
end
$function$
;

comment on function alma.scaleextent2 is 'Berechnung des Ausschnitts für WMS/WFS Abfragen';


drop function if exists alma.scaleextent(geometry, float8, float8);

create or replace function alma.scaleextent(geom geometry, targetwidth_cm double precision, targetheight_cm double precision)
 returns geometry
 language plpgsql
as $function$
declare
	exnt geometry;
begin

	exnt := alma.scaleextent2(geom, targetwidth_cm,targetheight_cm, alma.bestscalefactor(geom, targetwidth_cm ,targetheight_cm));
	return exnt;
end
$function$
;

comment on function alma.scaleextent is 'Berechnung des Ausschnitts für WMS/WFS Abfragen';


drop function if exists alma.queryextent(geometry, float8, float8);

create function alma.queryextent(geom public.geometry) returns text
    language plpgsql
    as $$
declare 
	qry text;
begin
    select translate(translate((st_extent(geom)::box2d)::text,'box()',''),' ',',') into qry;
    return qry;
end
$$;

comment on function alma.queryextent is 'Abfrage des Ausschnitts für WMS/WFS Abfragen';
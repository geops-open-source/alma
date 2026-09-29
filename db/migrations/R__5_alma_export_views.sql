drop view if exists alma_export.geoportal_ne_v;

create view alma_export.geoportal_ne_v
as with lang as (
         select 'fr'::text as lang
        )
 select v.vflz_id,
    v.vflz_combined_id_kt as staonr,
    v.bezeichnung as staobezeichnung,
    v.dat_rechtskraft as ersteintrag,
    alma.translate_code(alma.msgid_code(v.h_vflz_vftyp, v.c_vflz_vftyp), lang.lang) as staotyp,
    v.h_gem_id as gemeinde_bfs,
    h_gem.gemeinde,
        case
            when st_geometrytype(vflgeo.wkb_geometry) = 'ST_Point'::text then st_buffer(vflgeo.wkb_geometry, 10::double precision)
            else vflgeo.wkb_geometry
        end as wkb_geometry,
    betrieb_props.betrieb_branchen,
    betrieb_props.betrieb_zeitraum,
    ablag_props.ablag_zeitraum,
    ablag_props.ablag_gesamtvol,
    unfall_props.unfall_zeitpunkt,
    alma.translate_code(alma.msgid_code(bere.h_bere_res_abwbewe, bere.c_bere_res_abwbewe), lang.lang) as beurteilung,
    umweltbereiche.festgestellte_einwirkungen,
    to_char(vip.dat_latest_published::timestamp with time zone, 'DD.MM.YYYY'::text) as publikation_datum,
    parzellen.parzellen,
    v.vflz_flurname,
    betrieb_props.betrieb_strassen as vflz_strasse,
    v.vflz_postleitzahl,
    v.vflz_ort,
    st_x(v.zentroid) as x_koordinate,
    st_y(v.zentroid) as y_koordinate,
    v.publizieren,
    massnahmen.massnahmen,
    bem_begr.bem as begruend_beurt,
    umweltbereiche.bem as einwirkungen_bem,
    massnahmen.bem as massnahmen_bem,
    alma.translate_code(alma.msgid_code(bere.h_bere_prio_untersuch, bere.c_bere_prio_untersuch), lang.lang) as prio_untersuch
   from alma.vflz v
     join lang on true
     join alma.vflnr on vflnr.vflz_id = v.vflz_id and vflnr.aktiv = true
     join alma.vflz_is_published_v vip on vip.vflz_id = v.vflz_id and vip.is_latest_published
     join alma.bere bere on bere.vflz_id = v.vflz_id
     join alma.cod_kbsinfo ckbs on bere.h_bere_res_abwbewe = ckbs.h_bere_res_abwbewe and bere.c_bere_res_abwbewe = ckbs.c_bere_res_abwbewe and ckbs.belastet
     join alma.vflgeo on v.vflz_id = vflgeo.vflz_id
     left join alma.h_gem on h_gem.h_gem_id = v.h_gem_id
     left join ( select intb.vflz_id,
        array_to_string(array_agg(alma.translate_code(alma.msgid_code(intb.h_intb_bran, intb.c_intb_bran), lang_1.lang)), ''::text) as betrieb_branchen,
        array_to_string(array_agg(distinct alma.translate_code(intb.intb_firma_strasse::text, lang_1.lang)), ''::text) as betrieb_strassen,
        ( coalesce(to_char(min(intb.intb_vonbetrieb)::timestamp with time zone, 'DD.MM.YYYY'::text),
            alma.translate_code('zeitraum.unknown'::text, lang_1.lang)) || ' '::text ||
            alma.translate_code('zeitraum.bis'::text, lang_1.lang) || ' '::text ||
            case 
                when bool_or(intb.zeitraum_bisheute) then alma.translate_code('zeitraum.heute'::text, lang_1.lang)
                else coalesce(to_char(max(intb.intb_bisbetrieb)::timestamp with time zone, 'DD.MM.YYYY'::text),
                              alma.translate_code('zeitraum.unknown'::text, lang_1.lang))
            end
        ) as betrieb_zeitraum
            from lang lang_1, alma.intb
            group by intb.vflz_id, lang_1.lang
        ) betrieb_props on betrieb_props.vflz_id = v.vflz_id and v.c_vflz_vftyp::text = '02'::text
     left join ( select inta.vflz_id,
        (coalesce(to_char(min(inta.inta_ablag_von)::timestamp with time zone, 'DD.MM.YYYY'::text),
                     alma.translate_code('zeitraum.unknown'::text, lang_1.lang)) || ' '::text ||
            alma.translate_code('zeitraum.bis'::text, lang_1.lang) || ' '::text ||
            case
                when bool_or(inta.zeitraum_bisheute) then alma.translate_code('zeitraum.heute'::text, lang_1.lang)
                else coalesce(to_char(max(inta.inta_ablag_bis)::timestamp with time zone, 'DD.MM.YYYY'::text),
                              alma.translate_code('zeitraum.unknown'::text, lang_1.lang))
            end
        ) as ablag_zeitraum,
        sum(inta.inta_vol_kompartiment) as ablag_gesamtvol,
        array_to_string(array_agg(alma.translate_code(alma.msgid_code(kksk.h_kksk_stoffkl, kksk.c_kksk_stoffkl), lang_1.lang) ||
        coalesce(': '::text || alma.translate_code(alma.msgid_code(kksg.h_kksg_stoffgrp, kksg.c_kksg_stoffgrp), lang_1.lang), ''::text)), '
'::text) as ablag_stoffe
            from alma.inta
            join lang lang_1 on true
            left join alma.kksk on kksk.inta_id = inta.inta_id
            left join  alma.kksg on kksk.kksk_id = kksg.kksk_id
            group by inta.vflz_id, lang_1.lang
        ) ablag_props on ablag_props.vflz_id = v.vflz_id and v.c_vflz_vftyp::text = '01'::text
     left join ( select intu.vflz_id,
            alma_export.commacat_all(
                case
                    when intu.zeitraum_jahr then to_char(intu.intu_unfallvon::timestamp with time zone, 'yyyy'::text)
                    else to_char(intu.intu_unfallvon::timestamp with time zone, 'DD.MM.YYYY'::text)
                end) as unfall_zeitpunkt,
            array_to_string(array_agg(alma.translate_code(alma.msgid_code(inum.h_inum_stoffe, inum.c_inum_stoffe), lang_1.lang) || coalesce(((((': '::text || alma.translate_code('fields.Unfallstoff.stoffmng'::text, lang_1.lang)) || ' '::text) || nullif(inum.inum_stoffmng, 0::double precision)::text) || ' '::text) || alma.translate_code('litre'::text, lang_1.lang), ''::text)), '
'::text) as unfall_stoffe
           from alma.intu
             join lang lang_1 on true
             left join alma.inum on inum.intu_id = intu.intu_id
          group by intu.vflz_id, lang_1.lang) unfall_props on unfall_props.vflz_id = v.vflz_id and v.c_vflz_vftyp::text = '03'::text
     left join ( select vfus.vflz_id,
            array_to_string(array_agg(alma.translate_code(alma.msgid_code(vfus.h_vfus_art_schaden, vfus.c_vfus_art_schaden), lang_1.lang)), '
'::text) as gefaehrdete_umweltbereiche,
            array_to_string(array_agg(alma.translate_code(alma.msgid_code(vfus.h_vfus_schaeden, vfus.c_vfus_schaeden), lang_1.lang)), '
'::text) as festgestellte_einwirkungen,
            array_to_string(array_agg(bem.bem), '
'::text) as bem
           from alma.vfus
             join alma.bem on vfus.vfus_id = bem.key_value
             join lang lang_1 on true
          group by vfus.vflz_id, lang_1.lang) umweltbereiche on umweltbereiche.vflz_id = v.vflz_id
     left join ( select bem.key_value,
            bem.bem
           from alma.bem
             left join alma.bemgrp on bemgrp.bemgrp_id = bem.bemgrp_id
          where bemgrp.bemgrp::text = 'bere_begr_abwbewe'::text) bem_begr on bem_begr.key_value = v.vflz_id
     left join ( select mass.vflz_id,
            array_to_string(array_agg(alma.translate_code(alma.msgid_code(mass.h_massnahme, mass.c_massnahme), lang_1.lang)), '
'::text) as massnahmen,
            array_to_string(array_agg(bem.bem), '
'::text) as bem
           from alma.mass
             join alma.bem on mass.mass_id = bem.key_value and bem.bemgrp_id = 15
             join lang lang_1 on true
          group by mass.vflz_id, lang_1.lang) massnahmen on massnahmen.vflz_id = v.vflz_id
     left join ( select
        x.vflz_id,array_to_string(array_agg(x.gb_nummer), ', '::text) as parzellen
           from 
            (select distinct
                bet.vflz_id,
                grun.gb_nummer
            from alma.bet
            join alma.bet_art
                on bet.bet_id = bet_art.bet_id
            and bet_art.is_current
            join alma.grun
                on bet_art.grun_id = grun.grun_id
            where bet.is_current
            and grun.gb_nummer is not null
        ) x
        group by
            x.vflz_id) parzellen on parzellen.vflz_id = v.vflz_id
  where vflnr.aktiv
  order by v.vflz_combined_id_kt;

comment on view alma_export.geoportal_ne_v is 'Export Data für Geoportal Kanton NE';

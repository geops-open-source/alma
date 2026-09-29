delete from alma_export.report_report_sql_query;
delete from alma_export.report_sql_query;
delete from alma_export.report_param;
delete from alma_export.report;

insert into
alma_export.report (report_id, title, template, style, context, is_active)
values (1, 'report.title.katasterauszug', 'kataster_auszug.html.jinja2', 'styles.css', 'STANDORT', true);

insert into
alma_export.report_param (param_id, report_id, name, type)
values (1, 1, 'vflz_id', 'INTEGER');

insert into
alma_export.report_param (param_id, report_id, name, type)
values (4, 1, 'date', 'DATE');

insert into
alma_export.report_param (param_id, report_id, name, type)
values (7, 1, 'language', 'TEXT');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (1,'grunddaten', 'select * from alma_export.report_grunddaten_v where vflz_id=:vflz_id  and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (2, 'umweltdaten', 'select * from alma_export.report_umweltdaten_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (3, 'inta', 'select * from alma_export.report_inta_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (4, 'kksk', 'select * from alma_export.report_kksk_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (5, 'intb', 'select * from alma_export.report_intb_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (6, 'intu', 'select * from alma_export.report_intu_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (7, 'inum', 'select * from alma_export.report_inum_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (8, 'vfus', 'select * from alma_export.report_vfus_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (9, 'veen','select * from alma_export.report_veen_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (10, 'sani', 'select * from alma_export.report_saniziel_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (11, 'massnahme', 'select * from alma_export.report_massnahme_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (12, 'nubo', 'select * from alma_export.report_nubo_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (13, 'workflows', 'select * from alma_export.report_workflows_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (14, 'sanierbere', 'select * from alma_export.report_sanierbere_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (15, 'bemerkungen', 'select * from alma_export.report_bemerkungen_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (16, 'beteiligte', 'select * from alma_export.report_bet_v where vflz_id=:vflz_id and language=:language;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query)
values (17, 'parzellen', 'select * from alma_export.report_parcels_v where vflz_id=:vflz_id;');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query, is_translation_query)
values (18, 'translations', 'select * from alma.translations where locale=:language;', true);

insert into
alma_export.report_report_sql_query (report_id, report_sql_query_id)
values
    (1, 1),
    (1, 2),
    (1, 3),
    (1, 4),
    (1, 5),
    (1, 6),
    (1, 7),
    (1, 8),
    (1, 9),
    (1, 10),
    (1, 11),
    (1, 12),
    (1, 13),
    (1, 14),
    (1, 15),
    (1, 16),
    (1, 17),
    (1, 18)
    ;

insert into
alma_export.report (report_id, title, template, style, context, is_active)
values (2, 'report.title.inhaberorientierung', 'inhaberorientierung.html.jinja2', 'styles.css', 'STANDORT', true);

insert into
alma_export.report_param (param_id, report_id, name, type)
values (2, 2, 'vflz_id', 'INTEGER');

insert into
alma_export.report_param (param_id, report_id, name, type)
values (5, 2, 'date', 'DATE');

insert into
alma_export.report_param (param_id, report_id, name, type)
values (8, 2, 'language', 'TEXT');

insert into
alma_export.report_report_sql_query (report_id, report_sql_query_id)
values
    (2, 1),
    (2, 2),
    (2, 3),
    (2, 4),
    (2, 5),
    (2, 6),
    (2, 7),
    (2, 8),
    (2, 9),
    (2, 10),
    (2, 11),
    (2, 12),
    (2, 13),
    (2, 14),
    (2, 15),
    (2, 16),
    (2, 17),
    (2, 18)
    ;

insert into
alma_export.report (report_id, title, template, style, context, is_active)
values (3, 'report.title.intern', 'intern.html.jinja2', 'styles.css', 'STANDORT', true);

insert into
alma_export.report_param (param_id, report_id, name, type)
values (3, 3, 'vflz_id', 'INTEGER');

insert into
alma_export.report_param (param_id, report_id, name, type)
values (6, 3, 'date', 'DATE');

insert into
alma_export.report_param (param_id, report_id, name, type)
values (9, 3, 'language', 'TEXT');

insert into
alma_export.report_report_sql_query (report_id, report_sql_query_id)
values
    (3, 1),
    (3, 2),
    (3, 3),
    (3, 4),
    (3, 5),
    (3, 6),
    (3, 7),
    (3, 8),
    (3, 9),
    (3, 10),
    (3, 11),
    (3, 12),
    (3, 13),
    (3, 14),
    (3, 15),
    (3, 16),
    (3, 17),
    (3, 18)
    ;


insert into
alma_export.report (report_id, title, template, style, context, export_format, is_active)
values (4, 'report.title.jahresbericht', 'jahresbericht.xlsx', '', 'DASHBOARD',  'XLSX', true);

insert into
alma_export.report_sql_query (report_sql_query_id, name, query, worksheet_name)
values (19, 'Standort-Rohdaten', 'with latest_vflz_id as (
    select
        max(vflz_id) as max_vflz_id
    from alma.vflz
    where vflz_created_date <= :date
    group by vfl_id, obje_id
),
current_vfl as (
    select vfl_id
    from alma.vflz_current_v
    group by vfl_id
    having BOOL_OR(is_current) = true
)
SELECT vflz.vflz_id, vflz.vflz_combined_id_kt, vflnr.c_org_kuerzel, 
    bere.c_bere_res_abwbewe, t_bere_res_abwbewe.msgstr AS bere_res_abwbewe,
    cod_kbsinfo.c_bewe_gruppe, t_bewe_gruppe.msgstr AS bewe_gruppe,
    vflz.c_vflz_bearbstand, t_vflz_bearbstand.msgstr AS vflz_bearbstand,
    vflz.c_vflz_unterstand, t_vflz_unterstand.msgstr AS vflz_unterstand,
    vflz.c_vflz_vftyp, t_vflz_vftyp.msgstr AS vflz_vftyp
FROM alma.vflz 
JOIN latest_vflz_id lvi ON lvi.max_vflz_id = vflz.vflz_id
JOIN current_vfl cv ON cv.vfl_id = vflz.vfl_id
LEFT JOIN alma.bere USING (vflz_id)
LEFT JOIN alma.cod_kbsinfo USING (c_bere_res_abwbewe)
LEFT JOIN alma.translations t_bere_res_abwbewe ON t_bere_res_abwbewe.msgid = ''code:''||bere.h_bere_res_abwbewe||'':''||bere.c_bere_res_abwbewe AND t_bere_res_abwbewe.locale = ''de''
LEFT JOIN alma.translations t_bewe_gruppe ON t_bewe_gruppe.msgid = ''code:''||cod_kbsinfo.h_bewe_gruppe||'':''||cod_kbsinfo.c_bewe_gruppe AND t_bewe_gruppe.locale = ''de''
LEFT JOIN alma.translations t_vflz_bearbstand ON t_vflz_bearbstand.msgid = ''code:''||vflz.h_vflz_bearbstand||'':''||vflz.c_vflz_bearbstand AND t_vflz_bearbstand.locale = ''de''
LEFT JOIN alma.translations t_vflz_unterstand ON t_vflz_unterstand.msgid = ''code:''||vflz.h_vflz_unterstand||'':''||vflz.c_vflz_unterstand AND t_vflz_unterstand.locale = ''de''
LEFT JOIN alma.translations t_vflz_vftyp ON t_vflz_vftyp.msgid = ''code:''||vflz.h_vflz_vftyp||'':''||vflz.c_vflz_vftyp AND t_vflz_vftyp.locale = ''de''
LEFT JOIN alma.vflnr USING (vflz_id);', 'Standort-Rohdaten');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query, worksheet_name)
values (20, 'Geschäft-Rohdaten',
'SELECT 
	vflz.vflz_combined_id_kt AS "Standort", 
	COALESCE(t_parent_wf_node.msgstr, parent_wf_node.title) AS "Geschäft", 
	COALESCE(t_wf_node.msgstr, wf_node.title) AS "Aufgabe", 
	wf_node.status AS "Status", 
	TO_CHAR(COALESCE(wf_node.updated_at, wf_node.finished_at, wf_node.started_at), ''YYYY-MM-DD'') AS "Datum", 
	subj.vorname||'' ''||subj.name AS "Sachbearbeitung"
FROM alma.vflz
LEFT JOIN alma.wf_node ON wf_node.entity_id = vflz.vflz_id
LEFT JOIN alma.wf_node parent_wf_node ON parent_wf_node.wf_node_id = wf_node.parent_id
LEFT JOIN alma.bet_task ON bet_task.wf_node_id = wf_node.wf_node_id AND bet_task.c_bez_art = ''sachbearbeitung''
LEFT JOIN alma.subj ON subj.subj_id = bet_task.subj_id
LEFT JOIN alma.translations t_wf_node ON t_wf_node.msgid = wf_node.title AND t_wf_node.locale = ''de''
LEFT JOIN alma.translations t_parent_wf_node ON t_parent_wf_node.msgid = parent_wf_node.title AND t_parent_wf_node.locale = ''de''
WHERE wf_node.type = ''task'' AND COALESCE(wf_node.updated_at, wf_node.finished_at, wf_node.started_at) BETWEEN :date - INTERVAL ''12 months'' AND :date;', 'Geschäft-Rohdaten');

insert into
alma_export.report_sql_query (report_sql_query_id, name, query, worksheet_name)
values (21, 'Stichtag-Rohdaten', 'select (:date)::date as stichtag, (:date - INTERVAL ''12 months'')::date as zeitraum;', 'Stichtag-Rohdaten');


insert into
alma_export.report_sql_query (report_sql_query_id, name, query, worksheet_name)
values (22, 'Jahrestrends-Rohdaten', 'SELECT id, jahr, anzahl, kategorie FROM alma_export.jahrestrends;', 'Jahrestrends-Rohdaten');

insert into
alma_export.report_report_sql_query (report_id, report_sql_query_id)
values
    (4, 19),
    (4, 20),
    (4, 21),
    (4, 22)
;

insert into
alma_export.report_param (param_id, report_id, name, type)
values (10, 4, 'date', 'DATE');

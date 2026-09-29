alter table alma_export.report_sql_query add column is_translation_query boolean default false;

comment on column alma_export.report_sql_query.is_translation_query is 'Indicates if the report query is a translation query';

alter table alma_export.report_sql_query add column worksheet_name text;

comment on column alma_export.report_sql_query.worksheet_name is 'Name of the worksheet in the Excel file where the query results will be placed.'; 

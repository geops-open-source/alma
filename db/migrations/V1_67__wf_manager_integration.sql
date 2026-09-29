alter table alma.wf_node rename column erfassungs_datum to created_at;
alter table alma.wf_node rename column erfasser to created_by;
alter table alma.wf_node rename column mutations_datum to updated_at;
alter table alma.wf_node rename column mutierer to updated_by;

drop view if exists alma_export.report_workflows_v cascade;
drop view if exists alma_export.report_berichte_be_v cascade;
drop view if exists alma_export.report_workflows_be_v cascade;

alter table alma.wf_node alter column started_at type timestamp without time zone using started_at::timestamp;

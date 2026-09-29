drop view if exists alma_export.report_workflows_v cascade;

alter table alma.wf_node alter column started_at type date using started_at::date;

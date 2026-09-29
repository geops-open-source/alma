alter table alma.wf_node add url text;

comment on column alma.wf_node.url is 'Optionale URL fuer Dokument/Notiz-Knoten';

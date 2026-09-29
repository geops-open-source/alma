alter table alma.wf_node
drop constraint wf_node_next_node_id_fkey;

alter table alma.wf_node
add constraint wf_node_next_node_id_fkey
foreign key (next_node_id)
references alma.wf_node (wf_node_id)
on delete set null;

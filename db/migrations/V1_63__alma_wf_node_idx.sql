create index ix_wf_node_next_node_id on alma.wf_node using btree(next_node_id);
create index ix_wf_node_parent_id on alma.wf_node using btree(parent_id);

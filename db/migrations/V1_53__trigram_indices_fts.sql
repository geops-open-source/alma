create extension if not exists pg_trgm;

-- add for columns used by FTS_FIELDS
create index ix_trgm_vflz_bezeichnung on alma.vflz using gin (bezeichnung gin_trgm_ops);
create index ix_trgm_vflz_strasse on alma.vflz using gin (vflz_strasse gin_trgm_ops);
create index ix_trgm_vflz_ort on alma.vflz using gin (vflz_ort gin_trgm_ops);

create index ix_trgm_intb_firma_name on alma.intb using gin (intb_firma_name gin_trgm_ops);
create index ix_trgm_wf_node_note on alma.wf_node using gin (note gin_trgm_ops);
create index ix_trgm_intu_name on alma.intu using gin (intu_name gin_trgm_ops);
create index ix_trgm_intk_name on alma.intk using gin (name gin_trgm_ops);
create index ix_trgm_bem on alma.bem using gin (bem gin_trgm_ops);
create index ix_trgm_subj_name_vorname_taetigkeit_strasse_ort on alma.subj using gin ((name || ' ' || vorname || ', ' || taetigkeit || ', ' || strasse || ', ' || ort) gin_trgm_ops);

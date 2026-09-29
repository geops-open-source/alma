create index ix_to_tsvector_de_vflz_bezeichnung on alma.vflz using gin (to_tsvector('german', bezeichnung));
create index ix_to_tsvector_fr_vflz_bezeichnung on alma.vflz using gin (to_tsvector('french', bezeichnung));
create index ix_to_tsvector_it_vflz_bezeichnung on alma.vflz using gin (to_tsvector('italian', bezeichnung));

create index ix_to_tsvector_de_vflz_strasse on alma.vflz using gin (to_tsvector('german', vflz_strasse));
create index ix_to_tsvector_fr_vflz_strasse on alma.vflz using gin (to_tsvector('french', vflz_strasse));
create index ix_to_tsvector_it_vflz_strasse on alma.vflz using gin (to_tsvector('italian', vflz_strasse));

create index ix_to_tsvector_de_vflz_ort on alma.vflz using gin (to_tsvector('german', vflz_ort));
create index ix_to_tsvector_fr_vflz_ort on alma.vflz using gin (to_tsvector('french', vflz_ort));
create index ix_to_tsvector_it_vflz_ort on alma.vflz using gin (to_tsvector('italian', vflz_ort));

create index ix_to_tsvector_de_intb_firma_name on alma.intb using gin (to_tsvector('german', intb_firma_name));
create index ix_to_tsvector_fr_intb_firma_name on alma.intb using gin (to_tsvector('french', intb_firma_name));
create index ix_to_tsvector_it_intb_firma_name on alma.intb using gin (to_tsvector('italian', intb_firma_name));

create index ix_to_tsvector_de_wf_node_note on alma.wf_node using gin (to_tsvector('german', note));
create index ix_to_tsvector_fr_wf_node_note on alma.wf_node using gin (to_tsvector('french', note));
create index ix_to_tsvector_it_wf_node_note on alma.wf_node using gin (to_tsvector('italian', note));

create index ix_to_tsvector_de_intu_name on alma.intu using gin (to_tsvector('german', intu_name));
create index ix_to_tsvector_fr_intu_name on alma.intu using gin (to_tsvector('french', intu_name));
create index ix_to_tsvector_it_intu_name on alma.intu using gin (to_tsvector('italian', intu_name));

create index ix_to_tsvector_de_intk_name on alma.intk using gin (to_tsvector('german', name));
create index ix_to_tsvector_fr_intk_name on alma.intk using gin (to_tsvector('french', name));
create index ix_to_tsvector_it_intk_name on alma.intk using gin (to_tsvector('italian', name));

create index ix_to_tsvector_de_bem on alma.bem using gin (to_tsvector('german', bem));
create index ix_to_tsvector_fr_bem on alma.bem using gin (to_tsvector('french', bem));
create index ix_to_tsvector_it_bem on alma.bem using gin (to_tsvector('italian', bem));

create index ix_to_tsvector_de_subj_name_vorname_taetigkeit_strasse_ort on alma.subj using gin (to_tsvector('german', name || ' ' || vorname || ', ' || taetigkeit || ', ' || strasse || ', ' || ort));
create index ix_to_tsvector_fr_subj_name_vorname_taetigkeit_strasse_ort on alma.subj using gin (to_tsvector('french', name || ' ' || vorname || ', ' || taetigkeit || ', ' || strasse || ', ' || ort));
create index ix_to_tsvector_it_subj_name_vorname_taetigkeit_strasse_ort on alma.subj using gin (to_tsvector('italian', name || ' ' || vorname || ', ' || taetigkeit || ', ' || strasse || ', ' || ort));

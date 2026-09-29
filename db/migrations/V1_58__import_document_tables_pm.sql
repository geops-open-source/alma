CREATE TABLE wf_workflow.app_document (
	app_doc_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	app_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	del_index int4 DEFAULT 0 NOT NULL,
	doc_uid varchar(32) DEFAULT ''::character varying NULL,
	usr_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	app_doc_type varchar(32) DEFAULT ''::character varying NOT NULL,
	app_doc_create_date timestamp DEFAULT now() NULL,
	app_doc_index int4 NOT NULL,
	CONSTRAINT app_document_pkey PRIMARY KEY (app_doc_uid),
	CONSTRAINT fk_app_del FOREIGN KEY (app_uid,del_index) REFERENCES wf_workflow.app_delegation(app_uid,del_index) ON DELETE CASCADE
);
CREATE INDEX fki_app_del ON wf_workflow.app_document USING btree (app_uid, del_index);

CREATE TABLE wf_workflow.input_document (
	inp_doc_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	pro_uid varchar(32) DEFAULT '0'::character varying NOT NULL,
	inp_doc_form_needed varchar(20) DEFAULT 'REAL'::character varying NOT NULL,
	inp_doc_original varchar(20) DEFAULT 'COPY'::character varying NOT NULL,
	inp_doc_published varchar(20) DEFAULT 'PRIVATE'::character varying NOT NULL,
	CONSTRAINT input_document_pkey PRIMARY KEY (inp_doc_uid),
	CONSTRAINT fk_indoc_pro FOREIGN KEY (pro_uid) REFERENCES wf_workflow.process(pro_uid) ON DELETE CASCADE
);
CREATE INDEX fki_indoc_pro ON wf_workflow.input_document USING btree (pro_uid);


CREATE TABLE wf_workflow.output_document (
	out_doc_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	pro_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	out_doc_landscape int4 DEFAULT 0 NOT NULL,
	out_doc_generate varchar(10) DEFAULT 'BOTH'::character varying NOT NULL,
	out_doc_type varchar(32) DEFAULT 'HTML'::character varying NOT NULL,
	out_doc_current_revision int4 DEFAULT 0 NULL,
	out_doc_field_mapping text NULL,
	CONSTRAINT output_document_pkey PRIMARY KEY (out_doc_uid),
	CONSTRAINT fk_outdoc_pro FOREIGN KEY (pro_uid) REFERENCES wf_workflow.process(pro_uid) ON DELETE CASCADE
);
CREATE INDEX fki_outdoc_pro ON wf_workflow.output_document USING btree (pro_uid);

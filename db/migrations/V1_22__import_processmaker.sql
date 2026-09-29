-- Create tables from the processmaker db required for import of Geschäfte.

create schema wf_workflow;
comment on schema wf_workflow is 'Enthält Daten für die Migration der Geschäfte aus ProcessMaker';


-- wf_workflow.process definition

-- Drop table

-- DROP TABLE wf_workflow.process;

CREATE TABLE wf_workflow.process (
	pro_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	pro_parent varchar(32) DEFAULT '0'::character varying NOT NULL,
	pro_time float8 DEFAULT 1::double precision NOT NULL,
	pro_timeunit varchar(20) DEFAULT 'DAYS'::character varying NOT NULL,
	pro_status varchar(20) DEFAULT 'ACTIVE'::character varying NOT NULL,
	pro_type_day varchar(1) DEFAULT '0'::character varying NOT NULL,
	pro_type varchar(20) DEFAULT 'NORMAL'::character varying NOT NULL,
	pro_assignment varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	pro_show_map int4 DEFAULT 1 NOT NULL,
	pro_show_message int4 DEFAULT 1 NOT NULL,
	pro_show_delegate int4 DEFAULT 1 NOT NULL,
	pro_show_dynaform int4 DEFAULT 0 NOT NULL,
	pro_category varchar(48) DEFAULT ''::character varying NOT NULL,
	pro_sub_category varchar(48) DEFAULT ''::character varying NOT NULL,
	pro_industry int4 DEFAULT 1 NOT NULL,
	pro_update_date timestamp NULL,
	pro_create_date timestamp NOT NULL,
	pro_create_user varchar(32) DEFAULT ''::character varying NOT NULL,
	pro_height int4 DEFAULT 5000 NOT NULL,
	pro_width int4 DEFAULT 10000 NOT NULL,
	pro_title_x int4 DEFAULT 0 NOT NULL,
	pro_title_y int4 DEFAULT 6 NOT NULL,
	pro_debug int4 DEFAULT 0 NOT NULL,
	CONSTRAINT process_pkey PRIMARY KEY (pro_uid)
);


-- wf_workflow.task definition

-- Drop table

-- DROP TABLE wf_workflow.task;

CREATE TABLE wf_workflow.task (
	pro_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	tas_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	tas_type varchar(20) DEFAULT 'NORMAL'::character varying NOT NULL,
	tas_duration float8 DEFAULT 0::double precision NOT NULL,
	tas_delay_type varchar(30) DEFAULT ''::character varying NOT NULL,
	tas_temporizer float8 DEFAULT 0::double precision NOT NULL,
	tas_type_day varchar(1) DEFAULT '1'::character varying NOT NULL,
	tas_timeunit varchar(20) DEFAULT 'DAYS'::character varying NOT NULL,
	tas_alert varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	tas_priority_variable varchar(100) DEFAULT ''::character varying NOT NULL,
	tas_assign_type varchar(30) DEFAULT 'BALANCED'::character varying NOT NULL,
	tas_assign_variable varchar(100) DEFAULT '@@SYS_NEXT_USER_TO_BE_ASSIGNED'::character varying NOT NULL,
	tas_assign_location varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	tas_assign_location_adhoc varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	tas_transfer_fly varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	tas_last_assigned varchar(32) DEFAULT '0'::character varying NOT NULL,
	tas_user varchar(32) DEFAULT '0'::character varying NOT NULL,
	tas_can_upload varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	tas_view_upload varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	tas_view_additional_documentation varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	tas_can_cancel varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	tas_owner_app varchar(32) DEFAULT ''::character varying NOT NULL,
	stg_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	tas_can_pause varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	tas_can_send_message varchar(20) DEFAULT 'TRUE'::character varying NOT NULL,
	tas_can_delete_docs varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	tas_self_service varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	tas_start varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	tas_to_last_user varchar(20) DEFAULT 'FALSE'::character varying NOT NULL,
	tas_send_last_email varchar(20) DEFAULT 'TRUE'::character varying NOT NULL,
	tas_derivation varchar(100) DEFAULT 'NORMAL'::character varying NOT NULL,
	tas_posx int4 DEFAULT 0 NOT NULL,
	tas_posy int4 DEFAULT 0 NOT NULL,
	tas_color varchar(32) DEFAULT ''::character varying NOT NULL,
	tas_postpone_date timestamp NULL,
	CONSTRAINT task_pkey PRIMARY KEY (tas_uid),
	CONSTRAINT fd_tas_proc FOREIGN KEY (pro_uid) REFERENCES wf_workflow.process(pro_uid) ON DELETE CASCADE
);
CREATE INDEX fki_fd_tas_proc ON wf_workflow.task USING btree (pro_uid);


-- wf_workflow.app_thread definition

-- Drop table

-- DROP TABLE wf_workflow.app_thread;

CREATE TABLE wf_workflow.app_thread (
	app_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	app_thread_index int4 DEFAULT 0 NOT NULL,
	app_thread_parent int4 DEFAULT 0 NOT NULL,
	app_thread_status varchar(32) DEFAULT 'OPEN'::character varying NOT NULL,
	del_index int4 DEFAULT 0 NOT NULL,
	CONSTRAINT app_thread_pkey PRIMARY KEY (app_uid, app_thread_index)
);


-- wf_workflow.app_delegation definition

-- Drop table

-- DROP TABLE wf_workflow.app_delegation;

CREATE TABLE wf_workflow.app_delegation (
	app_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	del_index int4 DEFAULT 0 NOT NULL,
	del_previous int4 DEFAULT 0 NOT NULL,
	pro_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	tas_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	usr_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	del_type varchar(32) DEFAULT 'NORMAL'::character varying NOT NULL,
	del_thread int4 DEFAULT 0 NOT NULL,
	del_thread_status varchar(32) DEFAULT 'OPEN'::character varying NOT NULL,
	del_priority varchar(32) DEFAULT '3'::character varying NOT NULL,
	del_delegate_date timestamp NULL,
	del_init_date timestamp NULL,
	del_task_due_date timestamp NULL,
	del_finish_date timestamp NULL,
	del_duration float8 DEFAULT 0::double precision NULL,
	del_queue_duration float8 DEFAULT 0::double precision NULL,
	del_delay_duration float8 DEFAULT 0::double precision NULL,
	del_started int4 DEFAULT 0 NULL,
	del_finished int4 DEFAULT 0 NULL,
	del_delayed int4 DEFAULT 0 NULL,
	del_data text DEFAULT ''::text NOT NULL,
	step_position int4 DEFAULT 1 NULL,
	CONSTRAINT app_delegation_pkey PRIMARY KEY (app_uid, del_index),
	CONSTRAINT fk_ad_process FOREIGN KEY (pro_uid) REFERENCES wf_workflow.process(pro_uid) ON DELETE RESTRICT,
	CONSTRAINT fk_ad_task FOREIGN KEY (tas_uid) REFERENCES wf_workflow.task(tas_uid) ON DELETE RESTRICT,
	CONSTRAINT fk_app_thread FOREIGN KEY (app_uid,del_thread) REFERENCES wf_workflow.app_thread(app_uid,app_thread_index) ON DELETE CASCADE
);
CREATE INDEX fki_ad_process ON wf_workflow.app_delegation USING btree (pro_uid);
CREATE INDEX fki_ad_task ON wf_workflow.app_delegation USING btree (tas_uid);
CREATE INDEX fki_ad_user ON wf_workflow.app_delegation USING btree (usr_uid);
CREATE INDEX fki_app_thread ON wf_workflow.app_delegation USING btree (app_uid, del_thread);
CREATE INDEX idx_del_index ON wf_workflow.app_delegation USING btree (del_index);


-- wf_workflow.dynaform definition

-- Drop table

-- DROP TABLE wf_workflow.dynaform;

CREATE TABLE wf_workflow.dynaform (
	dyn_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	pro_uid varchar(32) DEFAULT '0'::character varying NOT NULL,
	dyn_type varchar(20) DEFAULT 'xmlform'::character varying NOT NULL,
	dyn_filename varchar(100) DEFAULT ''::character varying NOT NULL,
	CONSTRAINT dynaform_pkey PRIMARY KEY (dyn_uid),
	CONSTRAINT fk_dyn_pro FOREIGN KEY (pro_uid) REFERENCES wf_workflow.process(pro_uid) ON DELETE CASCADE
);
CREATE INDEX fki_dyn_pro ON wf_workflow.dynaform USING btree (pro_uid);


-- wf_workflow.step definition

-- Drop table

-- DROP TABLE wf_workflow.step;

CREATE TABLE wf_workflow.step (
	step_uid varchar(32) DEFAULT ''::character varying NOT NULL,
	pro_uid varchar(32) DEFAULT '0'::character varying NOT NULL,
	tas_uid varchar(32) DEFAULT '0'::character varying NOT NULL,
	step_type_obj varchar(20) DEFAULT 'DYNAFORM'::character varying NOT NULL,
	step_uid_obj varchar(32) DEFAULT '0'::character varying NOT NULL,
	step_condition text NOT NULL,
	step_position int4 DEFAULT 0 NOT NULL,
	step_mode varchar(10) DEFAULT 'EDIT'::character varying NULL,
	CONSTRAINT step_pkey PRIMARY KEY (step_uid)
);
CREATE INDEX idy_xtep_steop_uid_obj ON wf_workflow.step USING btree (step_uid_obj);


-- wf_workflow."content" definition

-- Drop table

-- DROP TABLE wf_workflow."content";

CREATE TABLE wf_workflow."content" (
	con_category varchar(30) DEFAULT ''::character varying NOT NULL,
	con_parent varchar(32) DEFAULT ''::character varying NOT NULL,
	con_id varchar(100) DEFAULT ''::character varying NOT NULL,
	con_lang varchar(10) DEFAULT ''::character varying NOT NULL,
	con_value text NULL,
	mutations_datum timestamp NULL
);
CREATE INDEX idx_content_lookup ON wf_workflow.content USING btree (con_category, con_id, con_lang);


create table wf_workflow.forms_imported (
    form_id integer not null generated always as identity primary key,
    pm_cache_id integer not null,
    app_uid varchar(32) not null,
    tas_uid varchar(32) not null,
    step_uid varchar(32) not null,
    usr_uid varchar(32) not null,
    dyn_uid varchar(32) not null,
    title text,
    form_config jsonb,
    form_data jsonb
);

comment on table wf_workflow.forms_imported is 'Formulardefinitionen und -Eingaben der Geschäfte, extrahiert aus processmaker db und dynaform XML-Dateien.';




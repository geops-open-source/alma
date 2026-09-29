drop index alma.iq_grun_h_n_bid_gb_nummer_is_current;

create unique index iq_grun_h_gem_id_h_nb_id_gb_nummer_is_current on alma.grun using btree (h_gem_id, h_nb_id, gb_nummer) where c_grun_status = '1';

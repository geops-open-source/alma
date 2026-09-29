create or replace view alma.vflz_publication_status_v as
select distinct on (vfl_id)
    -- TODO do we also need to look at 'publizieren'?
    vfl_id,
    vflz_id as published_vflz_id,
    dat_publizieren,
    belastet
from alma.vflz
    left join alma.bere using (vflz_id)
    left join alma.cod_kbsinfo using (h_bere_res_abwbewe, c_bere_res_abwbewe)
where dat_publizieren <= now()
order by vfl_id, vflz_id desc
;

comment on view alma.vflz_publication_status_v is 'Publikationsdatum und Belastet-Status der Beurteilung der letzten publizierten Version des Standorts, deren Publikationsdatum nicht in der Zukunft liegt.';


drop view if exists alma.vflz_current_v;

create view alma.vflz_current_v
as select vflz_id,
    vfl_id,
    is_current,
    vflz_created_date
   from alma.vflz v
  where is_current
;

comment on view alma.vflz_current_v is 'Alle aktuellen Standortversionen. Gelöschte Standorte werden rausgefiltert. In Altlast4Web war es möglich Standorte zu löschen.';

create or replace view alma.vflz_is_published_v as
 select distinct on (v.vflz_id) v.vflz_id,
        case
            when ((p.rnk = 1) and (p.dat_publizieren is null)) then true
            when ((p.rnk = 1) and (p.dat_publizieren > now())) then false
            when ((p.rnk = 1) and (p.dat_publizieren <= now())) then true
            when ((p.rnk = 2) and p.pub_in_future) then true
            else false
        end as is_latest_published,
        case
            when p.pub_in_future then ( select p.dat_publizieren
              where ((v.vfl_id = p.vfl_id) and (p.rnk = 2)))
            else p.max_dat_publizieren
        end as dat_latest_published
   from (alma.vflz v
   join alma.vflz_current_v c using (vfl_id)
     left join ( select vflz.vflz_id,
            vflz.vfl_id,
            vflz.dat_publizieren,
            dense_rank() over (partition by vflz.vfl_id order by vflz.vflz_id desc) as rnk,
            max_p.max_dat_publizieren,
                case
                    when (max_p.max_dat_publizieren > now()) then true
                    else false
                end as pub_in_future
           from (alma.vflz
             left join ( select vflz_1.vfl_id,
                    max(vflz_1.vflz_id) as max_vflz_id,
                    max(vflz_1.dat_publizieren) as max_dat_publizieren
                   from alma.vflz vflz_1
                  where vflz_1.publizieren
                  group by vflz_1.vfl_id) max_p using (vfl_id))
          where vflz.publizieren
          order by vflz.vflz_id) p on ((v.vflz_id = p.vflz_id)))
;

comment on view alma.vflz_is_published_v is 'Liste der Standortversionen mit dem aktuellen Publikationsstatus.';

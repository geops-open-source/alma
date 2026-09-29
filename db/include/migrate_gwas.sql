-- Migrate data from gwvk (Grundwasservorkommen) and gwnu (GrundwasserNutzung)
-- into the new combined gwas (Grundwasser) table.
--
-- Since both gwvk and gwnu had a UNIQUE constraint on vflz_id (1:1),
-- we merge them into a single row per vflz_id using a full outer join.
--
-- Run this script separately after the V1_54 migration has been applied.

insert into alma.gwas (
    vflz_id,
    h_gwas_relzugw,
    c_gwas_relzugw,
    gwas_flurabstand,
    h_gwas_nutzung,
    c_gwas_nutzung,
    gwas_distanz,
    erfassungs_datum,
    erfasser,
    mutations_datum,
    mutierer,
    is_current
)
select
    coalesce(gwvk.vflz_id, gwnu.vflz_id) as vflz_id,
    gwvk.h_gwvk_relzugw,
    gwvk.c_gwvk_relzugw,
    gwvk.gwvk_flurabstand,
    gwnu.h_gwnu_nutzung,
    gwnu.c_gwnu_nutzung,
    gwnu.gwnu_distanz,
    coalesce(gwvk.erfassungs_datum, gwnu.erfassungs_datum),
    coalesce(gwvk.erfasser, gwnu.erfasser),
    greatest(gwvk.mutations_datum, gwnu.mutations_datum),
    coalesce(gwvk.mutierer, gwnu.mutierer),
    coalesce(gwvk.is_current, gwnu.is_current)
from alma.gwvk
full outer join alma.gwnu on gwvk.vflz_id = gwnu.vflz_id;

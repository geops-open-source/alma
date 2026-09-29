import { gql } from "graphql-request";
import debounce from "lodash/debounce";
import { useEffect, useMemo, useState } from "react";
import useSWR, { type KeyedMutator } from "swr";

import Button from "@/components/Button";
import Dialog from "@/components/Dialog";
import Form from "@/components/Form";
import PlusIcon from "@/components/icons/PlusIcon";
import SaveIcon from "@/components/icons/SaveIcon";
import SearchIcon from "@/components/icons/SearchIcon";
import TrashIcon from "@/components/icons/TrashIcon";
import Input from "@/components/Input";
import Layout from "@/components/Layout";
import Pagination from "@/components/Pagination";
import Spinner from "@/components/Spinner";
import VflzLink from "@/components/VflzLink";
import client from "@/lib/client";
import createPoolMutation from "@/lib/createPoolMutation";
import { useI18n } from "@/lib/i18n";

import type { ChangeEvent, CSSProperties } from "react";

import type {
  CreatePoolMutation,
  FilterPoolsQuery,
  PoolQuery,
  PoolVflzQuery,
  UpdatePoolMutation,
} from "@/lib/graphql";

const queryPoolVflz = gql`
  query poolVflz($page: Int!, $perPage: Int, $poolId: ID!) {
    pool(poolId: $poolId) {
      bezeichnung
      standorte(page: $page, perPage: $perPage) {
        numPages
        numResultsTotal
        results {
          vflId
          vflzId
          bezeichnung
          combinedId
          beurteilung {
            kbsInfo {
              color
            }
          }
        }
      }
    }
  }
`;

const removeFromPool = gql`
  mutation removeFromPool($poolId: ID!, $vflId: ID!) {
    removeFromPool(poolId: $poolId, vflId: $vflId) {
      poolId
    }
  }
`;

function PoolVflz({
  bezeichnung,
  mutateFilter,
  perPage,
  poolId,
}: {
  bezeichnung?: null | string;
  mutateFilter: KeyedMutator<FilterPoolsQuery>;
  perPage?: number;
  poolId: string;
}) {
  const { pluralRules, t } = useI18n();
  const [page, setPage] = useState(1);
  const { data, mutate } = useSWR<PoolVflzQuery>(
    perPage !== undefined && [
      queryPoolVflz,
      { page, perPage: perPage - 5, poolId },
    ],
  );

  return data ? (
    <div className="border-gray-4 overflow-hidden rounded-lg border-2">
      <div className="bg-gray-4 p-2 text-xs font-bold">
        {t(
          `pools.tableHeader.${pluralRules.select(data.pool.standorte.numResultsTotal)}`,
          { count: data.pool.standorte.numResultsTotal.toString() },
        )}
        <i>{bezeichnung}</i>
      </div>
      {data.pool.standorte.numResultsTotal > 0 ? (
        <>
          <table className="text-gray-7 w-full text-sm" data-test="pools-vflz">
            <thead>
              <tr className="bg-gray-3 text-left text-xs">
                <th className="p-2 font-normal">
                  {t("fields.Vflz.standortNummer")}
                </th>
                <th className="p-2 font-normal">
                  {t("fields.Vflz.bezeichnung")}
                </th>
                <th />
              </tr>
            </thead>
            <tbody className="bg-white">
              {data.pool.standorte.results.map((v) => {
                return (
                  <tr
                    className="border-gray-4 relative border-y bg-(--kbs-color)/20 hover:cursor-pointer hover:bg-(--kbs-color)/10"
                    key={v.vflId}
                    style={
                      {
                        "--kbs-color":
                          v.beurteilung?.kbsInfo?.color ??
                          "var(--color-gray-5)",
                      } as CSSProperties
                    }
                    tabIndex={0}
                  >
                    <td className="p-[11.5px]">{v.combinedId}</td>
                    <td className="flex items-center justify-between p-[11.5px]">
                      <VflzLink className="expand-click-area" vflzId={v.vflzId}>
                        {v.bezeichnung}
                      </VflzLink>
                    </td>
                    <td className="hover:bg-red-2 relative w-12">
                      <button
                        className="expand-click-area text-red-6 hover:text-red-7 mx-auto flex items-center"
                        data-test="pools-removeFromPool"
                        onClick={() => {
                          void client
                            .request(removeFromPool, { poolId, vflId: v.vflId })
                            .then(() => {
                              void mutate();
                              void mutateFilter();
                            });
                        }}
                        type="button"
                      >
                        <TrashIcon />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <Pagination
            currentPage={page}
            pagesCount={data.pool.standorte.numPages}
            setPage={setPage}
          />
        </>
      ) : null}
    </div>
  ) : null;
}

const queryPool = gql`
  query pool($poolId: ID!) {
    pool(poolId: $poolId) {
      poolId
      bezeichnung
      bemerkungen
    }
  }
`;

const deletePoolMutation = gql`
  mutation deletePool($poolId: ID!) {
    deletePool(poolId: $poolId)
  }
`;

const updatePoolMutation = gql`
  mutation updatePool($data: UpdatePoolInfoInput!) {
    updatePoolInfo(data: $data) {
      __typename
      ... on ProblemGroup {
        ...FormProblems
      }
    }
  }
  ${Form.fragment}
`;

function Pool({
  mutateFilter,
  perPage,
  poolId,
  setPoolId,
}: {
  mutateFilter: KeyedMutator<FilterPoolsQuery>;
  perPage?: number;
  poolId?: string;
  setPoolId: (poolId: string | undefined) => void;
}) {
  const { t } = useI18n();
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const { data, mutate } = useSWR<PoolQuery>(poolId && [queryPool, { poolId }]);

  return (
    <div className="flex w-full flex-col gap-5">
      <Form
        className="border-gray-4 bg-gray-2 flex w-full flex-col gap-2 rounded-lg border p-5"
        data-test="pools-pool"
        model="Pool"
        onSubmit={async (values) => {
          if (!poolId) {
            const result = await client.request<CreatePoolMutation>(
              createPoolMutation,
              { data: values },
            );
            if (result.createPool?.__typename === "Pool") {
              await mutateFilter();
              setPoolId(result.createPool.poolId);
            } else {
              return result.createPool;
            }
          } else {
            const result = await client.request<UpdatePoolMutation>(
              updatePoolMutation,
              { data: values },
            );
            if (result.updatePoolInfo?.__typename === "Pool") {
              void mutate();
              void mutateFilter();
            } else {
              return result.updatePoolInfo;
            }
          }
        }}
        values={poolId ? data?.pool : { bemerkungen: "", bezeichnung: "" }}
      >
        <h2 className="-mt-2 text-lg font-semibold">
          {t(poolId ? "pools.pool" : "pools.createPool")}
        </h2>
        <div className="grid grid-cols-3 gap-5">
          <Input name="bezeichnung" required />
          <Input
            name="bemerkungen"
            placeholder={t("pools.bemerkungenPlaceholder")}
          />
          <div className="flex items-end gap-2">
            <Dialog
              isOpen={isDeleteDialogOpen}
              onClose={() => {
                setIsDeleteDialogOpen(false);
              }}
              title={t("pools.deletePool")}
            >
              <div>{t("pools.deletePoolMessage")}</div>
              <div className="mt-8 flex justify-end gap-4">
                <Button
                  onClick={() => {
                    setIsDeleteDialogOpen(false);
                  }}
                  outline
                >
                  {t("cancel")}
                </Button>
                <Button
                  data-test="pools-confirmDeletePool"
                  onClick={() => {
                    void client
                      .request(deletePoolMutation, { poolId })
                      .then(() => {
                        setIsDeleteDialogOpen(false);
                        setPoolId(undefined);
                        void mutateFilter();
                      });
                  }}
                >
                  {t("pools.deletePool")}
                </Button>
              </div>
            </Dialog>
            {poolId ? (
              <Button
                className="border-red-5 bg-red-1 text-red-6 hover:bg-red-2 hover:text-red-7 mb-1"
                data-test="pools-deletePool"
                onClick={() => {
                  setIsDeleteDialogOpen(true);
                }}
                outline
                size="small"
              >
                <TrashIcon />
              </Button>
            ) : null}
            <Button className="mb-1" outline size="small" type="submit">
              <SaveIcon />
            </Button>
          </div>
        </div>
      </Form>
      {poolId ? (
        <PoolVflz
          bezeichnung={data?.pool.bezeichnung}
          mutateFilter={mutateFilter}
          perPage={perPage}
          poolId={poolId}
        />
      ) : null}
    </div>
  );
}

const filterPools = gql`
  query filterPools($filter: String, $page: Int, $perPage: Int) {
    pools(filterBezeichnung: $filter, page: $page, perPage: $perPage) {
      numPages
      numResultsTotal
      results {
        poolId
        bezeichnung
        standorte {
          numResultsTotal
        }
      }
    }
  }
`;

export default function PoolsPage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState<number>();
  const [poolId, setPoolId] = useState<string>();
  const [filter, setFilter] = useState("");

  const { data, isLoading, mutate } = useSWR<FilterPoolsQuery>(
    perPage !== undefined && [filterPools, { filter, page, perPage }],
  );

  const handleFilterChange = useMemo(() => {
    return debounce((event: ChangeEvent<HTMLInputElement>) => {
      setPage(1);
      setFilter(event.target.value);
    }, 300);
  }, []);

  useEffect(() => {
    if (data?.pools.results.length) {
      setPoolId((id) => {
        return id ?? data.pools.results[0].poolId;
      });
    }
  }, [data]);

  useEffect(() => {
    const updatePerPage = debounce(() => {
      setPerPage(Math.max(Math.floor((window.innerHeight - 244) / 44), 10));
    }, 300);
    updatePerPage();
    window.addEventListener("resize", updatePerPage);
    return () => {
      return window.removeEventListener("resize", updatePerPage);
    };
  }, []);

  return (
    <Layout container title={t("pools.title")}>
      <div className="mb-4 flex items-center justify-between">
        <Form className="w-96" data-test="pools-filter" model="pools">
          <Input
            icon={<SearchIcon className="text-gray-6" />}
            name="filter"
            onChange={handleFilterChange}
            placeholder={t("pools.filterPlaceholder")}
          />
        </Form>
        <Button
          data-test="pools-createPool"
          onClick={() => {
            setPoolId(undefined);
          }}
        >
          <PlusIcon className="mr-2" />
          {t("pools.createPool")}
        </Button>
      </div>
      <div className="flex gap-5">
        <div
          className="divide-gray-4 border-gray-4 text-gray-7 h-fit w-96 shrink-0 divide-y overflow-hidden rounded-lg border text-sm font-medium"
          data-test="pools-list"
        >
          {isLoading || perPage === undefined ? (
            <Spinner className="mx-auto my-8 h-8" />
          ) : null}
          {data?.pools.results.map((p) => {
            return (
              <div
                className={`hover:bg-gray-3 flex h-11 items-center justify-between p-2 hover:cursor-pointer ${p.poolId === poolId ? "bg-gray-3 font-bold" : ""}`}
                key={p.poolId}
                onClick={() => {
                  setPoolId(p.poolId);
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    setPoolId(p.poolId);
                  }
                }}
                role="link"
                tabIndex={0}
              >
                <span className="truncate">{p.bezeichnung}</span>
                <span className="border-gray-4 bg-gray-2 text-gray-6 rounded-full border px-2 py-0.5 text-xs font-medium">
                  {p.standorte.numResultsTotal}
                </span>
              </div>
            );
          })}
          {data?.pools.numResultsTotal === 0 ? (
            <div className="mx-auto my-8 h-8 text-center font-normal">
              {t("pools.noPools")}
            </div>
          ) : null}
          {data && data.pools.numResultsTotal > 0 ? (
            <Pagination
              currentPage={page}
              pagesCount={data.pools.numPages}
              setPage={setPage}
              size="small"
            />
          ) : null}
        </div>
        <Pool
          mutateFilter={mutate}
          perPage={perPage}
          poolId={poolId}
          setPoolId={setPoolId}
        />
      </div>
    </Layout>
  );
}

import { gql } from "graphql-request";
import debounce from "lodash/debounce";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { useFormContext } from "react-hook-form";
import useSWR, { type KeyedMutator, useSWRConfig } from "swr";

import AdminLayout from "@/components/AdminLayout";
import Button from "@/components/Button";
import Checkbox from "@/components/Checkbox";
import Dialog from "@/components/Dialog";
import Form from "@/components/Form";
import CheckIcon from "@/components/icons/CheckIcon";
import EditIcon from "@/components/icons/EditIcon";
import LockedIcon from "@/components/icons/LockedIcon";
import PlusIcon from "@/components/icons/PlusIcon";
import SearchIcon from "@/components/icons/SearchIcon";
import Input from "@/components/Input";
import Pagination from "@/components/Pagination";
import Spinner from "@/components/Spinner";
import client from "@/lib/client";
import { translationsQuery, useI18n } from "@/lib/i18n";

import type {
  AdminCodeListQuery,
  AdminCodeListsQuery,
  CodeList,
  CodeListEntry,
  CreateCodeListEntryMutation,
  UpdateCodeListEntryMutation,
  UpdateCodeListMutation,
} from "@/lib/graphql";

const queryCodeLists = gql`
  query adminCodeLists(
    $filter: String
    $lang: Language
    $page: Int
    $perPage: Int
  ) {
    codeLists(filter: $filter, lang: $lang, page: $page, perPage: $perPage) {
      numPages
      results {
        bezeichnung {
          de
          fr
          it
        }
        cliId
        readOnly
      }
    }
  }
`;

const updateCodeListMutation = gql`
  mutation updateCodeList($data: UpdateCodeListInput!) {
    updateCodeList(data: $data) {
      cliId
    }
  }
`;

const createCodeListEntryMutation = gql`
  mutation createCodeListEntry($data: CreateCodeListEntryInput!) {
    createCodeListEntry(data: $data) {
      __typename
      ... on ProblemGroup {
        ...FormProblems
      }
    }
  }
  ${Form.fragment}
`;

const updateCodeListEntryMutation = gql`
  mutation updateCodeListEntry($data: UpdateCodeListEntryInput!) {
    updateCodeListEntry(data: $data) {
      __typename
      ... on CodeListEntry {
        code
      }
      ... on ProblemGroup {
        ...FormProblems
      }
    }
  }
  ${Form.fragment}
`;

function CodeListFormBody() {
  const { t } = useI18n();
  const { formState } = useFormContext();
  const isDirty = Object.keys(formState.dirtyFields).length > 0;
  return (
    <div className="flex w-lg flex-col gap-2">
      <Input disabled label={t("admin.fields.key")} name="cliId" />
      <Input label={t("language.DE")} name="bezeichnung.de" required />
      <Input label={t("language.FR")} name="bezeichnung.fr" required />
      <Input label={t("language.IT")} name="bezeichnung.it" required />
      <div className="flex justify-end pt-2">
        <Button disabled={!isDirty} type="submit">
          {t("admin.codelists.save")}
        </Button>
      </div>
    </div>
  );
}

function CodeListEntryFormBody({ readOnly }: { readOnly?: boolean }) {
  const { t } = useI18n();
  const { formState } = useFormContext();
  const isDirty = Object.keys(formState.dirtyFields).length > 0;
  return (
    <>
      <div className="flex w-lg flex-col gap-2">
        <div className="flex gap-4">
          <Input
            disabled={formState.defaultValues?.code !== undefined}
            label={t("admin.fields.key")}
            name="code"
            required
          />
          <Input disabled={readOnly} name="sortKey" type="integer" />
          <Checkbox disabled={readOnly} name="isActive" />
        </div>
        <Input label={t("language.DE")} name="bezeichnung.de" required />
        <Input label={t("language.FR")} name="bezeichnung.fr" required />
        <Input label={t("language.IT")} name="bezeichnung.it" required />
        <div className="flex justify-end pt-2">
          <Button disabled={!isDirty} type="submit">
            {t("admin.codelists.save")}
          </Button>
        </div>
      </div>
    </>
  );
}

const queryCodeList = gql`
  query adminCodeList($cliIds: [ID!]!) {
    codeLists(cliIds: $cliIds) {
      results {
        bezeichnung {
          de
          fr
          it
        }
        cliId
        readOnly
        entries {
          code
          bezeichnung {
            de
            fr
            it
          }
          sortKey
          isActive
        }
      }
    }
  }
`;

function CodeList({
  cliId,
  mutateList,
  perPage,
}: {
  cliId?: string;
  mutateList: KeyedMutator<AdminCodeListsQuery>;
  perPage: number;
}) {
  const { activeLocale, t } = useI18n();
  const router = useRouter();
  const [editCode, setEditCode] = useState<CodeListEntry>();
  const [page, setPage] = useState(1);
  const [, setTick] = useState(1);
  const [isEditCodeDialogOpen, setIsEditCodeDialogOpen] = useState(false);
  const [isEditListDialogOpen, setIsEditListDialogOpen] = useState(false);
  const config = useSWRConfig();
  const { data, mutate } = useSWR<AdminCodeListQuery>(
    cliId && [queryCodeList, { cliIds: [cliId] }],
  );
  const codeList = data?.codeLists.results.at(0);
  const pagesCount = codeList
    ? Math.ceil(codeList.entries.length / perPage)
    : 0;

  if (!cliId) {
    return null;
  }

  return (
    <div className="border-gray-4 sticky top-4 basis-2/3 rounded-lg border bg-white">
      <Dialog
        isOpen={isEditListDialogOpen}
        onClose={() => {
          setIsEditListDialogOpen(false);
        }}
        title={t("admin.codelists.editCodeList")}
      >
        <Form
          defaultValues={codeList}
          model="CodeList"
          onSubmit={async ({ bezeichnung }) => {
            await client.request<UpdateCodeListMutation>(
              updateCodeListMutation,
              { data: { bezeichnung, cliId } },
            );
            setIsEditListDialogOpen(false);
            await mutate();
            await mutateList();
          }}
        >
          <CodeListFormBody />
        </Form>
      </Dialog>
      <Dialog
        isOpen={isEditCodeDialogOpen}
        onClose={() => {
          setEditCode(undefined);
          setIsEditCodeDialogOpen(false);
        }}
        title={t("admin.codelists.edit")}
      >
        <Form
          defaultValues={editCode}
          model="CodeListEntry"
          onSubmit={async (values: CodeListEntry, methods) => {
            if (methods.formState.defaultValues?.code) {
              const { updateCodeListEntry } =
                await client.request<UpdateCodeListEntryMutation>(
                  updateCodeListEntryMutation,
                  { data: values },
                );
              if (updateCodeListEntry.__typename === "ProblemGroup") {
                return updateCodeListEntry; // ProblemGroup
              }
            } else {
              const { createCodeListEntry } =
                await client.request<CreateCodeListEntryMutation>(
                  createCodeListEntryMutation,
                  { data: { ...values, cliId, isActive: !!values.isActive } },
                );
              if (createCodeListEntry.__typename === "ProblemGroup") {
                return createCodeListEntry; // ProblemGroup
              }
            }
            setIsEditCodeDialogOpen(false);
            setEditCode(undefined);
            await mutate();
            await config.mutate(translationsQuery);
            setTick((tick) => {
              return tick + 1; // trigger re-render to update translations
            });
            router.events.on("routeChangeComplete", () => {
              router.reload(); // Reload app to apply changes to Code dropdown options
            });
          }}
        >
          <CodeListEntryFormBody readOnly={codeList?.readOnly} />
        </Form>
      </Dialog>
      <h2 className="mx-4 mt-4 text-lg font-semibold">
        {codeList?.bezeichnung?.[activeLocale]} ({cliId})
      </h2>
      <Button
        className="mx-4 my-2 flex gap-2"
        onClick={() => {
          setIsEditListDialogOpen(true);
        }}
        plain
      >
        <EditIcon className="h-5 w-5" />
        {t("admin.codelists.editCodeList")}
      </Button>
      {codeList?.readOnly ? null : (
        <Button
          className="mx-4 my-2 flex gap-2"
          disabled={codeList?.readOnly}
          onClick={() => {
            setEditCode(undefined);
            setIsEditCodeDialogOpen(true);
          }}
          plain
        >
          <PlusIcon />
          {t("admin.codelists.create")}
        </Button>
      )}
      <div className="mx-4">
        <table className="w-full text-sm" data-test="admin-codelist-entries">
          <thead>
            <tr>
              <th className="w-16 p-2 text-left">
                {t("fields.CodeListEntry.code")}
              </th>
              <th className="p-2 text-left">
                {t("fields.CodeListEntry.bezeichnung")}
              </th>
              <th className="w-16 p-2 text-left">
                {t("fields.CodeListEntry.sortKey")}
              </th>
              <th className="w-16 p-2 text-left">
                {t("fields.CodeListEntry.isActive")}
              </th>
            </tr>
          </thead>
          <tbody>
            {codeList?.entries
              .slice((page - 1) * perPage, page * perPage)
              .map((entry) => {
                return (
                  <tr
                    className="hover:bg-gray-2 border-gray-4 cursor-pointer border-y"
                    key={entry.code}
                    onClick={() => {
                      setEditCode(entry);
                      setIsEditCodeDialogOpen(true);
                    }}
                  >
                    <td className="text-gray-6 p-2">
                      {entry.code.split(":").pop()}
                    </td>
                    <td className="p-2">{t(entry.code)}</td>
                    <td className="p-2">{entry.sortKey}</td>
                    <td className="p-2">
                      {entry.isActive ? <CheckIcon /> : null}
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>
      <Pagination
        currentPage={Math.min(page, pagesCount + 1)}
        pagesCount={pagesCount}
        setPage={setPage}
      />
    </div>
  );
}

export default function AdminCodelistsPage() {
  const { activeLocale, t } = useI18n();
  const [cliId, setCliId] = useState<string>();
  const [filterInput, setFilterInput] = useState("");
  const [filter, setFilter] = useState("");
  const [perPage, setPerPage] = useState<number>();
  const [page, setPage] = useState(1);
  const { data, mutate } = useSWR<AdminCodeListsQuery>(
    perPage !== undefined && [
      queryCodeLists,
      { filter, lang: activeLocale.toUpperCase(), page, perPage },
    ],
    {
      onSuccess: ({ codeLists }) => {
        if (!cliId && codeLists.results.length > 0) {
          setCliId(codeLists.results[0].cliId);
        }
      },
    },
  );

  useEffect(() => {
    const updateFilter = debounce((value: string) => {
      setFilter(value);
      setPage(1);
    }, 300);

    updateFilter(filterInput);

    return () => {
      updateFilter.cancel();
    };
  }, [filterInput]);

  useEffect(() => {
    const updatePerPage = debounce(() => {
      setPerPage(Math.max(Math.floor((window.innerHeight - 300) / 37), 10));
    }, 300);
    updatePerPage();
    window.addEventListener("resize", updatePerPage);
    return () => {
      return window.removeEventListener("resize", updatePerPage);
    };
  }, []);

  return (
    <AdminLayout>
      <div className="mt-4 flex items-start gap-4">
        <div className="flex basis-1/3 flex-col">
          <div>
            <Form model="CodeList">
              <Input
                className="mb-4"
                hideLabel
                icon={<SearchIcon className="text-gray-6" />}
                name="codeListsFilter"
                onChange={(e) => {
                  setFilterInput(e.target.value);
                }}
                placeholder={t("fields.CodeList.filter")}
                value={filterInput}
              />
            </Form>
          </div>
          <div
            className="divide-gray-4 border-gray-4 text-gray-7 divide-y overflow-hidden rounded-lg border bg-white text-sm font-semibold"
            data-test="admin-codeLists-list"
          >
            {data ? (
              <>
                {data.codeLists.results.map((codeList) => {
                  return (
                    <button
                      className={`hover:bg-blue-1 hover:text-blue-8 flex w-full items-center justify-between space-x-4 px-3 py-2 text-left ${cliId && codeList.cliId === cliId ? "bg-blue-1 text-blue-8" : ""}`}
                      key={codeList.cliId}
                      onClick={() => {
                        setCliId(codeList.cliId);
                      }}
                    >
                      {codeList.bezeichnung?.[activeLocale]} ({codeList.cliId})
                      {codeList.readOnly ? <LockedIcon /> : null}
                    </button>
                  );
                })}
                <Pagination
                  currentPage={page}
                  pagesCount={data?.codeLists.numPages || 0}
                  setPage={setPage}
                />
              </>
            ) : (
              <div className="w-full p-4 text-center">
                <Spinner className="mx-auto my-8 size-8" />
              </div>
            )}
          </div>
        </div>
        <CodeList
          cliId={cliId}
          key={cliId}
          mutateList={mutate}
          perPage={(perPage ?? 10) - 2}
        />
      </div>
    </AdminLayout>
  );
}

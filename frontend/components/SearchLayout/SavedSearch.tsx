import { gql } from "graphql-request";
import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { FormProvider, useForm, useFormContext } from "react-hook-form";
import useSWR, { type KeyedMutator } from "swr";

import Button from "@/components/Button";
import Checkbox from "@/components/Checkbox";
import Dialog from "@/components/Dialog";
import Form from "@/components/Form";
import EditIcon from "@/components/icons/EditIcon";
import SearchIcon from "@/components/icons/SearchIcon";
import Input from "@/components/Input";
import client from "@/lib/client";
import { useI18n } from "@/lib/i18n";
import {
  getSearchURL,
  savedSearchesQuery,
  updateSavedSearchMutation,
} from "@/lib/search";
import useCurrentUser from "@/lib/useCurrentUser";

import SidebarDialog from "./SidebarDialog";

import type {
  CreateSavedSearchMutation,
  SavedSearchesQuery,
  SavedSearchFragment,
  UpdateSavedSearchMutation,
} from "@/lib/graphql";

const createSavedSearchMutation = gql`
  mutation createSavedSearch($data: CreateSavedSearchInput!) {
    savedSearch: createSavedSearch(data: $data) {
      __typename
      ... on ProblemGroup {
        ...FormProblems
      }
    }
  }
  ${Form.fragment}
`;

const deleteSavedSearchMutation = gql`
  mutation deleteSavedSearch($savedSearchId: ID!) {
    deleteSavedSearch(savedSearchId: $savedSearchId)
  }
`;

function SavedSearchDialogSubmitButton() {
  const { t } = useI18n();
  const { formState } = useFormContext();
  const isClean = Object.keys(formState.dirtyFields).length === 0;
  return (
    <Button disabled={isClean} type="submit">
      {t("search.savedSearchDialog.save")}
    </Button>
  );
}

function SavedSearchDialog({
  mutateSavedSearches,
  onClose,
  savedSearch,
}: {
  mutateSavedSearches: KeyedMutator<SavedSearchesQuery>;
  onClose: () => void;
  savedSearch?: SavedSearchFragment;
}) {
  const { t } = useI18n();
  const currentUser = useCurrentUser();
  const isFromDifferentUser = savedSearch?.user.id !== currentUser.id;

  const deleteSavedSearch = useCallback(async () => {
    await client.request(deleteSavedSearchMutation, {
      savedSearchId: savedSearch?.savedSearchId,
    });
    void mutateSavedSearches();
    onClose();
  }, [mutateSavedSearches, onClose, savedSearch?.savedSearchId]);

  return (
    <Dialog
      isOpen={savedSearch !== undefined}
      onClose={onClose}
      title={
        savedSearch
          ? t(
              savedSearch.savedSearchId
                ? "search.savedSearchDialog.updateTitle"
                : "search.savedSearchDialog.createTitle",
            )
          : ""
      }
    >
      <Form<SavedSearchFragment>
        className="min-w-96 space-y-4"
        data-test="search-savedSearchDialog"
        model="SavedSearch"
        onSubmit={(values) => {
          if (!savedSearch) {
            return;
          }
          const data = savedSearch.savedSearchId
            ? {
                isShared: values.isShared,
                name: values.name,
                savedSearchId: savedSearch.savedSearchId,
                showOnDashboard: values.showOnDashboard,
              }
            : {
                fields: savedSearch.fields,
                isGrouped: savedSearch.isGrouped,
                isShared: values.isShared,
                name: values.name,
                query: savedSearch.query,
                showOnDashboard: values.showOnDashboard,
                sortBy: savedSearch.sortBy,
              };
          return client
            .request<CreateSavedSearchMutation | UpdateSavedSearchMutation>(
              savedSearch.savedSearchId
                ? updateSavedSearchMutation
                : createSavedSearchMutation,
              { data },
            )
            .then((result) => {
              if (result.savedSearch.__typename === "ProblemGroup") {
                return result.savedSearch;
              }
              void mutateSavedSearches();
              onClose();
            });
        }}
        values={savedSearch}
      >
        <Input disabled={isFromDifferentUser} name="name" required />
        <Checkbox
          data-test="search-savedSearchDialog-isShared"
          disabled={isFromDifferentUser}
          name="isShared"
        />
        <Checkbox name="showOnDashboard" />
        <div className="flex justify-end gap-4">
          {savedSearch?.savedSearchId && isFromDifferentUser === false ? (
            <Button
              className="text-red-6 hover:text-red-7 border-red-6"
              onClick={() => {
                return void deleteSavedSearch();
              }}
              outline
            >
              {t("search.savedSearchDialog.delete")}
            </Button>
          ) : null}
          {savedSearch?.savedSearchId === "" ? (
            <Button onClick={onClose} outline>
              {t("search.savedSearchDialog.cancel")}
            </Button>
          ) : null}
          <SavedSearchDialogSubmitButton />
        </div>
      </Form>
    </Dialog>
  );
}

function SaveIconLarge() {
  return (
    <svg viewBox="0 0 48 48" width="48" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M0 24C0 10.83 10.83 0 24 0s24 10.83 24 24-10.83 24-24 24S0 37.17 0 24Z"
        fill="#e0f2fe"
      />
      <path
        d="M19 15v3.4c0 .56 0 .84.1 1.05a1 1 0 0 0 .45.44c.21.1.49.1 1.05.1h6.8c.56 0 .84 0 1.05-.1a1 1 0 0 0 .44-.44c.1-.21.1-.49.1-1.05V16m0 17v-6.4c0-.56 0-.84-.1-1.05a1 1 0 0 0-.44-.44c-.21-.1-.49-.1-1.05-.1h-6.8c-.56 0-.84 0-1.05.1a1 1 0 0 0-.44.44c-.1.21-.1.49-.1 1.05V33M33 21.32v6.88c0 1.68 0 2.52-.33 3.16a3 3 0 0 1-1.3 1.31c-.65.33-1.49.33-3.17.33h-8.4c-1.68 0-2.52 0-3.16-.33a3 3 0 0 1-1.31-1.3c-.33-.66-.33-1.5-.33-3.17v-8.4c0-1.68 0-2.52.33-3.16a3 3 0 0 1 1.3-1.31c.65-.33 1.49-.33 3.17-.33h6.87c.5 0 .74 0 .97.05.2.05.4.13.58.24.2.13.37.3.72.65l3.12 3.12c.35.35.52.52.64.72.11.18.2.38.24.58.06.23.06.48.06.96Z"
        fill="none"
        stroke="#0086c9"
        strokeWidth="1.6"
      />
    </svg>
  );
}

function SavedSearchSidebarDialog({
  savedSearches = [],
  setSavedSearch,
}: {
  savedSearches?: SavedSearchFragment[];
  setSavedSearch: (search: SavedSearchFragment | undefined) => void;
}) {
  const { t } = useI18n();
  const methods = useForm();
  const currentUser = useCurrentUser();
  const [filter, setFilter] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const filteredSavedSearches = useMemo(() => {
    return savedSearches.filter((search) => {
      if (filter === "") {
        return true;
      }
      return search.name.toLowerCase().includes(filter.toLowerCase());
    });
  }, [filter, savedSearches]);

  return (
    <>
      <SidebarDialog
        icon={<SaveIconLarge />}
        isOpen={isOpen}
        onClose={() => {
          setIsOpen(false);
        }}
        subtitle={t("search.savedSearchSidebar.subtitle")}
        title={t("search.savedSearchSidebar.title")}
      >
        <FormProvider {...methods}>
          <Input
            className="pt-4"
            icon={<SearchIcon className="text-gray-6" />}
            label=""
            onChange={(e) => {
              setFilter(e.target.value);
            }}
            placeholder={t("search.savedSearchSidebar.placeholder")}
            value={filter}
          />
        </FormProvider>
        {filteredSavedSearches.length === 0 ? (
          <div className="text-gray-6 pt-3 text-sm">
            {t("search.savedSearchSidebar.empty")}
          </div>
        ) : (
          <ul
            className="divide-gray-4 border-gray-4 text-gray-7 mt-4 divide-y overflow-hidden rounded-lg border text-sm"
            data-test="search-savedSearchSidebar-list"
          >
            {filteredSavedSearches.map((search) => {
              return (
                <li className="flex" key={search.savedSearchId}>
                  <Link
                    className="text-gray-6 hover:bg-blue-1 grow px-3 py-2 text-left"
                    href={getSearchURL(search)}
                    onNavigate={() => {
                      setIsOpen(false);
                    }}
                  >
                    <div className="font-semibold">{search.name}</div>
                    {search.user.id !== currentUser.id ? (
                      <div className="text-xs">{search.user.username}</div>
                    ) : null}
                  </Link>
                  <button
                    className="text-gray-6 hover:bg-blue-1 hover:text-blue-8 p-2"
                    onClick={() => {
                      setSavedSearch(search);
                    }}
                    type="button"
                  >
                    <EditIcon className="h-4 w-4" />
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </SidebarDialog>
      <Button
        data-test="search-savedSearchSidebar"
        onClick={() => {
          setIsOpen(true);
        }}
        plain
      >
        {t("search.savedSearchSidebar.button")}
      </Button>
    </>
  );
}

export default function SavedSearch({
  savedSearch,
  setSavedSearch,
}: {
  savedSearch?: SavedSearchFragment;
  setSavedSearch: (search: SavedSearchFragment | undefined) => void;
}) {
  const { activeLocale } = useI18n();
  const { data, mutate } = useSWR<SavedSearchesQuery>([
    savedSearchesQuery,
    { lang: activeLocale.toUpperCase() },
  ]);
  return (
    <>
      <SavedSearchDialog
        mutateSavedSearches={mutate}
        onClose={() => {
          setSavedSearch(undefined);
        }}
        savedSearch={savedSearch}
      />
      <SavedSearchSidebarDialog
        savedSearches={data?.savedSearches}
        setSavedSearch={setSavedSearch}
      />
    </>
  );
}

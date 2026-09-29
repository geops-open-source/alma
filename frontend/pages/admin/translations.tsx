import { gql } from "graphql-request";
import isObject from "lodash/isObject";
import set from "lodash/set";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";

import AdminLayout from "@/components/AdminLayout";
import Box from "@/components/Box";
import Button from "@/components/Button";
import Dialog from "@/components/Dialog";
import Form from "@/components/Form";
import SearchIcon from "@/components/icons/SearchIcon";
import Input from "@/components/Input";
import Pagination from "@/components/Pagination";
import client from "@/lib/client";
import { translationsQuery, useI18n } from "@/lib/i18n";

import type { TranslationsQuery } from "@/lib/graphql";

const updateTranslation = gql`
  mutation UpdateTranslation($data: UpdateTranslationInput!) {
    updateTranslation(data: $data)
  }
`;

interface TranslationItem {
  de: string;
  fr: string;
  it: string;
  key: string;
}

function SearchCell({
  placeholder,
  setFilter,
  ...props
}: {
  name?: string;
  placeholder?: string;
  setFilter: (value: string) => void;
  value: string;
}) {
  const { t } = useI18n();
  return (
    <td className="relative py-2">
      <SearchIcon className="text-gray-6 absolute top-4 left-2" />
      <input
        className="border-gray-5 rounded-lg border px-3 py-2 pl-8 text-xs font-medium shadow-xs focus:outline-hidden"
        onChange={(event) => {
          setFilter(event.target.value);
        }}
        placeholder={placeholder ?? t("admin.translations.filterPlaceholder")}
        type="text"
        {...props}
      />
    </td>
  );
}

const PER_PAGE = 12;

export default function AdminFieldsPage() {
  const i18n = useI18n();
  const { data, mutate } = useSWR<TranslationsQuery>(translationsQuery);
  const [deFilter, setDeFilter] = useState("");
  const [frFilter, setFrFilter] = useState("");
  const [itFilter, setItFilter] = useState("");
  const [keyFilter, setKeyFilter] = useState("");
  const [currentPage, setPage] = useState(1);
  const [editTranslation, setEditTranslation] = useState<TranslationItem>();

  const translations: TranslationItem[] = useMemo(() => {
    if (data?.translations === undefined) {
      return [];
    }
    const fr = Object.entries(data.translations.fr);
    const it = Object.entries(data.translations.it);
    return Object.entries(data.translations.de)
      .map(([deKey, deValue]) => {
        const byKey = ([key]: [string, string]) => {
          return key === deKey;
        };
        return {
          de: deValue,
          fr: fr.find(byKey)?.[1] ?? "",
          it: it.find(byKey)?.[1] ?? "",
          key: deKey,
        };
      })
      .sort((a, b) => {
        return a.key.localeCompare(b.key);
      });
  }, [data?.translations]);

  const filteredTranslations = useMemo(() => {
    return translations.filter(({ de, fr, it, key }) => {
      let found = true;
      if (keyFilter.length > 0) {
        found = key.toLowerCase().includes(keyFilter.toLowerCase());
      }
      if (deFilter.length > 0 && found) {
        found = de.toLowerCase().includes(deFilter.toLowerCase());
      }
      if (frFilter.length > 0 && found) {
        found = fr.toLowerCase().includes(frFilter.toLowerCase());
      }
      if (itFilter.length > 0 && found) {
        found = it.toLowerCase().includes(itFilter.toLowerCase());
      }
      return found;
    });
  }, [deFilter, frFilter, itFilter, keyFilter, translations]);

  const pagesCount = useMemo(() => {
    return Math.ceil(filteredTranslations.length / PER_PAGE);
  }, [filteredTranslations]);

  useEffect(() => {
    setPage(1);
  }, [deFilter, frFilter, itFilter, keyFilter]);

  return (
    <AdminLayout>
      <Dialog
        isOpen={!!editTranslation}
        onClose={() => {
          setEditTranslation(undefined);
        }}
        title={i18n.t("admin.translations.edit")}
      >
        <Form<TranslationItem>
          model="Translation"
          onSubmit={async ({ de, fr, it, key }) => {
            const deTable = i18n.table("de");
            const frTable = i18n.table("fr");
            const itTable = i18n.table("it");
            if (isObject(deTable) && isObject(frTable) && isObject(itTable)) {
              set(deTable, key, de);
              set(frTable, key, fr);
              set(itTable, key, it);
            }
            setEditTranslation(undefined);
            await client.request(updateTranslation, {
              data: { key, translation: { de, fr, it } },
            });
            await mutate();
          }}
          values={editTranslation}
        >
          <div className="flex w-lg flex-col gap-2">
            <Input disabled name="key" />
            <Input name="de" />
            <Input name="fr" />
            <Input name="it" />
          </div>
          <div className="mt-4 flex justify-end">
            <Button type="submit">{i18n.t("admin.save")}</Button>
          </div>
        </Form>
      </Dialog>
      <Box className="mt-4">
        <table className="w-full table-fixed text-sm">
          <thead>
            <tr>
              <th className="p-2 text-left">
                {i18n.t("admin.translations.key")}
              </th>
              <th className="p-2 text-left">{i18n.t("language.DE")}</th>
              <th className="p-2 text-left">{i18n.t("language.FR")}</th>
              <th className="p-2 text-left">{i18n.t("language.IT")}</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-gray-4 border-y">
              <SearchCell
                name="key-filter"
                placeholder={i18n.t("admin.translations.keyFilterPlaceholder")}
                setFilter={setKeyFilter}
                value={keyFilter}
              />
              <SearchCell setFilter={setDeFilter} value={deFilter} />
              <SearchCell setFilter={setFrFilter} value={frFilter} />
              <SearchCell setFilter={setItFilter} value={itFilter} />
            </tr>
            {filteredTranslations
              .slice((currentPage - 1) * PER_PAGE, currentPage * PER_PAGE)
              .map((translation) => {
                return (
                  <tr
                    className="hover:bg-gray-2 border-gray-4 cursor-pointer border-y"
                    key={translation.key}
                    onClick={() => {
                      setEditTranslation(translation);
                    }}
                  >
                    <td className="text-gray-6 truncate p-2">
                      {translation.key}
                    </td>
                    <td className="truncate p-2">{translation.de}</td>
                    <td className="truncate p-2">{translation.fr}</td>
                    <td className="truncate p-2">{translation.it}</td>
                  </tr>
                );
              })}
          </tbody>
        </table>
        {filteredTranslations.length == 0 ? (
          <div className="text-gray-7 mx-auto mt-2 h-8 text-center text-sm">
            {i18n.t("admin.translations.noResults")}
          </div>
        ) : null}
        <Pagination
          currentPage={Math.min(currentPage, pagesCount)}
          pagesCount={pagesCount}
          setPage={setPage}
        />
      </Box>
    </AdminLayout>
  );
}

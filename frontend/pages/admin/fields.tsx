import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";

import AdminLayout from "@/components/AdminLayout";
import Checkbox from "@/components/Checkbox";
import Form from "@/components/Form";
import SearchIcon from "@/components/icons/SearchIcon";
import Input from "@/components/Input";
import client from "@/lib/client";
import { useI18n } from "@/lib/i18n";
import queryInstanceSettings from "@/lib/instanceSettingsQuery";
import updateInstanceSetting from "@/lib/updateInstanceSetting";

import type {
  InstanceSettingsQuery,
  UpdateInstanceSettingMutation,
} from "@/lib/graphql";

interface FieldWithLabel {
  category: string;
  key: string;
  label?: string;
  value: boolean;
}

export default function AdminFieldsPage() {
  const { t } = useI18n();
  const router = useRouter();
  const { data, mutate } = useSWR<InstanceSettingsQuery>(queryInstanceSettings);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState<null | string>(null);

  useEffect(() => {
    const reloadPage = (url: string) => {
      if (url !== "/admin/fields") {
        router.reload();
      }
    };
    router.events.on("routeChangeComplete", reloadPage);
    return () => {
      setTimeout(() => {
        router.events.off("routeChangeComplete", reloadPage);
      }, 100); // Delay to ensure the event is handled after component unmount
    };
  }, [router]);

  const fields: FieldWithLabel[] = useMemo(() => {
    return (
      data?.instanceSettings
        .filter((field) => {
          return (
            field.key.startsWith("ui.fields.") && field.key.endsWith(".hidden")
          );
        })
        .map((field) => {
          return {
            category: field.category,
            key: field.key,
            label: t(field.key.split("ui.").pop()?.split(".hidden")[0] ?? ""),
            value: field.value as boolean,
          };
        })
        .filter((field) => {
          if (field.label?.toLowerCase().includes(filter.toLowerCase())) {
            return true;
          }
          if (field.key.toLowerCase().includes(filter.toLowerCase())) {
            return true;
          }
          return false;
        })
        .sort((a, b) => {
          return a.key.localeCompare(b.key);
        }) ?? []
    );
  }, [data?.instanceSettings, filter, t]);

  return (
    <AdminLayout>
      <div className="border-gray-4 sticky top-4 mt-4 rounded-lg border bg-white p-4">
        <h2 className="mb-2">{t("admin.fields.showFields")}</h2>
        {error ? (
          <div data-test="error">{error}</div>
        ) : (
          <Form model="InstanceSettings">
            <Input
              hideLabel
              icon={<SearchIcon className="text-gray-6" />}
              name="fieldsFilter"
              onChange={(e) => {
                setFilter(e.target.value);
              }}
              placeholder={t("admin.fields.placeholder")}
            />
            <div className="text-gray-6 text-xs">
              {t("admin.fields.fieldCount", {
                count: fields.length.toString(),
              })}
            </div>
            <table className="mt-4 w-full table-fixed text-sm">
              <thead>
                <tr>
                  <th className="w-1/6 pr-4 pb-2 text-center">
                    {t("admin.fields.hide")}
                  </th>
                  <th className="w-2/6 pb-2 text-left">
                    {t("admin.fields.label")}
                  </th>
                  <th className="w-3/6 pb-2 text-left">
                    {t("admin.fields.key")}
                  </th>
                </tr>
              </thead>
              <tbody className="mt-14">
                {fields.map((field) => {
                  return (
                    <tr key={field.key}>
                      <td className="p-1">
                        <Checkbox
                          checked={field.value}
                          className="mx-auto my-0.5"
                          label=""
                          onChange={(e) => {
                            void (async () => {
                              try {
                                await client.request<UpdateInstanceSettingMutation>(
                                  updateInstanceSetting,
                                  {
                                    data: {
                                      category: field.category,
                                      key: field.key,
                                      value: e,
                                    },
                                  },
                                );
                                void mutate();
                              } catch (err) {
                                if (err instanceof Error) {
                                  setError(err.message);
                                } else {
                                  setError("Unknown error");
                                }
                              }
                            })();
                          }}
                        />
                      </td>
                      <td className="pr-2">{field.label}</td>
                      <td className="break-all">{field.key}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Form>
        )}
      </div>
    </AdminLayout>
  );
}

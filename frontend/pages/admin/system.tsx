import { useMemo, useState } from "react";
import useSWR from "swr";
import { z } from "zod";

import AdminLayout from "@/components/AdminLayout";
import Button from "@/components/Button";
import Checkbox from "@/components/Checkbox";
import Dialog from "@/components/Dialog";
import Form from "@/components/Form";
import SaveIcon from "@/components/icons/SaveIcon";
import Textarea from "@/components/Textarea";
import client from "@/lib/client";
import { useI18n } from "@/lib/i18n";
import queryInstanceSettings from "@/lib/instanceSettingsQuery";
import updateInstanceSetting from "@/lib/updateInstanceSetting";

import type {
  InstanceSetting,
  InstanceSettingsQuery,
  UpdateInstanceSettingMutation,
} from "@/lib/graphql";

export default function AdminSystemPage() {
  const { t } = useI18n();
  const { data, mutate } = useSWR<InstanceSettingsQuery>(queryInstanceSettings);
  const [isEditSettingOpen, setIsEditSettingOpen] = useState(false);
  const [editSetting, setEditSetting] = useState<InstanceSetting>();

  const systemSettings: InstanceSetting[] = useMemo(() => {
    return (
      data?.instanceSettings.filter((setting) => {
        return !setting.key.startsWith("ui.fields.");
      }) ?? []
    );
  }, [data]);

  return (
    <AdminLayout>
      <div className="border-gray-4 sticky top-4 mt-4 rounded-lg border bg-white p-4">
        <h2 className="text-lg font-semibold">{t("admin.system.heading")}</h2>
        <table className="w-full table-fixed text-sm">
          <thead>
            <tr>
              <th className="w-64 p-2 text-left">Key</th>
              <th className="p-2 text-left">
                {t("fields.InstanceSetting.value")}
              </th>
            </tr>
          </thead>
          <tbody>
            {systemSettings?.map((setting) => {
              const isBoolean =
                setting.valueSchema &&
                typeof setting.valueSchema === "object" &&
                "type" in setting.valueSchema &&
                setting.valueSchema.type === "boolean";
              return (
                <tr
                  className={`border-gray-4 border-y ${isBoolean ? "" : "hover:bg-gray-2 cursor-pointer"}`}
                  key={setting.key}
                  onClick={() => {
                    if (!isBoolean) {
                      setEditSetting(setting);
                      setIsEditSettingOpen(true);
                    }
                  }}
                >
                  <td className="text-gray-6 truncate p-2">{setting.key}</td>
                  <td className="truncate p-2">
                    {isBoolean ? (
                      <Form model="InstanceSetting">
                        <Checkbox
                          checked={!!setting.value}
                          label=""
                          onChange={(e) => {
                            void (async () => {
                              await client.request<UpdateInstanceSettingMutation>(
                                updateInstanceSetting,
                                {
                                  data: {
                                    category: setting.category,
                                    key: setting.key,
                                    value: e,
                                  },
                                },
                              );
                              void mutate();
                            })();
                          }}
                        />
                      </Form>
                    ) : (
                      JSON.stringify(setting.value, null, 1)
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <Dialog
          isOpen={isEditSettingOpen}
          onClose={() => {
            setIsEditSettingOpen(false);
            setEditSetting(undefined);
          }}
          title={t("admin.system.editTitle")}
        >
          <Form
            model={"InstanceSetting"}
            onSubmit={async (values) => {
              const updatedSetting = {
                ...editSetting,
                value: values.value,
              };
              const { updateInstanceSetting: settingResponse } =
                await client.request<UpdateInstanceSettingMutation>(
                  updateInstanceSetting,
                  {
                    data: {
                      category: updatedSetting.category,
                      key: updatedSetting.key,
                      value: JSON.parse(updatedSetting.value) as unknown,
                    },
                  },
                );

              if (settingResponse.__typename === "InstanceSetting") {
                void mutate();
                setIsEditSettingOpen(false);
                setEditSetting(undefined);
              }
            }}
            values={{ value: JSON.stringify(editSetting?.value, null, 2) }}
          >
            <Textarea
              className="w-lg font-mono"
              name="value"
              rows={14}
              validate={(v) => {
                if (!v) {
                  return "Field.errorTitle.required";
                }
                try {
                  z.fromJSONSchema(
                    editSetting?.valueSchema as Record<string, unknown>,
                  ).parse(JSON.parse(String(v)));
                } catch (error) {
                  if (error instanceof SyntaxError) {
                    return "admin.system.jsonInvalid";
                  }
                  if (editSetting?.valueSchema) {
                    return "admin.system.jsonSchemaInvalid";
                  }
                  return "admin.system.jsonInvalid";
                }
              }}
            />
            <div className="mt-4 flex justify-end gap-2">
              <Button
                onClick={() => {
                  setIsEditSettingOpen(false);
                  setEditSetting(undefined);
                }}
                outline
              >
                {t("cancel")}
              </Button>
              <Button className="flex gap-2" type="submit">
                <SaveIcon />
                {t("admin.save")}
              </Button>
            </div>
          </Form>
        </Dialog>
      </div>
    </AdminLayout>
  );
}

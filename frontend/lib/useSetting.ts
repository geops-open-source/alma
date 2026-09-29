import { gql } from "graphql-request";
import { useCallback } from "react";
import useSWRImmutable from "swr/immutable";

import client from "@/lib/client";
import updateInstanceSetting from "@/lib/updateInstanceSetting";

import type {
  SettingCategory,
  UpdateInstanceSettingMutation,
  UseSettingQuery,
} from "@/lib/graphql";

const querySettings = gql`
  query useSetting {
    instanceSettings {
      key
      value
    }
  }
`;

export default function useSetting<T>(
  key: string,
  defaultValue: T,
): [T, (value: T, category?: SettingCategory) => Promise<void>, boolean] {
  const { data, isLoading, mutate } =
    useSWRImmutable<UseSettingQuery>(querySettings);

  const updateSetting = useCallback(
    async (value: T, category: SettingCategory = "GENERAL") => {
      await client.request<UpdateInstanceSettingMutation>(
        updateInstanceSetting,
        { data: { category, key, value } },
      );
      await mutate(
        (currentData) => {
          if (!currentData) {
            return undefined;
          }
          const instanceSettings = [
            ...currentData.instanceSettings.filter((s) => {
              return s.key !== key;
            }),
            { category, key, value, valueSchema: null },
          ];
          return { instanceSettings };
        },
        { revalidate: false },
      );
    },
    [mutate, key],
  );

  const value = data?.instanceSettings.find((s) => {
    return s.key === key;
  })?.value as T;

  return [value ?? defaultValue, updateSetting, isLoading];
}

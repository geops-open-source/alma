import { gql } from "graphql-request";
import { useCallback, useMemo } from "react";
import useSWR from "swr";

import client from "@/lib/client";
import { Permission } from "@/lib/graphql";

import type {
  UpdateUserSettingMutation,
  UseCurrentUserQuery,
} from "@/lib/graphql";

const queryCurrentUser = gql`
  query useCurrentUser {
    currentUser {
      id
      username
      permissions
      settings {
        key
        value
      }
    }
  }
`;

const updateUserSetting = gql`
  mutation updateUserSetting($data: UpdateUserSettingInput!) {
    updateUserSetting(data: $data) {
      key
      value
    }
  }
`;

export default function useCurrentUser() {
  const { data, isLoading, mutate } =
    useSWR<UseCurrentUserQuery>(queryCurrentUser);

  const permissions = useMemo(() => {
    const currentUserPermissions = data?.currentUser.permissions;
    return {
      canEditProcess: currentUserPermissions?.includes(Permission.EditProcess),
      canEditUser: currentUserPermissions?.includes(Permission.EditUser),
      canEditVfl: currentUserPermissions?.includes(Permission.EditVfl),
      canViewProcess: currentUserPermissions?.includes(Permission.ViewProcess),
      canViewVfl: currentUserPermissions?.includes(Permission.ViewVfl),
    };
  }, [data?.currentUser.permissions]);

  const getSetting = useCallback(
    <T>(key: string, fallback: T) => {
      const settings = data?.currentUser.settings;
      return (
        (settings?.find((s) => {
          return s.key === key;
        })?.value as T) ?? fallback
      );
    },
    [data],
  );

  const updateSetting = useCallback(
    async <T>(key: string, value: T) => {
      await client.request<UpdateUserSettingMutation>(updateUserSetting, {
        data: { key, value },
      });
      await mutate(
        (currentData) => {
          if (!currentData) {
            return undefined;
          }
          const settings = [
            ...currentData.currentUser.settings.filter((s) => {
              return s.key !== key;
            }),
            { key, value },
          ];
          return { currentUser: { ...currentData.currentUser, settings } };
        },
        { revalidate: false },
      );
    },
    [mutate],
  );

  const { id, username } = data?.currentUser ?? {};

  return { getSetting, id, isLoading, permissions, updateSetting, username };
}

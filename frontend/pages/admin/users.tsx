import { gql } from "graphql-request";
import { useEffect, useState } from "react";
import { useFormContext } from "react-hook-form";
import useSWR from "swr";

import AdminLayout from "@/components/AdminLayout";
import Button from "@/components/Button";
import Checkbox from "@/components/Checkbox";
import Form from "@/components/Form";
import LockedIcon from "@/components/icons/LockedIcon";
import SaveIcon from "@/components/icons/SaveIcon";
import Input from "@/components/Input";
import Listbox from "@/components/Listbox";
import Message from "@/components/Message";
import PasswordRules from "@/components/PasswordRules";
import client from "@/lib/client";
import { RoleName } from "@/lib/graphql";
import { useI18n } from "@/lib/i18n";
import usePasswordValidation from "@/lib/usePasswordValidation";

import type {
  CreateUserInput,
  CreateUserMutation,
  UpdateUserInput,
  UpdateUserMutation,
  UsersQuery,
} from "@/lib/graphql";

const userFragment = gql`
  fragment User on User {
    id
    email
    firstName
    lastName
    roleName
    isSachbearbeitung
  }
`;

const queryUsers = gql`
  query Users {
    users {
      ...User
    }
  }
  ${userFragment}
`;

const createUserMutation = gql`
  mutation createUser($data: CreateUserInput!) {
    user: createUser(data: $data) {
      ... on User {
        ...User
      }
      ... on ProblemGroup {
        ...FormProblems
      }
    }
  }
  ${Form.fragment}
  ${userFragment}
`;

const updateUserMutation = gql`
  mutation updateUser($data: UpdateUserInput!) {
    user: updateUser(data: $data) {
      ... on User {
        ...User
      }
      ... on ProblemGroup {
        ...FormProblems
      }
    }
  }
  ${Form.fragment}
  ${userFragment}
`;

function SubmitButton() {
  const { formState } = useFormContext();
  const { t } = useI18n();
  const isClean = Object.keys(formState.dirtyFields).length === 0;
  return (
    <div className="flex justify-end">
      <Button disabled={isClean} type="submit">
        <SaveIcon className="mr-2" /> {t("admin.save")}
      </Button>
    </div>
  );
}

const emptyUser: CreateUserInput = {
  email: "",
  firstName: "",
  isSachbearbeitung: false,
  lastName: "",
  password: "",
  roleName: null,
};

export default function AdminUsersPage() {
  const { data, mutate } = useSWR<UsersQuery>(queryUsers);
  const [selectedUser, setSelectedUser] = useState<
    CreateUserInput | UpdateUserInput
  >();
  const { t } = useI18n();
  const passwordValidation = usePasswordValidation();

  useEffect(() => {
    if (data?.users?.length) {
      setSelectedUser((user) => {
        return user ?? data.users[0];
      });
    }
  }, [data]);

  return (
    <AdminLayout>
      <div className="flex justify-end pt-4">
        <Button
          data-test="admin-users-create"
          onClick={() => {
            setSelectedUser(emptyUser);
          }}
          outline
        >
          {t("admin.users.create")}
        </Button>
      </div>
      <div className="mt-4 flex items-start gap-4">
        <div
          className="divide-gray-4 border-gray-4 text-gray-7 basis-1/3 divide-y overflow-hidden rounded-lg border bg-white text-sm font-semibold"
          data-test="admin-users-List"
        >
          {data?.users?.map((user) => {
            return (
              <button
                className={`hover:bg-blue-1 hover:text-blue-8 flex w-full items-center justify-between space-x-4 px-3 py-2 text-left ${selectedUser && "id" in selectedUser && user.id === selectedUser?.id ? "bg-blue-1 text-blue-8" : ""}`}
                key={user.id}
                onClick={() => {
                  setSelectedUser(user);
                }}
              >
                <div>{user.email}</div>
                {user.roleName ? null : <LockedIcon className="shrink-0" />}
              </button>
            );
          })}
        </div>
        <div className="w-full space-y-4">
          <div className="border-gray-4 sticky top-4 basis-2/3 rounded-lg border bg-white p-4">
            {selectedUser ? (
              <Form
                className="space-y-2"
                model="User"
                onSubmit={async (values) => {
                  const mutation =
                    "id" in selectedUser
                      ? updateUserMutation
                      : createUserMutation;
                  const result = await client.request<
                    CreateUserMutation | UpdateUserMutation
                  >(mutation, { data: values });
                  if ("id" in result.user) {
                    setSelectedUser(result.user);
                    await mutate();
                  } else {
                    return result.user;
                  }
                }}
                values={selectedUser}
              >
                <h2 className="text-lg font-semibold">
                  {"id" in selectedUser
                    ? selectedUser.email
                    : t("admin.users.create")}
                </h2>
                <Input name="firstName" required />
                <Input name="lastName" required />
                <Input name="email" required />
                <Listbox
                  name="roleName"
                  options={[
                    { label: "-", value: null },
                    ...Object.values(RoleName)
                      .map((value) => {
                        return { label: t(`RoleName.${value}`), value };
                      })
                      .sort((a, b) => {
                        return a.label.localeCompare(b.label);
                      }),
                  ]}
                />
                {"id" in selectedUser ? null : (
                  <>
                    <Input
                      name="password"
                      required
                      type="password"
                      validate={passwordValidation}
                    />
                    <Message>{t("admin.users.password")}</Message>
                    <PasswordRules />
                  </>
                )}
                <Checkbox name="isSachbearbeitung" />
                <SubmitButton />
              </Form>
            ) : null}
          </div>
        </div>
      </div>
      <button
        className="text-gray-2 hover:text-red-5"
        onClick={() => {
          throw new Error("Sentry Test Error");
        }}
        type="button"
      >
        Sentry Test Error
      </button>
    </AdminLayout>
  );
}

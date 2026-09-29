import { gql } from "graphql-request";
import { useEffect } from "react";
import { useFormContext, useWatch } from "react-hook-form";

import Button from "@/components/Button";
import Fieldset from "@/components/Fieldset";
import Form from "@/components/Form";
import Input from "@/components/Input";
import Layout from "@/components/Layout";
import PasswordRules from "@/components/PasswordRules";
import client from "@/lib/client";
import { useI18n } from "@/lib/i18n";
import usePasswordValidation from "@/lib/usePasswordValidation";

import type { UpdateUserPasswordMutation } from "@/lib/graphql";

const updateUserPasswordMutation = gql`
  mutation updateUserPassword($data: UpdateCurrentUserPasswordInput!) {
    updateCurrentUserPassword(data: $data) {
      ...FormProblems
    }
  }
  ${Form.fragment}
`;

interface UserFormValues {
  password: string;
  passwordRepeat: string;
}

function SubmitButton() {
  const { formState, reset } = useFormContext();
  const password = useWatch<UserFormValues>({ name: "password" });
  const passwordRepeat = useWatch<UserFormValues>({ name: "passwordRepeat" });
  const { t } = useI18n();

  useEffect(() => {
    if (formState.isSubmitSuccessful) {
      reset();
    }
  }, [formState.isSubmitSuccessful, reset]);

  return (
    <Button disabled={!password || password !== passwordRepeat} type="submit">
      {t("user.submit")}
    </Button>
  );
}

export default function UserPage() {
  const { t } = useI18n();
  const passwordValidation = usePasswordValidation();
  return (
    <Layout container title={t("user.settings")}>
      <Form<UserFormValues>
        model="User"
        onSubmit={async (data) => {
          const result = await client.request<UpdateUserPasswordMutation>(
            updateUserPasswordMutation,
            { data: { password: data.password } },
          );
          if (result.updateCurrentUserPassword?.__typename === "ProblemGroup") {
            return result.updateCurrentUserPassword;
          }
        }}
      >
        <Fieldset className="max-w-96 space-y-4" legend={t("user.settings")}>
          <Input
            name="password"
            type="password"
            validate={passwordValidation}
          />
          <Input name="passwordRepeat" type="password" />
          <PasswordRules />
          <SubmitButton />
        </Fieldset>
      </Form>
    </Layout>
  );
}

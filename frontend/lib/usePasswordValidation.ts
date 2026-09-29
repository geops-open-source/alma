import { isString } from "lodash";
import { useMemo } from "react";

import { useI18n } from "./i18n";

const numberRegex = /[0-9]+/;
const symbolRegex = /[-#!$@£%^&*()_+|~=`{}[\]:";'<>?,./\\ ]+/;
const lowerUpperCaseRegex = /(?=.*[a-z])(?=.*[A-Z])/;

export default function usePasswordValidation() {
  const { t } = useI18n();
  return useMemo(() => {
    return (value: unknown) => {
      if (isString(value)) {
        if (value.length < 12) {
          return t("PasswordRules.length");
        } else if (!symbolRegex.test(value)) {
          return t("PasswordRules.symbols");
        } else if (!numberRegex.test(value)) {
          return t("PasswordRules.numbers");
        } else if (!lowerUpperCaseRegex.test(value)) {
          return t("PasswordRules.lowerUpperCase");
        }
      }
    };
  }, [t]);
}

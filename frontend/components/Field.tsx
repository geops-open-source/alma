import * as Headless from "@headlessui/react";
import { has } from "lodash";
import { useFormContext, useWatch } from "react-hook-form";

import { useValidatedData } from "@/components/Form";
import ValidationPopover from "@/components/ValidationPopover";
import { useI18n } from "@/lib/i18n";
import { useModelContext } from "@/lib/modelContext";
import useSetting from "@/lib/useSetting";

import type { PropsWithChildren } from "react";
import type { FieldError } from "react-hook-form";

type ValidatedDataFieldError =
  | {
      message: string;
      name: string;
      type: "validatedData";
    }
  | { type: "validatedDataEmpty" }
  | { type: "validatedDataSuccess" };

function getErrorTitle(error: FieldError) {
  switch (error.type) {
    case "validate":
      return "Field.errorTitle.VALIDATION.general";
    default:
      return `Field.errorTitle.${error.type}`;
  }
}

function getValidatedDataErrorTitle(error: ValidatedDataFieldError) {
  switch (error.type) {
    case "validatedData":
      return "Field.validatedDataTitle";
    case "validatedDataEmpty":
      return "Field.validatedDataEmptyTitle";
    case "validatedDataSuccess":
      return "Field.validatedDataSuccessTitle";
    default:
      return "Field.validationTitle";
  }
}

function getValidatedDataErrorStatus(error: ValidatedDataFieldError) {
  switch (error.type) {
    case "validatedData":
      return "info";
    case "validatedDataEmpty":
      return "info";
    case "validatedDataSuccess":
      return "success";
    default:
      return "error";
  }
}

function ValidationErrorContent({
  error,
  label,
}: {
  error: FieldError;
  label?: string;
}) {
  const { t } = useI18n();

  if (error.type === "required") {
    return (
      <>
        {t("Field.requiredStart")}
        <strong>{label}</strong>
        {t("Field.requiredEnd")}
      </>
    );
  } else if (error.type === "validate") {
    return (
      t(error.message ?? "Field.errorContent.VALIDATION.general") ||
      error.message
    );
  }

  return t(`Field.errorContent.${error.type}`);
}

function ValidatedDataErrorContent({
  error,
}: {
  error: ValidatedDataFieldError;
}) {
  const { setValue } = useFormContext();
  const closeValidationPopover = Headless.useClose();
  const { pluralRules, t } = useI18n();

  if (error.type === "validatedDataEmpty") {
    return (
      <p data-test="Field-validatedDataEmpty">
        {t("Field.validatedDataEmptyDescription")}
      </p>
    );
  } else if (
    (error.type === "validatedData" || error.type === "validatedDataSuccess") &&
    "name" in error
  ) {
    let data: unknown[] = [];
    try {
      data = JSON.parse(error.message) as unknown[];
    } catch {
      // ignore JSON parse errors
    }
    const pluralRule = pluralRules.select(data.length);
    return (
      <>
        <p>
          {t(
            error.type === "validatedData"
              ? `Field.validatedDataDescription.${pluralRule}`
              : `Field.validatedDataSuccessDescription.${pluralRule}`,
          )}
        </p>
        <ul
          className={`mt-1 ${data.length > 1 ? "ml-4 list-disc space-y-1" : ""}`}
        >
          {data.map((item) => {
            let key;
            let values: [string, string][] = [];
            if (typeof item === "string") {
              key = item;
              values = [[error.name, item]];
            } else if (has(item, "ort") && has(item, "postleitzahl")) {
              // needed for Ort and Postleitzahl validation
              key = `${item.postleitzahl as string} ${item.ort as string}`;
              values = [
                ["ort", item.ort],
                ["postleitzahl", item.postleitzahl as string],
              ];
            } else if (has(item, "displayValue")) {
              // needed for Gemeinde and Kanton validation
              key = item.displayValue;
              const prefix = error.name.split(".").at(0)!;
              values = Object.entries(item)
                .filter(([k]) => {
                  return k !== "__typename";
                })
                .map(([k, v]) => {
                  return [`${prefix}.${k}`, v];
                });
            }
            return (
              <li key={key}>
                <button
                  className="hover:text-blue-8 underline"
                  onClick={() => {
                    closeValidationPopover();
                    values.forEach(([name, value]) => {
                      setValue(name, value, {
                        shouldDirty: true,
                        shouldTouch: true,
                        shouldValidate: true,
                      });
                    });
                  }}
                  type="button"
                >
                  {key?.startsWith("code:") ? t(key) : key}
                </button>
              </li>
            );
          })}
        </ul>
      </>
    );
  }
  return null;
}

function SimpleField({
  children,
  className = "",
  error,
  hideLabel,
  inline,
  label,
  validatedDataError,
  ...props
}: PropsWithChildren<{
  className?: string;
  error?: FieldError;
  hideLabel?: boolean;
  inline?: boolean;
  label: string;
  space?: number;
  validatedDataError?: ValidatedDataFieldError;
}>) {
  const { t } = useI18n();
  const spaceX = `space-x-${props.space ?? "1"}`;
  return (
    <Headless.Field
      className={`flex ${inline ? "items-center" : "flex-col space-y-1.5"} ${spaceX} ${className}`}
      {...props}
    >
      {inline ? children : null}
      {hideLabel ? (
        <div />
      ) : (
        <div className="flex space-x-2">
          <Headless.Label className="text-gray-7 truncate text-xs font-medium text-wrap">
            {label}
          </Headless.Label>
          {error ? (
            <ValidationPopover
              className="-mt-0.5 h-0"
              status="error"
              title={t(getErrorTitle(error))}
            >
              <ValidationErrorContent error={error} label={label} />
            </ValidationPopover>
          ) : null}
          {validatedDataError ? (
            <ValidationPopover
              className="-mt-0.5 h-0 pl-1"
              status={getValidatedDataErrorStatus(validatedDataError)}
              title={t(getValidatedDataErrorTitle(validatedDataError))}
            >
              <ValidatedDataErrorContent error={validatedDataError} />
            </ValidationPopover>
          ) : null}
        </div>
      )}
      {inline ? null : children}
    </Headless.Field>
  );
}

// contains field names that are allowed to be empty
// without showing a validation error
const fieldNamesValidateEmpty = ["flugplatz"];

function HideableField({
  children,
  name,
  ...props
}: PropsWithChildren<{
  error?: FieldError;
  label?: string;
  name: string;
}>) {
  const value = useWatch({ name }) as string;
  const { formState } = useFormContext();
  const model = useModelContext();
  const { t } = useI18n();
  const { validatedData } = useValidatedData();
  const fieldName = name.split(".").pop();
  const hidden =
    useSetting(`ui.fields.${model}.${fieldName}.hidden`, false).at(0) === true;
  const label = props.label ?? t(`fields.${model}.${fieldName}`);
  const validatedKey = name.split(".").at(0)!;

  let validatedDataError: undefined | ValidatedDataFieldError;
  if (validatedData && validatedKey in validatedData && !formState.disabled) {
    const data = validatedData[validatedKey];
    if (data?.length === 0) {
      if (fieldNamesValidateEmpty.includes(fieldName!)) {
        validatedDataError = value
          ? { type: "validatedDataEmpty" }
          : { type: "validatedDataSuccess" };
      } else {
        validatedDataError = { type: "validatedDataEmpty" };
      }
    } else if (data) {
      const isValid = data.some((item) => {
        if (typeof item === "string") {
          return item === value;
        } else if (has(item, "displayValue")) {
          return item.displayValue === value;
        }
      });
      if (validatedKey === "ort" || validatedKey === "postleitzahl") {
        validatedDataError = {
          message: JSON.stringify(
            validatedData.ort.map((ort, index) => {
              return {
                ort,
                postleitzahl: validatedData.postleitzahl[index],
              };
            }),
          ),
          name,
          type: isValid ? "validatedDataSuccess" : "validatedData",
        };
      } else {
        validatedDataError = {
          message: JSON.stringify(data),
          name,
          type: isValid ? "validatedDataSuccess" : "validatedData",
        };
      }
    }
  }

  return hidden ? null : (
    <SimpleField
      label={label}
      validatedDataError={validatedDataError}
      {...props}
    >
      {children}
    </SimpleField>
  );
}

function Field({
  children,
  ...props
}: PropsWithChildren<
  {
    className?: string;
    error?: FieldError;
    hideLabel?: boolean;
    inline?: boolean;
    space?: number;
  } & ({ label: string; name: string } | { label: string } | { name: string })
>) {
  return "name" in props ? (
    <HideableField {...props}>{children}</HideableField>
  ) : (
    <SimpleField {...props}>{children}</SimpleField>
  );
}

export default Field;

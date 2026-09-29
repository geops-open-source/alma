import {
  Combobox,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from "@headlessui/react";
import { gql } from "graphql-request";
import { router } from "next/client";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Controller, useFormContext } from "react-hook-form";
import useSWR from "swr";

import Button from "@/components/Button";
import Form from "@/components/Form";
import ResetIcon from "@/components/icons/ResetIcon";
import SearchIcon from "@/components/icons/SearchIcon";
import SearchLayout from "@/components/SearchLayout";
import SearchFieldSelector from "@/components/SearchLayout/SearchFieldSelector";
import fonts from "@/lib/fonts";
import { useI18n } from "@/lib/i18n";

import type {
  AutoSuggestItem,
  AutosuggestSearchQuery,
  Problem,
  SortItem,
  ValidateSearchQuery,
} from "@/lib/graphql";

interface AdvancedSearchValues {
  advanced: boolean;
  advancedQuery?: string;
  page?: number;
  perPage?: number;
  sortby?: SortItem[];
}

function ValidIcon() {
  return (
    <svg fill="none" height="20" width="20" xmlns="http://www.w3.org/2000/svg">
      <path
        d="m6.25 10 2.5 2.5 5-5m4.583 2.5a8.333 8.333 0 1 1-16.667 0 8.333 8.333 0 0 1 16.667 0Z"
        stroke="#079455"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.667"
      />
    </svg>
  );
}

function ListIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 20 20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M17.5 10h-10m10-5h-10m10 10h-10m-3.333-5A.833.833 0 1 1 2.5 10a.833.833 0 0 1 1.667 0Zm0-5A.833.833 0 1 1 2.5 5a.833.833 0 0 1 1.667 0Zm0 10A.833.833 0 1 1 2.5 15a.833.833 0 0 1 1.667 0Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function ListIconLarge() {
  return (
    <svg fill="none" height="48" width="48" xmlns="http://www.w3.org/2000/svg">
      <path d="M0 24a24 24 0 1 1 48 0 24 24 0 0 1-48 0Z" fill="#E0F2FE" />
      <path
        d="M33 24H21m12-6H21m12 12H21m-4-6a1 1 0 1 1-2 0 1 1 0 0 1 2 0Zm0-6a1 1 0 1 1-2 0 1 1 0 0 1 2 0Zm0 12a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"
        stroke="#0086C9"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

const queryValidateSearch = gql`
  query ValidateSearch($query: String!) {
    validateSearchQuery(query: $query) {
      message
      problemCode
      field
      messageCode
      messageArgs
    }
  }
`;

const queryAutosuggestSearch = gql`
  query AutosuggestSearch($input: String!, $pos: Int!, $lang: Language!) {
    autosuggestSearchQuery(input: $input, pos: $pos, lang: $lang) {
      category
      fieldType
      type
      value
    }
  }
`;

const advancedSearchEmptyValues: AdvancedSearchValues = {
  advanced: true,
  advancedQuery: "",
  page: 1,
  perPage: undefined,
};

function AdvancedSearchForm({
  onReset,
  values,
}: {
  onReset: () => void;
  values?: AdvancedSearchValues;
}) {
  const { activeLocale, t } = useI18n();
  const { control, formState, reset, setValue } = useFormContext();
  const [fullSearchQuery, setFullSearchQuery] = useState(
    values?.advancedQuery ?? "",
  );
  const END_OF_INPUT = 1e6;
  const [cursorPosition, setCursorPosition] = useState(END_OF_INPUT);
  const [autocompleteValues, setAutocompleteValues] = useState<
    AutoSuggestItem[]
  >([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const isDirty = Object.keys(formState.dirtyFields).length > 0;

  const {
    data: autoSuggest,
    error: autoSuggestError,
    isLoading: autoSuggestLoading,
  } = useSWR<AutosuggestSearchQuery, Problem>(
    // currently, autosuggest should only happen at end of input string
    cursorPosition >= fullSearchQuery.length && [
      queryAutosuggestSearch,
      {
        input: fullSearchQuery,
        lang: activeLocale.toUpperCase(),
        pos: cursorPosition,
      },
    ],
  );

  const { data: validatedData, isLoading: validationLoading } =
    useSWR<ValidateSearchQuery>(
      fullSearchQuery && [
        queryValidateSearch,
        {
          query: fullSearchQuery,
        },
      ],
    );

  const disableSubmit =
    !isDirty ||
    !!validatedData?.validateSearchQuery ||
    autoSuggestLoading ||
    validationLoading;

  useEffect(() => {
    if (autoSuggestLoading) {
      return;
    }
    if (autoSuggestError) {
      setAutocompleteValues([]);
      return;
    }
    if (autoSuggest === undefined) {
      setAutocompleteValues([]);
      return;
    }
    const matches = autoSuggest.autosuggestSearchQuery;
    setAutocompleteValues(matches);
  }, [autoSuggest, autoSuggestError, autoSuggestLoading]);

  useEffect(() => {
    if (!values) {
      return;
    }
    setFullSearchQuery(values.advancedQuery ?? "");
    reset(values);
  }, [reset, values]);

  function reopenComboboxWithKey() {
    if (inputRef.current) {
      const event = new KeyboardEvent("keydown", {
        bubbles: true,
        cancelable: true,
        key: "ArrowDown",
      });
      inputRef.current.dispatchEvent(event);
    }
  }

  useEffect(() => {
    if (!inputRef.current) {
      return;
    }
    inputRef.current.style.height = "auto";
    inputRef.current.style.height = `${inputRef.current.scrollHeight + 2}px`;
  }, [fullSearchQuery]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter") {
      const highlightedOption = document.querySelector(
        "div#autosuggest-options",
      );
      if (!highlightedOption?.hasChildNodes()) {
        e.preventDefault();
        e.stopPropagation();
        if (disableSubmit) {
          return;
        }
        const form = e.currentTarget.closest("form");
        if (!form) {
          return;
        }
        form.dispatchEvent(
          new Event("submit", { bubbles: true, cancelable: true }),
        );
        return;
      }
    }

    if (e.key === "ArrowLeft") {
      setCursorPosition(cursorPosition > 0 ? cursorPosition - 1 : 0);
      return;
    }
    if (e.key === "ArrowRight") {
      setCursorPosition(
        cursorPosition < e.currentTarget.value.length
          ? cursorPosition + 1
          : e.currentTarget.value.length,
      );
      return;
    }
    if (e.shiftKey && e.key === "Home") {
      e.preventDefault();
      e.stopPropagation();
      inputRef.current?.setSelectionRange(
        0,
        inputRef.current?.selectionStart ?? 0,
        "backward",
      );
      setCursorPosition(0);
      return;
    }
    if (e.key === "Home") {
      e.preventDefault();
      e.stopPropagation();
      inputRef.current?.setSelectionRange(0, 0);
      setCursorPosition(0);
      return;
    }
    if (e.shiftKey && e.key === "End") {
      e.preventDefault();
      e.stopPropagation();
      inputRef.current?.setSelectionRange(
        inputRef.current?.selectionStart ?? 0,
        fullSearchQuery?.length ?? END_OF_INPUT,
        "forward",
      );
      setCursorPosition(END_OF_INPUT);
      return;
    }
    if (e.key === "End") {
      e.preventDefault();
      e.stopPropagation();
      const pos = fullSearchQuery?.length ?? END_OF_INPUT;
      inputRef.current?.setSelectionRange(pos, pos);
      setCursorPosition(END_OF_INPUT);
      return;
    }
  }

  function handleComboboxChange(value: AutoSuggestItem | null | string) {
    if (!inputRef.current) {
      return;
    }
    if (!value) {
      return;
    }

    const autocompleteField = value as AutoSuggestItem;
    if (!autocompleteField) {
      return;
    }

    const autocompleteString = autocompleteField.value;
    let newQuery: string;
    if (autocompleteString.startsWith('"')) {
      // replace existing string starting from the last found quote
      const lastQuoteIndex = fullSearchQuery.lastIndexOf(
        '"',
        cursorPosition - 1,
      );
      if (lastQuoteIndex !== -1) {
        newQuery = `${fullSearchQuery.substring(0, lastQuoteIndex)}${autocompleteString}`;
      } else {
        newQuery = `${fullSearchQuery} ${autocompleteString}`;
      }
    } else {
      // replace the last word (determined by open blank space or open bracket)
      const splitIndex = Math.max(
        fullSearchQuery.lastIndexOf(" "),
        fullSearchQuery.lastIndexOf("("),
      );
      newQuery =
        splitIndex !== -1
          ? `${fullSearchQuery.substring(0, splitIndex + 1)}${autocompleteString}`
          : autocompleteString;
    }

    if (
      /[()'"]$/.test(newQuery) ||
      /^(TRUE|FALSE)$/.test(autocompleteField.value) ||
      autocompleteField.type !== "VALUE"
    ) {
      newQuery += " ";
    }

    if (autocompleteField.type === "OPERATOR") {
      if (
        autocompleteField.fieldType === "CODE" ||
        autocompleteField.fieldType === "TEXT"
      ) {
        newQuery += '"';
      }
    }

    setCursorPosition(newQuery.length);
    setFullSearchQuery(newQuery);
    setValue("advancedQuery", newQuery, { shouldDirty: true });

    setTimeout(() => {
      if (!inputRef.current) {
        return;
      }
      inputRef.current.setSelectionRange(newQuery.length, newQuery.length);
      reopenComboboxWithKey();
    });
  }

  return (
    <>
      <div className="relative flex items-center justify-between gap-2">
        <div className="mt-1.5 flex w-full items-center gap-2">
          <Controller
            control={control}
            defaultValue={fullSearchQuery}
            name="advancedQuery"
            render={() => {
              return (
                <Combobox
                  immediate
                  onChange={handleComboboxChange}
                  value={fullSearchQuery}
                >
                  <div className="relative flex w-full">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                      {fullSearchQuery.length > 0 &&
                      validatedData?.validateSearchQuery === null ? (
                        <ValidIcon />
                      ) : (
                        <SearchIcon className="text-gray-6" />
                      )}
                    </div>
                    <ComboboxInput
                      as="textarea"
                      autoComplete="off"
                      className="border-gray-5 focus:border-blue-4 focus:ring-blue-6/25 disabled:bg-gray-2 disabled:text-gray-6 max-h-96 w-full resize-none overflow-y-scroll rounded-lg border px-3 py-2 pl-9 text-xs shadow-xs focus:ring-4 focus:outline-hidden"
                      name="advancedQuery"
                      onChange={(e) => {
                        setFullSearchQuery(e.target.value);
                        setValue("advancedQuery", e.target.value, {
                          shouldDirty: true,
                        });
                        setCursorPosition(
                          e.target.selectionStart ?? END_OF_INPUT,
                        );
                      }}
                      onClick={(e) => {
                        setCursorPosition(e.currentTarget.selectionStart ?? 0);
                      }}
                      onFocus={(e) => {
                        setCursorPosition(e.target.selectionStart ?? 0);
                      }}
                      onKeyDown={handleKeyDown}
                      placeholder={t("search.placeholderAdvanced")}
                      ref={inputRef}
                      rows={1}
                      spellCheck={false}
                      value={fullSearchQuery}
                    />
                  </div>
                  <ComboboxOptions
                    anchor="bottom start"
                    className={`${fonts} border-gray-5 z-30 max-h-96! w-(--input-width) max-w-96! space-y-1 rounded-lg border bg-white py-1 shadow-lg empty:invisible`}
                    id="autosuggest-options"
                  >
                    {autocompleteValues
                      .sort((a, b) => {
                        return a.type === "FIELD_NAME" &&
                          b.type === "FIELD_NAME"
                          ? a.value.localeCompare(b.value)
                          : 0;
                      })
                      .map((suggestion) => {
                        return (
                          <ComboboxOption
                            className="data-focus:bg-blue-1 cursor-pointer rounded-lg px-2 py-2 text-sm hover:bg-blue-100"
                            key={suggestion.value}
                            value={suggestion}
                          >
                            {suggestion.value}
                          </ComboboxOption>
                        );
                      })}
                  </ComboboxOptions>
                </Combobox>
              );
            }}
          />
          <SearchFieldSelector
            className="flex items-center gap-2"
            disabled={
              fullSearchQuery.length > 0 &&
              (autocompleteValues.length < 1 ||
                autocompleteValues[0].type !== "FIELD_NAME")
            }
            icon={<ListIconLarge />}
            onSelect={(selection) => {
              if (typeof selection !== "string") {
                return;
              }
              handleComboboxChange({ type: "FIELD_NAME", value: selection });
              setTimeout(() => {
                inputRef.current?.focus();
              });
            }}
            subtitle={t("search.fieldSelector.subheading")}
            title={t("search.fieldSelector.heading")}
          >
            <ListIcon className="size-4" />
            {t("search.fieldSelector.buttonLabel")}
          </SearchFieldSelector>
        </div>
        <Button
          className="mt-1.5 flex space-x-1.5"
          disabled={disableSubmit}
          type="submit"
        >
          <SearchIcon />
          <span>{t("search.submit")}</span>
        </Button>
        <Button
          className="mt-1.5 flex space-x-1.5"
          disabled={
            !isDirty &&
            JSON.stringify(formState.defaultValues) ===
              JSON.stringify(advancedSearchEmptyValues)
          }
          onClick={() => {
            void reset(advancedSearchEmptyValues, { keepDefaultValues: true });
            onReset();
          }}
          type="button"
        >
          <ResetIcon />
          <span>{t("search.reset")}</span>
        </Button>
      </div>
      <div className="min-h-6 pl-8">
        {formState.errors.advancedQuery ? (
          <span
            className="border-gray-4 bg-red-2 text-gray-7 rounded-full px-2 text-xs"
            data-test="validationMessage"
          >
            {typeof formState.errors.advancedQuery.message === "string" &&
              t(`${formState.errors.advancedQuery.message}.title`)}
          </span>
        ) : (
          validatedData?.validateSearchQuery?.problemCode === "VALIDATION" && (
            <span
              className="border-gray-4 bg-red-2 text-gray-7 rounded-full px-2 text-xs"
              data-test="validationMessage"
            >
              {validatedData.validateSearchQuery.messageCode
                ? t(
                    validatedData.validateSearchQuery.messageCode,
                    validatedData.validateSearchQuery.messageArgs as Record<
                      string,
                      string
                    >,
                  )
                : validatedData.validateSearchQuery.message}
            </span>
          )
        )}
      </div>
    </>
  );
}

export default function AdvancedSearch() {
  const [formValues, setFormValues] = useState<AdvancedSearchValues>();
  const searchParams = useSearchParams();

  useEffect(() => {
    setFormValues({
      advanced: true,
      advancedQuery: searchParams.get("q") ?? "",
      page: searchParams.get("p") ? parseInt(searchParams.get("p") ?? "1") : 1,
      perPage: searchParams.get("perPage")
        ? parseInt(searchParams.get("perPage") ?? "1")
        : undefined,
    });
  }, [searchParams]);

  return (
    <Form
      data-test="advancedSearchForm"
      model="advancedSearch"
      onSubmit={(values: AdvancedSearchValues) => {
        const params = new URLSearchParams(searchParams);
        params.delete("p");
        params.delete("q");
        params.set("q", values.advancedQuery ?? "");
        params.set("advanced", "true");
        localStorage.removeItem("search-params-advanced");
        localStorage.setItem("last-search-mode", "advanced");
        void router.push(`?${params.toString()}`);
        setFormValues({ ...values, advanced: true, page: 1 });
      }}
    >
      <SearchLayout>
        <AdvancedSearchForm
          onReset={() => {
            void router.push(``);
            localStorage.removeItem("search-params-advanced");
            setFormValues(advancedSearchEmptyValues);
          }}
          values={formValues}
        />
      </SearchLayout>
    </Form>
  );
}

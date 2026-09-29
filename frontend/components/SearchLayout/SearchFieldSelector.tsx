import { Field, Checkbox as HeadlessCheckbox, Label } from "@headlessui/react";
import { gql } from "graphql-request";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useFormContext } from "react-hook-form";
import useSWRImmutable from "swr/immutable";

import Button from "@/components/Button";
import Checkbox from "@/components/Checkbox";
import Form from "@/components/Form";
import CheckboxIcon from "@/components/icons/CheckboxIcon";
import ChevronIcon from "@/components/icons/ChevronIcon";
import NoResultsIcon from "@/components/icons/NoResultsIcon";
import SearchIcon from "@/components/icons/SearchIcon";
import Input from "@/components/Input";
import { useI18n } from "@/lib/i18n";

import SidebarDialog from "./SidebarDialog";

import type {
  SearchField,
  SearchFieldCategory,
  SearchFieldNamesQuery,
} from "@/lib/graphql";

const querySearchFields = gql`
  query SearchFieldNames($lang: Language!) {
    searchFieldNames(lang: $lang) {
      category
      field
      name
    }
  }
`;

function includesNormalized(str: string, subStr: string): boolean {
  const normalize = (s: string) => {
    return s
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  };
  return normalize(str).includes(normalize(subStr));
}

function CategoryPanel({
  alwaysSelectedFields = [],
  className,
  items,
  multiSelect = false,
  onSelect,
  title,
}: {
  alwaysSelectedFields: SearchField[];
  className?: string;
  items: SearchField[];
  multiSelect?: boolean;
  onSelect?: (field: SearchField[] | string) => void;
  title: string;
}) {
  const [isOpen, setIsOpen] = useState(true);
  const { setValue, watch } = useFormContext();
  const itemsCheckValues = watch(items) as SearchField[];
  const { activeLocale } = useI18n();
  const { data: searchFields } = useSWRImmutable<SearchFieldNamesQuery>([
    querySearchFields,
    { lang: activeLocale.toUpperCase() },
  ]);

  const categoryChecked = useMemo(() => {
    return itemsCheckValues.every((v) => {
      return v;
    });
  }, [itemsCheckValues]);

  const categoryIndeterminate = useMemo(() => {
    return (
      itemsCheckValues.some((v) => {
        return v;
      }) && !categoryChecked
    );
  }, [categoryChecked, itemsCheckValues]);

  const getNameByField = useCallback(
    (field: SearchField) => {
      return (
        searchFields?.searchFieldNames.find((f) => {
          return f.field === field;
        })?.name ?? "?"
      );
    },
    [searchFields],
  );

  return (
    <div className={`${className} px-4`}>
      {multiSelect ? (
        <div
          className={`${isOpen && "border-b-gray-4 border-b"} flex w-full items-center justify-between text-left font-medium hover:cursor-pointer`}
        >
          <Field className="flex items-center gap-2 py-3">
            <HeadlessCheckbox
              checked={categoryChecked}
              className={`group border-gray-5 data-checked:border-blue-6 data-checked:bg-blue-6 data-indeterminate:border-blue-6 data-indeterminate:bg-blue-6 block size-4 shrink-0 rounded-sm border bg-white`}
              indeterminate={categoryIndeterminate}
              name={`category_${title}`}
              onChange={(value) => {
                items.forEach((item) => {
                  if (alwaysSelectedFields.includes(item)) {
                    return;
                  }
                  setValue(item, value);
                });
              }}
            >
              <CheckboxIcon
                className="size-full text-white"
                indeterminate={categoryIndeterminate}
              />
            </HeadlessCheckbox>
            <Label>{title}</Label>
          </Field>
          <button
            className="-mr-3 p-3"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setIsOpen(!isOpen);
            }}
          >
            <ChevronIcon className={`${isOpen ? "rotate-0" : "rotate-180"}`} />
          </button>
        </div>
      ) : (
        <button
          className={`${isOpen && "border-b-gray-4 border-b"} flex w-full justify-between py-3 text-left font-medium hover:cursor-pointer`}
          onClick={() => {
            setIsOpen(!isOpen);
          }}
          type="button"
        >
          {title}
          <ChevronIcon
            className={`${isOpen ? "rotate-0" : "rotate-180"} mt-2`}
          />
        </button>
      )}
      <div
        className={`${isOpen ? "h-auto py-2" : "h-0 overflow-y-clip"} transition-all`}
      >
        {items.map((field) => {
          if (multiSelect) {
            return (
              <Checkbox
                className="my-1"
                disabled={alwaysSelectedFields.includes(field)}
                key={field}
                label={getNameByField(field)}
                name={field}
                space={2}
              />
            );
          }
          return (
            <button
              className="text-blue-7 hover:bg-blue-1 block w-full py-1 text-left hover:cursor-pointer"
              key={field}
              onClick={() => {
                if (onSelect) {
                  onSelect(getNameByField(field));
                }
              }}
              type="button"
            >
              {getNameByField(field)}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function FieldSelectorFormBody({
  alwaysSelectedFields = [],
  initialSelection,
  multiSelect,
  onClose,
  onSelect,
}: {
  alwaysSelectedFields: SearchField[];
  initialSelection: SearchField[];
  multiSelect: boolean;
  onClose: () => void;
  onSelect: (field: SearchField[] | string) => void;
}) {
  const { activeLocale, t } = useI18n();
  const { reset, setValue, watch } = useFormContext();
  const { data: searchFields } = useSWRImmutable<SearchFieldNamesQuery>([
    querySearchFields,
    { lang: activeLocale.toUpperCase() },
  ]);
  const filterValue = watch("fieldFilter", "") as string;

  useEffect(() => {
    const selection = Array.from(
      new Set([...(initialSelection ?? []), ...alwaysSelectedFields]),
    );
    if (selection.length === 0) {
      return;
    }
    const selectedState = selection.reduce(
      (acc, field) => {
        acc[field] = true;
        return acc;
      },
      {} as Record<string, boolean>,
    );
    reset(selectedState);
  }, [alwaysSelectedFields, initialSelection, reset]);

  const filteredSearchFields = useMemo(() => {
    const allFields = searchFields?.searchFieldNames ?? [];
    if (!filterValue) {
      return allFields;
    }
    const searchValue = filterValue.toLowerCase();
    return allFields.filter((field) => {
      return (
        includesNormalized(field.name, searchValue) ||
        includesNormalized(
          t(`search.categories.${field.category.toLowerCase()}`),
          searchValue,
        )
      );
    });
  }, [filterValue, searchFields?.searchFieldNames, t]);

  return (
    <>
      <Input
        className="ml-1 py-4"
        icon={<SearchIcon className="text-gray-6" />}
        name="fieldFilter"
        placeholder={t("search.fieldSelector.placeholder")}
      />
      <div className="overflow-y-scroll">
        {Object.entries(
          filteredSearchFields.reduce(
            (groups, item) => {
              const category = item.category ?? "default";
              if (!groups[category]) {
                groups[category] = [];
              }
              groups[category].push(item.field);
              return groups;
            },
            {} as Record<SearchFieldCategory, SearchField[]>,
          ) ?? {},
        ).map(([category, items]) => {
          return (
            <CategoryPanel
              alwaysSelectedFields={alwaysSelectedFields}
              className="border-gray-4 bg-gray-2 mb-4 overflow-x-hidden rounded-lg border text-sm"
              items={items}
              key={category}
              multiSelect={multiSelect}
              onSelect={onSelect}
              title={t(`search.categories.${category.toLowerCase()}`)}
            />
          );
        })}
        {filteredSearchFields.length < 1 && (
          <div className="text-blue-8 mx-auto flex justify-center gap-2 bg-white py-8">
            <NoResultsIcon className="text-blue-7 shrink-0" />
            <div className="font-semibold">
              {t("search.fieldSelector.noMatches")}
            </div>
          </div>
        )}
      </div>
      {multiSelect && (
        <div className="border-t-gray-4 flex gap-2 border-t pt-4">
          <Button className="basis-1/2" onClick={onClose} outline>
            {t("search.columnSelector.cancel")}
          </Button>
          <Button
            className="basis-1/2"
            onClick={() => {
              setValue("fieldFilter", "");
            }}
            type="submit"
          >
            {t("search.columnSelector.submit")}
          </Button>
        </div>
      )}
    </>
  );
}

export default function SearchFieldSelector({
  alwaysSelectedFields = [],
  children,
  className,
  disabled,
  icon,
  initialSelection,
  multiSelect = false,
  onSelect,
  subtitle,
  title,
}: React.PropsWithChildren<{
  alwaysSelectedFields?: SearchField[];
  className?: string;
  disabled?: boolean;
  icon: React.ReactNode;
  initialSelection?: SearchField[];
  multiSelect?: boolean;
  onSelect: (fields: SearchField[] | string) => void;
  subtitle?: string;
  title: string;
}>) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <>
      <SidebarDialog
        icon={icon}
        isOpen={isOpen}
        onClose={() => {
          setIsOpen(false);
        }}
        subtitle={subtitle}
        title={title}
      >
        <Form
          className="flex h-full flex-col overflow-y-hidden"
          model="searchFields"
          onSubmit={(values) => {
            const selectedFields = Object.keys(values).filter((key) => {
              return values[key];
            }) as SearchField[];
            setIsOpen(false);
            onSelect(selectedFields);
          }}
        >
          <FieldSelectorFormBody
            alwaysSelectedFields={alwaysSelectedFields}
            initialSelection={initialSelection ?? []}
            multiSelect={multiSelect}
            onClose={() => {
              setIsOpen(false);
            }}
            onSelect={(f) => {
              onSelect(f);
              setIsOpen(false);
            }}
          />
        </Form>
      </SidebarDialog>
      <Button
        className={className}
        data-test="columnSelector"
        disabled={disabled}
        onClick={() => {
          setIsOpen(true);
        }}
        outline
      >
        {children}
      </Button>
    </>
  );
}

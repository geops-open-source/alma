import * as Headless from "@headlessui/react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useFormContext, useWatch } from "react-hook-form";

import { anchor } from "@/components/Combobox";
import Field from "@/components/Field";
import CheckIcon from "@/components/icons/CheckIcon";
import ChevronIcon from "@/components/icons/ChevronIcon";
import fonts from "@/lib/fonts";
import { useI18n } from "@/lib/i18n";
import { useModelContext } from "@/lib/modelContext";

interface Option {
  categoryValues?: string[];
  label: string;
  originalSortIndex?: number;
  value: boolean | null | number | string;
}

export default function MultiComboBox({
  categories,
  hideLabel = true,
  name,
  options = [],
  sortByValue = true,
  ...props
}: {
  categories?: { label: string; values: string[] }[];
  hideLabel?: boolean;
  name: string;
  options?: Option[];
  sortByValue?: boolean;
}) {
  const model = useModelContext();
  const { t } = useI18n();
  const fieldname = name.split(".").pop();
  const { register, setValue } = useFormContext();
  const selectedValues = useWatch<Record<string, Option[]>>({ name });

  const makeDisplayValue = useCallback(() => {
    if (selectedValues?.length === 1) {
      const selected = options.find((o) => {
        return o.value === selectedValues[0].value;
      });
      return selected?.label ?? "?";
    }
    return `${t(`fields.${model}.${fieldname}`)} (${selectedValues?.length || 0})`;
  }, [fieldname, model, options, selectedValues, t]);

  const [displayValue, setDisplayValue] = useState<string>(makeDisplayValue());
  const [query, setQuery] = useState("");
  const { onChange } = register(name);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setDisplayValue(makeDisplayValue());
  }, [makeDisplayValue]);

  const filteredOptions = useMemo(() => {
    return query === ""
      ? options
      : options.filter((option) => {
          return option.label.toLowerCase().includes(query.toLowerCase());
        });
  }, [options, query]);

  const selectedOptions = useMemo(() => {
    return options.filter((o) => {
      return selectedValues?.some((s) => {
        return s.value === o.value;
      });
    });
  }, [options, selectedValues]);

  const sortedOptions = useMemo(() => {
    const sortedOptionsWithoutCategories = filteredOptions.sort((a, b) => {
      const aSelected = selectedOptions.includes(a);
      const bSelected = selectedOptions.includes(b);
      if (aSelected !== bSelected) {
        return aSelected ? -1 : 1;
      }
      if (!sortByValue) {
        return (a.originalSortIndex ?? 0) - (b.originalSortIndex ?? 0);
      }
      if (!a.value || !b.value) {
        return 0;
      }
      return a.value.toString().localeCompare(b.value.toString());
    });

    if (categories) {
      const sortedOptionsWithCategories: Option[] = [];
      categories.forEach((category) => {
        sortedOptionsWithCategories.push({
          categoryValues: category.values,
          label: category.label,
          value: category.label,
        });
        sortedOptionsWithCategories.push(
          ...sortedOptionsWithoutCategories.filter((o) => {
            if (o.value) {
              return category.values.includes(o.value.toString());
            }
            return false;
          }),
        );
      });
      return sortedOptionsWithCategories;
    }
    return sortedOptionsWithoutCategories;
  }, [categories, filteredOptions, selectedOptions, sortByValue]);

  const getCategoryValues = useCallback(
    ({ values }: { values: string[] }) => {
      return options.filter((o) => {
        if (typeof o.value === "string") {
          return values.includes(o.value);
        }
        return false;
      });
    },
    [options],
  );

  const areAllSelected = useCallback(
    ({ values }: { values: string[] }) => {
      if (!selectedValues) {
        return false;
      }
      return getCategoryValues({ values }).every((v) => {
        return selectedValues.some((s) => {
          return s.value === v.value;
        });
      });
    },
    [getCategoryValues, selectedValues],
  );

  const handleCategoryClick = useCallback(
    ({ values }: { values: string[] }) => {
      const categoryValues = getCategoryValues({ values });
      let newSelectedValues: Option[];
      if (areAllSelected({ values })) {
        newSelectedValues = selectedValues?.filter((s) => {
          return categoryValues.every((v) => {
            return s.value !== v.value;
          });
        });
      } else {
        newSelectedValues = selectedValues
          ? [
              ...selectedValues,
              ...categoryValues.filter((v) => {
                return selectedValues.every((s) => {
                  return s.value !== v.value;
                });
              }),
            ]
          : categoryValues;
      }
      setValue(name, newSelectedValues, { shouldDirty: true });
    },
    [areAllSelected, getCategoryValues, name, selectedValues, setValue],
  );

  return (
    <Field {...(hideLabel ? { label: "" } : {})} name={name} {...props}>
      <Headless.Combobox
        multiple={true}
        onChange={(value: Option[]) => {
          const clickedCaterory = value.find((v) => {
            return v.categoryValues;
          });
          if (clickedCaterory?.categoryValues) {
            handleCategoryClick({ values: clickedCaterory.categoryValues });
            return;
          }
          void onChange({ target: { name, value: value } });
        }}
        onClose={() => {
          setQuery("");
          setDisplayValue(makeDisplayValue);
        }}
        value={selectedOptions}
        virtual={{ options: sortedOptions }}
      >
        <div className="relative">
          <Headless.ComboboxInput
            className="border-gray-5 focus:border-blue-4 focus:ring-blue-6/25 disabled:bg-gray-2 disabled:text-gray-6 w-full truncate rounded-lg border py-2 pr-6 pl-3 text-xs shadow-xs focus:ring-4 focus:outline-hidden"
            displayValue={() => {
              return displayValue;
            }}
            name={name}
            onBlur={() => {
              return setDisplayValue(makeDisplayValue);
            }}
            onChange={(event) => {
              return setQuery(event.target.value);
            }}
            onFocus={() => {
              return setDisplayValue("");
            }}
          />
          <Headless.ComboboxButton className="group absolute inset-y-0 right-0 px-2.5">
            <ChevronIcon className="text-gray-6 rotate-180 transition-transform group-data-active:rotate-0" />
          </Headless.ComboboxButton>
        </div>
        <Headless.ComboboxOptions
          anchor={anchor}
          className={`${fonts} border-gray-5 z-30 min-w-xs rounded-lg border bg-white p-0.5 shadow-lg`}
        >
          {({ option }: { option: Option }) => {
            return (
              <Headless.ComboboxOption
                className={`group data-focus:bg-gray-2 data-selected:bg-blue-1 flex w-full cursor-pointer items-center overflow-x-hidden rounded-md border-2 border-white py-2.5 pr-7 pl-2 font-medium ${option.categoryValues ? "text-gray-6 before:border-t-gray-4 text-xs font-semibold uppercase before:absolute before:top-0 before:left-0 before:w-full before:border-t before:content-[''] first-of-type:before:border-t-0" : "text-gray-9 text-sm"} ${option.categoryValues && areAllSelected({ values: option.categoryValues }) && "bg-blue-1"}`}
                value={option}
              >
                {option.label}
                <CheckIcon className="text-blue-6 absolute right-1 hidden size-6 rounded-full p-0.5 group-data-selected:block" />
              </Headless.ComboboxOption>
            );
          }}
        </Headless.ComboboxOptions>
      </Headless.Combobox>
    </Field>
  );
}

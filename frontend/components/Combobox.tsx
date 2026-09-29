import * as Headless from "@headlessui/react";
import { useMemo, useState } from "react";
import { useFormContext, useWatch } from "react-hook-form";

import Field from "@/components/Field";
import CheckIcon from "@/components/icons/CheckIcon";
import ChevronIcon from "@/components/icons/ChevronIcon";
import fonts from "@/lib/fonts";

export const anchor: Headless.ComboboxOptionsProps["anchor"] = {
  gap: "8px",
  padding: "32px",
  to: "bottom start",
};

interface Option {
  disabled?: boolean;
  label: string;
  value: null | string;
}

export default function Combobox({
  disabled,
  name,
  options = [],
  ...props
}: {
  className?: string;
  disabled?: boolean;
  name: string;
  options?: Option[];
}) {
  const { formState, register } = useFormContext();
  const [query, setQuery] = useState("");
  const { onChange } = register(name);
  const selectedValue = useWatch({ name }) as Option["value"];

  const filteredOptions = useMemo(() => {
    return query === ""
      ? options
      : options.filter((option) => {
          return option.label.toLowerCase().includes(query.toLowerCase());
        });
  }, [options, query]);

  const selectedOption = useMemo(() => {
    return options.find((o) => {
      return o.value === (selectedValue ?? "");
    });
  }, [options, selectedValue]);

  return (
    <Field name={name} {...props}>
      <Headless.Combobox
        disabled={disabled ?? formState.disabled}
        onChange={(option) => {
          if (option) {
            void onChange({ target: { name, value: option.value } });
          }
        }}
        onClose={() => {
          return setQuery("");
        }}
        value={selectedOption}
        virtual={{ options: filteredOptions }}
      >
        <div className="relative">
          <Headless.ComboboxInput
            aria-label="Assignee"
            className="border-gray-5 focus:border-blue-4 focus:ring-blue-6/25 disabled:bg-gray-2 disabled:text-gray-6 w-full rounded-lg border bg-white px-3 py-2 text-xs shadow-xs focus:ring-4 focus:outline-hidden"
            displayValue={(option: Option) => {
              return option?.label;
            }}
            name={name}
            onChange={(event) => {
              return setQuery(event.target.value);
            }}
          />
          <Headless.ComboboxButton className="group absolute inset-y-0 right-0 px-2.5">
            <ChevronIcon className="text-gray-6 rotate-180 transition-transform group-data-active:rotate-0" />
          </Headless.ComboboxButton>
        </div>
        <Headless.ComboboxOptions
          anchor={anchor}
          className={`${fonts} border-gray-5 z-30 w-(--input-width) space-y-1 rounded-lg border bg-white p-1 shadow-lg`}
        >
          {({ option }: { option: Option }) => {
            return (
              <Headless.ComboboxOption
                className="group text-gray-7 data-focus:bg-gray-2 data-selected:bg-gray-2 data-focus:text-gray-8 data-selected:text-gray-8 flex w-full cursor-pointer items-center justify-between rounded-md p-2.5 pl-2 text-sm font-medium data-disabled:hidden"
                disabled={option.disabled}
                value={option}
              >
                {option.label}
                <CheckIcon className="text-blue-6 hidden group-data-selected:block" />
              </Headless.ComboboxOption>
            );
          }}
        </Headless.ComboboxOptions>
      </Headless.Combobox>
    </Field>
  );
}

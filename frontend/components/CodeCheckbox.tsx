import { useFormContext, useWatch } from "react-hook-form";

import useCodeOptions, { type Props } from "@/lib/useCodeOptions";

import Checkbox from "./Checkbox";
import Field from "./Field";

export default function CodeCheckbox({
  name,
}: { className?: string; disabled?: boolean } & Props) {
  const options = useCodeOptions({ name, required: true });
  const { setValue } = useFormContext();
  const selectedValues = useWatch<Record<string, null | string[]>>({ name });

  if (!options?.length) {
    // ALMABASE-674: Do not display label if no options available
    return null;
  }

  return (
    <Field name={name}>
      <div className="mt-2 flex flex-wrap gap-4">
        {options.map(({ label, value }) => {
          return (
            <Checkbox
              checked={selectedValues?.includes(value ?? "") ?? false}
              key={value}
              label={label}
              onChange={(checked) => {
                const filtered =
                  selectedValues?.filter((v) => {
                    return v !== value;
                  }) ?? [];
                setValue(name, checked ? [...filtered, value] : filtered, {
                  shouldDirty: true,
                });
              }}
            />
          );
        })}
      </div>
    </Field>
  );
}

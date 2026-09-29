import { Field, Label, Switch } from "@headlessui/react";

export default function AlmaSwitch({
  checked,
  className,
  label,
  onChange,
}: {
  checked: boolean;
  className?: string;
  label: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <Field className={`flex items-center gap-2 ${className}`}>
      <Switch
        checked={checked}
        className="group bg-gray-5 data-checked:bg-blue-4 inline-flex h-5 w-10 items-center rounded-full transition"
        onChange={onChange}
      >
        <span className="size-4 translate-x-0.5 rounded-full bg-white transition group-data-checked:translate-x-5.5" />
      </Switch>
      <Label className="cursor-pointer text-sm">{label}</Label>
    </Field>
  );
}

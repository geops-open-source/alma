import useCodeOptions, { type Props as CodeProps } from "@/lib/useCodeOptions";

import Listbox, { type Props as ListboxProps } from "./Listbox";

export default function CodeListbox({
  multiple,
  name,
  ...props
}: CodeProps & ListboxProps) {
  return (
    <Listbox
      multiple={multiple}
      name={name}
      options={useCodeOptions({ name, required: multiple })}
      {...props}
    />
  );
}

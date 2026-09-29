import MultiComboBox from "@/components/MultiComboBox";
import useCodeOptions from "@/lib/useCodeOptions";

import type { Props } from "@/lib/useCodeOptions";

export default function CodeMultiComboBox({
  categories,
  name,
  ...props
}: {
  categories?: { label: string; values: string[] }[];
  className?: string;
  sortByValue?: boolean;
} & Props) {
  return (
    <MultiComboBox
      categories={categories}
      name={name}
      options={useCodeOptions({ name, required: true })}
      {...props}
    />
  );
}

import useCodeOptions, { type Props } from "@/lib/useCodeOptions";

import Combobox from "./Combobox";

export default function CodeCombobox(
  props: { className?: string; disabled?: boolean } & Props,
) {
  return <Combobox options={useCodeOptions(props)} {...props} />;
}

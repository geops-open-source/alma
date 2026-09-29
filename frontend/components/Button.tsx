import * as Headless from "@headlessui/react";

import Link from "@/components/Link";
import tw from "@/lib/tw";

type Size = "normal" | "small";

type Props = {
  active?: boolean;
  children: React.ReactNode;
  className?: string;
  group?: boolean;
  ref?: React.Ref<HTMLAnchorElement | HTMLButtonElement>;
  size?: Size;
} & (
  | { outline: true; plain?: never }
  | { outline?: never; plain: true }
  | { outline?: never; plain?: never }
) &
  (
    | Omit<Headless.ButtonProps, "className">
    | Omit<React.ComponentProps<typeof Link>, "className">
  );

export function getClassName(
  className: string,
  outline?: boolean,
  plain?: boolean,
  size?: Size,
  group?: boolean,
  active?: boolean,
) {
  const base = tw`inline-flex items-center justify-center rounded-lg border py-2 text-xs font-semibold disabled:cursor-auto ${size === "small" ? "px-2" : "px-3"}`;

  if (group) {
    const buttonGroupBase = tw`border-gray-5 text-gray-7 hover:bg-gray-3 flex inline-flex items-center justify-center gap-2 border px-3 py-2 text-sm not-first:border-l-0 first:rounded-l-lg last:rounded-r-lg ${active ? "bg-gray-3 font-bold" : "font-medium bg-white"}`;
    return tw`${className} ${buttonGroupBase}`;
  } else if (outline) {
    return tw`${className} ${base} border-gray-5 text-gray-7 hover:text-gray-8 disabled:border-gray-5 disabled:bg-gray-2 disabled:text-gray-6 hover:bg-white`;
  } else if (plain) {
    return tw`${className} ${base} text-gray-7 hover:bg-gray-2 hover:text-gray-8 disabled:text-gray-6 border-transparent`;
  } else {
    return tw`${className} ${base} border-blue-6 bg-blue-6 hover:border-blue-7 hover:bg-blue-7 disabled:border-gray-4 disabled:bg-gray-3 disabled:text-gray-6 text-white`;
  }
}

export default function Button({
  active,
  children,
  className = "",
  group,
  outline,
  plain,
  size = "normal",
  ...props
}: Props) {
  const fullClassName = getClassName(
    className,
    outline,
    plain,
    size,
    group,
    active,
  );

  return "href" in props ? (
    <Link {...props} className={fullClassName}>
      {children}
    </Link>
  ) : (
    <Headless.Button {...props} className={fullClassName}>
      {children}
    </Headless.Button>
  );
}

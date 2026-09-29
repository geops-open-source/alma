import * as Headless from "@headlessui/react";
import { type PropsWithChildren } from "react";

import ChevronIcon from "@/components/icons/ChevronIcon";
import Link from "@/components/Link";
import fonts from "@/lib/fonts";
import tw from "@/lib/tw";

export const menuItemsClassName = tw`${fonts} border-gray-5 z-60 mt-2 flex flex-col space-y-1 rounded-lg border bg-white p-1 shadow-lg`;

export function Menu({
  children,
  title,
  ...props
}: PropsWithChildren<{ title: string }>) {
  return (
    <Headless.Menu>
      <Headless.MenuButton
        className="group border-gray-5 text-gray-7 flex items-center rounded-lg border px-3.5 py-2.5 text-xs font-medium"
        {...props}
      >
        {title}
        <ChevronIcon className="ml-2 rotate-180 transition-transform group-data-active:rotate-0" />
      </Headless.MenuButton>
      <Headless.Transition leave="duration-100 ease-in" leaveTo="opacity-0">
        <Headless.MenuItems
          anchor="bottom end"
          className={menuItemsClassName}
          {...props}
        >
          {children}
        </Headless.MenuItems>
      </Headless.Transition>
    </Headless.Menu>
  );
}

const menuItemClassName = tw`text-gray-7 hover:bg-gray-2 hover:text-gray-8 flex items-center rounded-md px-3 py-2 text-left text-xs font-medium`;

export type MenuItemProps = { className?: string } & (
  | Omit<React.ComponentPropsWithoutRef<"button">, "className">
  | Omit<React.ComponentPropsWithoutRef<typeof Link>, "className">
);

export function MenuItem({ className = "", ...props }: MenuItemProps) {
  return (
    <Headless.MenuItem>
      {"href" in props ? (
        <Link
          role="menuitem"
          {...props}
          className={`${className} ${menuItemClassName}`}
        />
      ) : (
        <button
          type="button"
          {...props}
          className={`${className} ${menuItemClassName} disabled:text-gray-5 disabled:cursor-default disabled:hover:bg-white`}
        />
      )}
    </Headless.MenuItem>
  );
}

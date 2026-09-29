import { Popover, PopoverButton, PopoverPanel } from "@headlessui/react";

import XCircleIcon from "@/components/icons/XCircleIcon";
import fonts from "@/lib/fonts";

import type { PropsWithChildren } from "react";

function InfoIcon() {
  return (
    <svg
      data-test="ValidationPopover-info"
      fill="none"
      height="20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M10 7.5v3.33m0 3.34h0M8.86 3.24 1.99 15.08c-.38.66-.57.99-.54 1.26.02.23.15.45.34.58.22.16.6.16 1.36.16h13.7c.76 0 1.14 0 1.36-.16.2-.14.32-.35.34-.58.03-.27-.16-.6-.54-1.26L11.15 3.24c-.38-.65-.56-.98-.81-1.09a.83.83 0 0 0-.68 0c-.25.11-.44.44-.81 1.1Z"
        stroke="#DC6803"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function SuccessIcon() {
  return (
    <svg
      data-test="ValidationPopover-success"
      fill="none"
      height="20"
      viewBox="0 0 20 20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="m6.25 10 2.5 2.5 5-5m4.58 2.5a8.33 8.33 0 1 1-16.66 0 8.33 8.33 0 0 1 16.66 0Z"
        stroke="#079455"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

export default function ValidationPopover({
  children,
  className,
  status = "error",
  title,
}: PropsWithChildren<{
  className?: string;
  status?: "error" | "info" | "success";
  title: string;
}>) {
  return (
    <Popover className={className}>
      <PopoverButton
        className="text-red-5 outline-hidden"
        data-test="ValidationPopover-button"
      >
        {status === "error" ? <XCircleIcon /> : null}
        {status === "info" ? <InfoIcon /> : null}
        {status === "success" ? <SuccessIcon /> : null}
      </PopoverButton>
      <PopoverPanel
        anchor={{ gap: 6, to: "top" }}
        className={`${fonts} z-20 space-y-1.5 overflow-visible! rounded-lg bg-white p-3 text-xs shadow-lg after:absolute after:right-0 after:left-0 after:mx-auto after:h-3 after:w-3 after:rotate-45 after:bg-white data-[anchor=bottom_center]:after:-top-1 data-[anchor=top_center]:after:-bottom-1`}
        data-test="ValidationPopover-panel"
      >
        <div className="font-semibold">{title}</div>
        {children}
      </PopoverPanel>
    </Popover>
  );
}

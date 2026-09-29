import type { PropsWithChildren } from "react";

export default function Box({
  children,
  className = "",
  ...props
}: PropsWithChildren<{ className?: string }>) {
  return (
    <div
      className={`border-gray-4 rounded-xl border bg-white p-4 shadow-xs ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

import type { PropsWithChildren } from "react";

export default function Message({ children }: PropsWithChildren) {
  return (
    <div className="bg-blue-1 text-gray-7 rounded-lg p-2 text-xs font-medium">
      {children}
    </div>
  );
}

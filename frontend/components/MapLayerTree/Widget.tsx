import XIcon from "@/components/icons/XIcon";

export default function Widget({
  children,
  className = "",
  icon,
  onClose,
  title,
  ...props
}: React.PropsWithChildren<{
  className?: string;
  icon: React.ReactNode;
  onClose: () => void;
  title: string;
}>) {
  return (
    <div
      className={`alma-map-widget mt-0 mb-auto w-96 space-y-1 p-1 ${className}`}
      {...props}
    >
      <div className="flex items-center justify-between px-2">
        <div className="text-gray-9 flex items-center space-x-2">
          {icon}
          <span className="text-xs font-semibold">{title}</span>
        </div>
        <button onClick={onClose} type="button">
          <XIcon className="text-gray-7 hover:text-gray-8 w-5" />
        </button>
      </div>
      {children}
    </div>
  );
}

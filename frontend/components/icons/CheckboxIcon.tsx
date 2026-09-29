export default function CheckboxIcon({
  className,
  indeterminate,
}: {
  className?: string;
  indeterminate?: boolean;
}) {
  return (
    <svg
      className={className}
      fill="none"
      height="12"
      viewBox="0 0 12 12"
      width="12"
    >
      {indeterminate ? (
        <path
          d="M2.5 6h7"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.67"
        />
      ) : (
        <path
          d="M10 3 4.5 8.5 2 6"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.67"
        />
      )}
    </svg>
  );
}

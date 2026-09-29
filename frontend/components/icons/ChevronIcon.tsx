export default function ChevronIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="8"
      viewBox="0 0 12 8"
      width="12"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="m11 6.5-5-5-5 5"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.66667"
      />
    </svg>
  );
}

export default function SearchIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="16"
      viewBox="0 0 20 20"
      width="16"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="m17.5 17.5-5-5m1.667-4.167a5.833 5.833 0 1 1-11.667 0 5.833 5.833 0 0 1 11.667 0Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.667"
      />
    </svg>
  );
}

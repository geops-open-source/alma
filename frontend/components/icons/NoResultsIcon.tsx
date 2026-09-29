export default function NoResultsIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="24"
      width="24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="m19 19-4-4m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
      <path
        d="m8 8 4 4m-4 0 4-4"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="2"
      />
    </svg>
  );
}

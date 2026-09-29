export default function PlusIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M10 6.67v6.66M6.67 10h6.66m5 0a8.33 8.33 0 1 1-16.66 0 8.33 8.33 0 0 1 16.66 0Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.67"
      />
    </svg>
  );
}

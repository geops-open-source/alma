export default function EditIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="12"
      viewBox="0 0 12 12"
      width="12"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M5.5 2H3.4c-.84 0-1.26 0-1.581.163a1.5 1.5 0 0 0-.656.656C1 3.139 1 3.559 1 4.4v4.2c0 .84 0 1.26.163 1.581a1.5 1.5 0 0 0 .656.655c.32.164.74.164 1.581.164h4.2c.84 0 1.26 0 1.581-.164a1.5 1.5 0 0 0 .656-.655C10 9.861 10 9.441 10 8.6V6.5M4 8h.837c.245 0 .367 0 .482-.028a1 1 0 0 0 .29-.12c.1-.061.187-.148.36-.32L10.75 2.75a1.06 1.06 0 0 0-1.5-1.5L4.469 6.031c-.173.173-.26.26-.322.36a1 1 0 0 0-.12.29C4 6.796 4 6.918 4 7.163V8Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

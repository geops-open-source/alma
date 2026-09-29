export default function PoolIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="24"
      viewBox="0 0 24 24"
      width="25"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M4.668 7.2c0-1.12 0-1.68.218-2.108a2 2 0 0 1 .874-.874C6.188 4 6.748 4 7.868 4h2.8v6h-6V7.2ZM14.668 4h2.8c1.12 0 1.68 0 2.108.218a2 2 0 0 1 .874.874c.218.428.218.988.218 2.108V10h-6V4ZM4.668 14h6v6h-2.8c-1.12 0-1.68 0-2.108-.218a2 2 0 0 1-.874-.874c-.218-.428-.218-.988-.218-2.108V14ZM14.668 14h6v2.8c0 1.12 0 1.68-.218 2.108a2 2 0 0 1-.874.874c-.428.218-.988.218-2.108.218h-2.8v-6Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

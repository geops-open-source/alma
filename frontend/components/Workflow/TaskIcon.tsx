import type { TaskType } from "@/lib/graphql";

export function IconProzess({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="24"
      viewBox="0 0 24 24"
      width="24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="m7.543 9.498 1.125.75 1.872-2.496M14.058 9h2M14 15h2m-8.457.499 1.125.75 1.872-2.496M6 20h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function IconAufgabe({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="24"
      width="24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M15 9.5 10.5 15l-2-2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function IconFormular({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="24"
      width="24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M12 6.17H6.17c-.92 0-1.67.74-1.67 1.66v8.34c0 .92.75 1.66 1.67 1.66H12m3.33-11.66h2.5c.92 0 1.67.74 1.67 1.66v8.34c0 .92-.75 1.66-1.67 1.66h-2.5m0-11.66V4.08m0 2.09v11.66m0 0v2.09"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function IconDokument({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="24"
      width="24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M9 7h6m-6 4h6m-6 4h2m-4 6h10a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function IconNotiz({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="24"
      width="24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M21 18s-1.33 1.54-2.83 1.54-2.71-1.42-4.18-1.42A4 4 0 0 0 11 19.54m7.41-15.13.18.18a2 2 0 0 1 0 2.82l-12 12a2 2 0 0 1-1.42.59H3v-2.17a2 2 0 0 1 .59-1.42l12-12a2 2 0 0 1 2.82 0Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

export default function TaskIcon({
  className,
  taskType,
}: {
  className?: string;
  taskType: TaskType;
}) {
  switch (taskType) {
    case "AUFGABE":
      return <IconAufgabe className={className} />;
    case "DOKUMENT":
      return <IconDokument className={className} />;
    case "FORMULAR":
      return <IconFormular className={className} />;
    case "NOTIZ":
      return <IconNotiz className={className} />;
    case "PROZESS":
      return <IconProzess className={className} />;
    default:
      return <IconAufgabe className={className} />;
  }
}

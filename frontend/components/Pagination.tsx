import Button from "@/components/Button";
import { useI18n } from "@/lib/i18n";

type Size = "normal" | "small";

function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M15.833 10H4.166m0 0 5.833 5.833M4.166 10l5.833-5.833"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.667"
      />
    </svg>
  );
}

function ArrowRightIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M4.166 10h11.667m0 0L9.999 4.167M15.833 10l-5.834 5.833"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.667"
      />
    </svg>
  );
}

const range = (start: number, end: number) => {
  return [...Array<number>(end - start + 1)].map((_, i) => {
    return i + start;
  }) as (number | string)[];
};

function getPageNumbers(pagesCount: number, currentPage: number, size: Size) {
  const delta = size === "small" ? 0 : 2;
  const left = Math.max(currentPage - delta, 1);
  const right = Math.min(currentPage + delta, pagesCount);
  const pageNumbers = range(left, right);

  if (left > 1) {
    if (left > 2) {
      pageNumbers.unshift("...");
    }
    pageNumbers.unshift(1);
  }

  if (right < pagesCount) {
    if (right < pagesCount - 1) {
      pageNumbers.push("...");
    }
    pageNumbers.push(pagesCount);
  }

  return pageNumbers;
}

export default function Pagination({
  currentPage,
  pagesCount,
  setPage,
  size = "normal",
}: {
  currentPage: number;
  pagesCount: number;
  setPage: (p: number) => void;
  size?: Size;
}) {
  const { t } = useI18n();

  return (
    <div className="flex justify-between bg-white p-4">
      <Button
        className="flex gap-2 disabled:opacity-50"
        disabled={currentPage <= 1}
        onClick={() => {
          return setPage(currentPage - 1);
        }}
        outline
        size={size}
      >
        <ArrowLeftIcon />
        {size !== "small" && t("Pagination.back")}
      </Button>
      <div className="flex shrink-0 justify-center">
        {getPageNumbers(pagesCount, currentPage, size).map((page, index) => {
          return page === "..." ? (
            <span className="p-2" key={index}>
              ...
            </span>
          ) : (
            <Button
              className={`${currentPage === page && "bg-gray-3"}`}
              key={index}
              onClick={() => {
                return setPage(page as number);
              }}
              plain
            >
              {page}
            </Button>
          );
        })}
      </div>
      <Button
        className="flex gap-2 disabled:opacity-50"
        disabled={currentPage >= pagesCount}
        onClick={() => {
          return setPage(currentPage + 1);
        }}
        outline
        size={size}
      >
        {size !== "small" && t("Pagination.forward")}
        <ArrowRightIcon />
      </Button>
    </div>
  );
}

const isISODate =
  /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(?:\.\d*)?(?:Z|[+-]\d{2}:\d{2})?)?$/;

export default function toLocaleDateString(input?: null | string) {
  const date = input?.match(isISODate) && new Date(input);
  return !date || Number.isNaN(date.getTime())
    ? ""
    : date.toLocaleDateString("de", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      });
}

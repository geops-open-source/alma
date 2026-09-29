export default function StableWidthText({ value }: { value: string }) {
  return (
    <span
      className={`block text-center before:invisible before:block before:h-0 before:font-bold before:content-[attr(title)]`}
      title={value}
    >
      {value}
    </span>
  );
}

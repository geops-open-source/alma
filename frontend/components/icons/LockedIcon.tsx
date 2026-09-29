export default function LockedIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      data-test="LockedIcon"
      fill="none"
      height="18"
      width="16"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M12.167 7.333V5.667a4.167 4.167 0 0 0-8.334 0v1.666M8 11.083v1.667M5.333 16.5h5.334c1.4 0 2.1 0 2.635-.273a2.5 2.5 0 0 0 1.092-1.092c.273-.535.273-1.235.273-2.635v-1.167c0-1.4 0-2.1-.273-2.635a2.5 2.5 0 0 0-1.092-1.092c-.535-.273-1.235-.273-2.635-.273H5.333c-1.4 0-2.1 0-2.635.273a2.5 2.5 0 0 0-1.092 1.092c-.273.535-.273 1.235-.273 2.635V12.5c0 1.4 0 2.1.273 2.635a2.5 2.5 0 0 0 1.092 1.092c.535.273 1.235.273 2.635.273Z"
        stroke="#344054"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.667"
      />
    </svg>
  );
}

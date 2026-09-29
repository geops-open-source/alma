import { useEffect } from "react";

function useClickOutside(
  ref: React.RefObject<HTMLElement | null>,
  callback: () => void,
) {
  useEffect(() => {
    const handleClickOutside = (event: KeyboardEvent | MouseEvent) => {
      if (
        ref.current &&
        event.target &&
        !ref.current.contains(event.target as Node)
      ) {
        callback();
      }
    };
    document.addEventListener("click", handleClickOutside);
    document.addEventListener("keyup", handleClickOutside);
    return () => {
      document.removeEventListener("click", handleClickOutside);
      document.removeEventListener("keyup", handleClickOutside);
    };
  }, [ref, callback]);
}

export default useClickOutside;

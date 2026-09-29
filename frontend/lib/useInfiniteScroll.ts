import { useCallback, useEffect, useRef } from "react";

export default function useInfiniteScroll(
  onScrollDown: () => void,
  offset = 1024,
  wait = 200,
  onScrollUp?: () => void,
) {
  const onScrollDownRef = useRef(onScrollDown);
  const onScrollUpRef = useRef(onScrollUp);

  // Keep refs in sync so the scroll handler always calls the latest callback,
  // avoiding stale closures without re-attaching the event listener.
  useEffect(() => {
    onScrollDownRef.current = onScrollDown;
    onScrollUpRef.current = onScrollUp;
  });

  // Callback ref: React re-invokes it whenever the underlying DOM node
  // changes, so listeners are always attached to the current element.
  return useCallback(
    (el: HTMLDivElement | null) => {
      if (!el) {
        return;
      }

      let timeoutId: null | ReturnType<typeof setTimeout> = null;

      const handleScroll = () => {
        if (timeoutId) {
          return;
        }
        timeoutId = setTimeout(() => {
          timeoutId = null;
          if (el.scrollHeight - el.scrollTop - el.clientHeight < offset) {
            onScrollDownRef.current();
          }
          if (onScrollUpRef.current && el.scrollTop < offset) {
            onScrollUpRef.current();
          }
        }, wait);
      };

      el.addEventListener("scroll", handleScroll);
      el.addEventListener("touchmove", handleScroll, { passive: true });
      el.addEventListener("wheel", handleScroll, { passive: true });

      return () => {
        el.removeEventListener("scroll", handleScroll);
        el.removeEventListener("touchmove", handleScroll);
        el.removeEventListener("wheel", handleScroll);
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
      };
    },
    [offset, wait],
  );
}

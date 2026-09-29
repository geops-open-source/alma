import { useEffect, useState } from "react";

import type { Dispatch, SetStateAction } from "react";

export default function useLocalStorage<T>(
  key: string,
  defaultValue: T,
): [T, Dispatch<SetStateAction<T>>] {
  const [value, setValue] = useState<T>(() => {
    let currentValue;

    try {
      currentValue = JSON.parse(
        localStorage.getItem(key) ?? String(defaultValue),
      ) as T;
    } catch {
      currentValue = defaultValue;
    }

    return currentValue;
  });

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value));
  }, [value, key]);

  return [value, setValue];
}

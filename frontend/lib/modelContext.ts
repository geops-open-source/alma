import { createContext, useContext } from "react";

export const ModelContext = createContext("");

export function useModelContext() {
  return useContext(ModelContext);
}

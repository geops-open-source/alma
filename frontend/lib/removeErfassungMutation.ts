/**
 * Strip the read-only `erfassungMutation` field from a GraphQL query result
 * before re-submitting it as mutation input (input types don't accept it).
 */
export default function removeErfassungMutation<
  T extends { erfassungMutation?: unknown },
>(obj: T): Omit<T, "erfassungMutation"> {
  const newObj = { ...obj };
  delete newObj.erfassungMutation;
  return newObj;
}

type MaybeDateTime = null | string | undefined;

export default function notFuture(a: MaybeDateTime, b: MaybeDateTime) {
  return new Date(a ?? 0) <= new Date(b ?? 0);
}

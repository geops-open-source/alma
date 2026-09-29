export function dayEnd(date: string) {
  return `${date.slice(0, 10)}T23:59:59`;
}

export function dayStart(date: string) {
  return `${date.slice(0, 10)}T00:00:00`;
}

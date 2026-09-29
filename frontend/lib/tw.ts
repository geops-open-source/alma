function tw(strings: ArrayLike<string> | string[], ...values: unknown[]) {
  return String.raw({ raw: strings }, ...values);
}

export default tw;

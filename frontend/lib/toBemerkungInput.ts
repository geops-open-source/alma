import type { BemerkungInput } from "./graphql";

type Bemerkung = { bem?: null | string } | null;

function toBemerkungInput(bemerkung?: Bemerkung | null): BemerkungInput | null {
  return bemerkung?.bem ? { bem: bemerkung.bem } : null;
}

export default toBemerkungInput;

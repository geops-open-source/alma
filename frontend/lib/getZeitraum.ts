import { gql } from "graphql-request";

import { StandortTyp } from "./graphql";
import toLocaleDateString from "./toLocaleDateString";

import type { ZeitraumInput } from "./graphql";

interface Info {
  vftypEnum?: StandortTyp;
  zeitraum?: null | Omit<ZeitraumInput, "__typename">;
}

function getZeitraum(t: (key: string) => string, info?: Info | null) {
  let von = t("zeitraum.unknown");
  if (info?.zeitraum?.von && info.zeitraum.vonjahr) {
    von = new Date(info.zeitraum.von).getFullYear().toString();
  } else if (info?.zeitraum?.von) {
    von = toLocaleDateString(info.zeitraum.von);
  }

  let bis = t("zeitraum.unknown");
  if (info?.zeitraum?.bisheute) {
    bis = t("zeitraum.bisheute");
  } else if (info?.zeitraum?.bis && info.zeitraum.bisjahr) {
    bis = new Date(info.zeitraum.bis).getFullYear().toString();
  } else if (info?.zeitraum?.bis) {
    bis = toLocaleDateString(info.zeitraum.bis);
  }

  return info?.vftypEnum === StandortTyp.Unfall ? von : `${von} - ${bis}`;
}

getZeitraum.fragment = gql`
  fragment getZeitraum on Zeitraum {
    von
    bis
    vonjahr
    bisjahr
    bisheute
  }
`;

export default getZeitraum;

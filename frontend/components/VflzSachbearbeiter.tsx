import { gql } from "graphql-request";

import type { VflzSachbearbeiterFragment } from "@/lib/graphql";

function Beteiligter({ name }: { name: string }) {
  return (
    <div
      className="border-gray-5 rounded-md border px-1 py-0.5 text-xs"
      data-test="VflzSachbearbeiter-beteiligter"
    >
      {name}
    </div>
  );
}

function VflzSachbearbeiter({
  beteiligteStandort,
}: {
  beteiligteStandort?: VflzSachbearbeiterFragment["beteiligteStandort"];
}) {
  return (
    <div className="flex space-x-2">
      {beteiligteStandort
        ?.filter(({ beteiligter }) => {
          return beteiligter.isSachbearbeiter;
        })
        .map(({ beteiligter }) => {
          return `${beteiligter.subjekt.vorname} ${beteiligter.subjekt.name}`;
        })
        .sort((a, b) => {
          return a.localeCompare(b);
        })
        .map((name) => {
          return <Beteiligter key={name} name={name} />;
        })}
    </div>
  );
}

VflzSachbearbeiter.fragment = gql`
  fragment VflzSachbearbeiter on Vflz {
    beteiligteStandort {
      beteiligter {
        isSachbearbeiter
        subjekt {
          name
          vorname
        }
      }
    }
  }
`;

export default VflzSachbearbeiter;

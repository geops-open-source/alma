import { gql } from "graphql-request";
import Link from "next/link";

import { useI18n } from "@/lib/i18n";
import toLocaleDateString from "@/lib/toLocaleDateString";

import type { VflzStatusTextFragment } from "@/lib/graphql";

function VflzStatusText({ vflz }: { vflz?: VflzStatusTextFragment }) {
  const { t } = useI18n();
  const isCurrent = vflz?.isCurrent;
  const versionen = vflz?.versionen;
  const publishedVersion = versionen?.find((v) => {
    return v.publizieren;
  });
  const isContaminated = publishedVersion?.beurteilung?.kbsInfo?.belastet;

  const text: string[] = [];
  if (isCurrent) {
    text[0] = "current";
  } else if (vflz) {
    text[0] = "historized";
  }
  if (isCurrent && isContaminated) {
    text[1] = "contaminated";
  } else if (isCurrent === false && isContaminated) {
    text[1] = "contaminated";
  } else if (isCurrent && isContaminated === false) {
    text[1] = "deleted";
  } else if (isCurrent === false && isContaminated === false) {
    text[1] = "deleted";
  }

  const { datPublizieren } =
    vflz?.versionen.find((v) => {
      return v.publizieren;
    }) ?? {};

  const values = {
    datPublizieren: toLocaleDateString(datPublizieren),
    vflzCreatedDate: toLocaleDateString(vflz?.vflzCreatedDate),
  };

  if (publishedVersion && text[1] === "contaminated") {
    return (
      <>
        <p>{t(`VflzStatusText.${text[0]}`, values)}</p>
        <p>
          <Link
            className="text-blue-8 hover:underline"
            href={`/vflz/${publishedVersion.vflzId}/data`}
          >
            {t(`VflzStatusText.${text[1]}`, values)}
          </Link>
        </p>
      </>
    );
  }

  return text.map((txt, i) => {
    return <p key={i}>{t(`VflzStatusText.${txt}`, values)}</p>;
  });
}

VflzStatusText.fragment = gql`
  fragment VflzStatusText on Vflz {
    isCurrent
    vflzCreatedDate
    versionen {
      vflzId
      datPublizieren
      publizieren
      beurteilung {
        kbsInfo {
          belastet
        }
      }
    }
  }
`;

export default VflzStatusText;

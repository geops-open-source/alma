import { gql } from "graphql-request";
import Link from "next/link";
import { useRouter } from "next/router";

import PublicationIcon from "@/components/icons/PublicationIcon";
import VflzStatusText from "@/components/VflzStatusText";
import { useI18n } from "@/lib/i18n";

import type { VflzStatusFragment, VflzSummaryFragment } from "@/lib/graphql";

function MarkerIcon({ className = "" }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="26"
      viewBox="0 0 24 26"
      width="22"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M11 14.2a3.68 3.68 0 0 0 3.75-3.6C14.75 8.61 13.07 7 11 7a3.68 3.68 0 0 0-3.75 3.6c0 1.99 1.68 3.6 3.75 3.6Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M11 25c5-4.8 10-9.1 10-14.4C21 5.3 16.52 1 11 1S1 5.3 1 10.6 6 20.2 11 25Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function VflzStatus({ vflz }: { vflz?: VflzStatusFragment }) {
  const { t } = useI18n();
  if (!vflz) {
    return null;
  } else if (vflz.evaluationStatus.deleteNow) {
    return t("VflzSummary.deleteNow");
  } else if (vflz.evaluationStatus.publishNow) {
    return t("VflzSummary.publishNow");
  } else if (vflz.evaluationStatus.publishedPreviously) {
    return t("VflzSummary.publishedPreviously");
  } else if (vflz.evaluationStatus.deletedPreviously) {
    return t("VflzSummary.deletedPreviously");
  } else if (vflz.isCurrent) {
    return t("VflzSummary.current");
  }
  return t("VflzSummary.historized");
}

VflzStatus.fragment = gql`
  fragment VflzStatus on Vflz {
    isCurrent
    evaluationStatus {
      deletedPreviously
      deleteNow
      publishedPreviously
      publishNow
    }
  }
`;

function VflzSummary({
  className = "",
  isWide,
  vflz,
}: {
  className?: string;
  isWide?: boolean;
  vflz?: VflzSummaryFragment;
}) {
  const router = useRouter();
  const { t } = useI18n();
  return (
    <div
      className={`text-gray-7 text-sm font-medium ${isWide ? "space-y-1" : "space-y-2"} ${className}`}
      data-test="VflzSummary"
    >
      <div className={`flex ${isWide ? "space-x-3" : "flex-col"}`}>
        <div className="text-gray-9 min-h-7 text-lg font-semibold">
          {router.asPath.startsWith(`/vflz/${vflz?.vflzId}`) ? (
            <>
              {vflz?.combinedId} {vflz?.bezeichnung}
            </>
          ) : (
            <Link className="text-blue-7" href={`/vflz/${vflz?.vflzId}`}>
              {vflz?.combinedId} {vflz?.bezeichnung}
            </Link>
          )}
        </div>
        {vflz?.gemeinde ? (
          <div className="flex items-center" data-test="VflzSummary-gemeinde">
            <MarkerIcon className="mr-1 h-4 w-4 stroke-2" />
            {vflz.gemeinde.gemeinde}
          </div>
        ) : null}
      </div>
      <div
        className={`flex ${isWide ? "h-8 flex-row-reverse items-start justify-end space-x-3 space-x-reverse" : "flex-col space-y-1"}`}
      >
        {vflz?.beurteilung?.beurteilung && vflz.beurteilung.kbsInfo ? (
          <div
            className="flex w-fit items-center rounded-full border py-0.5 pr-2 pl-1.5 text-xs font-medium"
            data-test="VflzSummary-beurteilung"
            style={{
              backgroundColor: `${vflz.beurteilung.kbsInfo.color}33`,
              borderColor: vflz.beurteilung.kbsInfo.color,
            }}
          >
            <div
              className="mr-1 h-1.5 w-1.5 rounded-full"
              style={{ backgroundColor: vflz.beurteilung.kbsInfo.color }}
            />
            {t(vflz.beurteilung.beurteilung)}
          </div>
        ) : null}
        <div className="flex items-center">
          <PublicationIcon className="mr-1 w-5" vflz={vflz} />
          <VflzStatus vflz={vflz} />
        </div>
      </div>
    </div>
  );
}

VflzSummary.fragment = gql`
  fragment VflzSummary on Vflz {
    vflzId
    combinedId
    beurteilung {
      beurteilung
      kbsInfo {
        color
      }
    }
    bezeichnung
    gemeinde {
      gemeinde
      kanton
    }
    publizieren
    ...PublicationIcon
    ...VflzStatus
    ...VflzStatusText
  }
  ${PublicationIcon.fragment}
  ${VflzStatus.fragment}
  ${VflzStatusText.fragment}
`;

export default VflzSummary;

import { gql } from "graphql-request";

import type { PublicationIconFragment } from "@/lib/graphql";

function PublicationIcon({
  className = "",
  preserveLayout = false,
  vflz,
}: {
  className?: string;
  preserveLayout?: boolean;
  vflz?: PublicationIconFragment;
}) {
  const fill =
    vflz?.evaluationStatus.deleteNow === true ||
    vflz?.evaluationStatus.publishNow === true
      ? "fill-blue-6"
      : "fill-blue-4";

  const isOpen =
    (vflz?.evaluationStatus.publishNow === true ||
      vflz?.evaluationStatus.publishedPreviously === true) &&
    vflz?.evaluationStatus.deleteNow === false;

  if (
    vflz?.evaluationStatus.deleteNow === false &&
    vflz?.evaluationStatus.deletedPreviously === false &&
    vflz?.evaluationStatus.publishNow === false &&
    vflz?.evaluationStatus.publishedPreviously === false
  ) {
    return preserveLayout ? (
      <span className={className ? className : "size-6"} />
    ) : null;
  }

  return (
    <svg
      className={className}
      data-test={isOpen ? "PublicationIcon-open" : "PublicationIcon"}
      height="24"
      viewBox="0 0 24 24"
      width="24"
      xmlns="http://www.w3.org/2000/svg"
    >
      {isOpen ? (
        <>
          <path className={fill} d="M10 12a2 2 0 1 1 4 0 2 2 0 0 1-4 0Z" />
          <path
            className={fill}
            d="M4.74 7.03A10.48 10.48 0 0 1 12 4c3.07 0 5.55 1.4 7.25 3.03.86.82 1.53 1.7 2 2.55.44.81.75 1.68.75 2.42s-.3 1.6-.76 2.42c-.46.84-1.13 1.73-1.98 2.55A10.48 10.48 0 0 1 12 20c-3.07 0-5.55-1.4-7.26-3.03-.85-.82-1.52-1.7-1.98-2.55A5.31 5.31 0 0 1 2 12c0-.74.3-1.6.76-2.42.46-.84 1.13-1.73 1.98-2.55ZM12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z"
          />
        </>
      ) : (
        <>
          <path
            className={fill}
            d="M23.373 2.707a1 1 0 0 0-1.414-1.414L17.93 5.32a.203.203 0 0 1-.244.032A10.058 10.058 0 0 0 12.666 4C9.599 4 7.112 5.396 5.411 7.029a10.928 10.928 0 0 0-1.988 2.55c-.45.815-.757 1.678-.757 2.421 0 .91.462 2.022 1.136 3.048.487.739 1.126 1.5 1.902 2.196a.203.203 0 0 1 .01.294l-3.755 3.755a1 1 0 1 0 1.414 1.414l20-20Zm-8.858 6.03a.19.19 0 0 0-.043-.307 4 4 0 0 0-5.376 5.376.19.19 0 0 0 .306.043l1.25-1.25c.05-.05.07-.123.055-.193a2 2 0 0 1 2.365-2.365.213.213 0 0 0 .194-.055l1.25-1.25Z"
            fillRule="evenodd"
          />
          <path
            className={fill}
            d="m10.703 18.204 2.159-2.158a.206.206 0 0 1 .129-.06 4 4 0 0 0 3.661-3.66.206.206 0 0 1 .06-.13l3.324-3.325a1 1 0 0 1 1.548.166c.642.998 1.082 2.075 1.082 2.963 0 .743-.308 1.605-.758 2.42a10.929 10.929 0 0 1-1.987 2.551C18.22 18.604 15.733 20 12.666 20a9.94 9.94 0 0 1-1.396-.098 1 1 0 0 1-.567-1.698Z"
          />
        </>
      )}
    </svg>
  );
}

PublicationIcon.fragment = gql`
  fragment PublicationIcon on Vflz {
    evaluationStatus {
      deletedPreviously
      deleteNow
      publishedPreviously
      publishNow
    }
  }
`;

export default PublicationIcon;

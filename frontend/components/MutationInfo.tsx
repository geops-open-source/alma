import { gql } from "graphql-request";

import EditIcon from "@/components/icons/EditIcon";
import toLocaleDateString from "@/lib/toLocaleDateString";

import type { MutationInfoFragment } from "@/lib/graphql";

export type Props = {
  className?: string;
} & MutationInfoFragment;

function MutationInfo({ className = "", ...props }: Props) {
  return (props.erfassungsDatum || props.mutationsDatum) &&
    (props.erfasser || props.mutierer) ? (
    <div
      className={`border-gray-4 bg-gray-2 flex items-center space-x-1.5 rounded-full border p-1 px-2.5 text-xs font-medium ${className}`}
      data-test="MutationInfo"
    >
      <EditIcon />
      <span>{`${props.mutierer || props.erfasser} ${toLocaleDateString(props.mutationsDatum || props.erfassungsDatum)}`}</span>
    </div>
  ) : null;
}

export const mutationInfoFragment = gql`
  fragment MutationInfo on ErfassungMutation {
    erfassungsDatum
    erfasser
    mutationsDatum
    mutierer
  }
`;

export default MutationInfo;

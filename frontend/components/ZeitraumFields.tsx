import { gql } from "graphql-request";
import get from "lodash/get";

import CodeListbox from "./CodeListbox";
import DatePicker from "./DatePicker";

interface Props {
  mitGenauigkeit?: boolean;
  name: string;
}

function validate(von: unknown, bis: unknown) {
  if (
    typeof von === "string" &&
    typeof bis === "string" &&
    new Date(von) > new Date(bis)
  ) {
    return "zeitraum";
  }
}

function ZeitraumFields({ mitGenauigkeit, name }: Props) {
  return (
    <>
      <DatePicker
        hasJahr
        name={`${name}.von`}
        validate={(von, values) => {
          return validate(von, get(values, `${name}.bis`));
        }}
      />
      {mitGenauigkeit && <CodeListbox name={`${name}.genauigkeitVon`} />}
      <DatePicker
        hasHeute
        hasJahr
        name={`${name}.bis`}
        validate={(bis, values) => {
          return validate(get(values, `${name}.von`), bis);
        }}
      />
      {mitGenauigkeit && <CodeListbox name={`${name}.genauigkeitBis`} />}
    </>
  );
}

ZeitraumFields.fragment = gql`
  fragment ZeitraumFields on Zeitraum {
    von
    vonjahr
    bis
    bisjahr
    bisheute
  }
`;

ZeitraumFields.fragmentMitGenauigkeit = gql`
  fragment ZeitraumFieldsMitGenauigkeit on ZeitraumMitGenauigkeit {
    von
    vonjahr
    bis
    bisjahr
    bisheute
    genauigkeitVon
    genauigkeitBis
  }
`;

export default ZeitraumFields;

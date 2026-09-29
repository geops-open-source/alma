import { gql } from "graphql-request";
import dynamic from "next/dynamic";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { type Path, useFormContext, useWatch } from "react-hook-form";
import useSWR from "swr";

import Form, { useValidatedData } from "@/components/Form";
import Layout from "@/components/Layout";
import VflzActionMenu from "@/components/VflzActionMenu";
import VflzCreateFormFields from "@/components/VflzCreateFormFields";
import VflzMapEditorFragment from "@/components/VflzMapEditor.fragment";
import client from "@/lib/client";
import { useI18n } from "@/lib/i18n";
import useCurrentUser from "@/lib/useCurrentUser";

import type { GeoJSONMultiPolygon, GeoJSONPoint } from "ol/format/GeoJSON";

import type {
  CreateTeilstandortMutation,
  ValidateCreateTeilstandortQuery,
  VflzSplitQuery,
} from "@/lib/graphql";

const VflzMapEditor = dynamic(
  () => {
    return import("@/components/VflzMapEditor");
  },
  {
    ssr: false,
  },
);

type CreateTeilstandortForm = {
  geometry?: GeoJSONMultiPolygon | GeoJSONPoint | null;
  selectedGeometry?: GeoJSONMultiPolygon | GeoJSONPoint | null;
  selectedZentroid?: GeoJSONPoint | null;
} & VflzSplitQuery["vflz"];

const createTeilstandortMutation = gql`
  mutation createTeilstandort($data: CreateTeilstandortInput!) {
    createTeilstandort(data: $data) {
      __typename
      ... on Vflz {
        vflzId
      }
      ... on ProblemGroup {
        ...FormProblems
      }
    }
  }
  ${Form.fragment}
`;

const queryParentVflz = gql`
  query VflzSplit($vflzId: ID!) {
    vflz(vflzId: $vflzId) {
      isCurrent
      readOnly
      ...VflzCreateFormFields
      ...VflzMapEditor
    }
  }
  ${VflzCreateFormFields.fragment}
  ${VflzMapEditorFragment}
`;

const queryValidateCreateTeilstandort = gql`
  query validateCreateTeilstandort($data: ValidateCreateTeilstandortInput!) {
    validateCreateTeilstandort(data: $data) {
      ... on ValidatedCreateVflzData {
        combinedId
        flugplatz
        gemeinde {
          __typename
          displayValue
          hGemId
          kanton
        }
      }
      ... on ProblemGroup {
        ...FormProblems
      }
    }
  }
  ${Form.fragment}
`;

function FormFields({ parentCombinedId }: { parentCombinedId?: string }) {
  const [, setTick] = useState(0);
  const { setValidatedData } = useValidatedData();
  const { setError, setValue } = useFormContext<CreateTeilstandortForm>();
  const { t } = useI18n();
  const geometry = useWatch<CreateTeilstandortForm>({
    name: "selectedGeometry",
  });
  const hGemId = useWatch<CreateTeilstandortForm>({ name: "gemeinde.hGemId" });

  useEffect(() => {
    if (!geometry || !parentCombinedId) {
      setValidatedData({});
      return;
    }
    void client
      .request<ValidateCreateTeilstandortQuery>(
        queryValidateCreateTeilstandort,
        {
          data: {
            combinedId: null,
            gemeinde: hGemId ? { hGemId } : null,
            geometry,
            parentCombinedId,
          },
        },
      )
      .then(({ validateCreateTeilstandort }) => {
        if ("combinedId" in validateCreateTeilstandort) {
          if (validateCreateTeilstandort.combinedId.length === 1) {
            setValue("combinedId", validateCreateTeilstandort.combinedId[0], {
              shouldDirty: true,
            });
          }
          if (validateCreateTeilstandort.gemeinde.length === 1) {
            setValue("gemeinde", validateCreateTeilstandort.gemeinde[0], {
              shouldDirty: true,
            });
          }
          setValidatedData(validateCreateTeilstandort);
        } else {
          setValidatedData({});
          validateCreateTeilstandort.problems.forEach((p) => {
            setError(p.field as Path<CreateTeilstandortForm>, {
              type: `${p.problemCode}.${p.field}`,
            });
          });
          setTick((tick) => {
            return tick + 1;
          }); // force rerender to update view
        }
      });
  }, [
    geometry,
    hGemId,
    parentCombinedId,
    setError,
    setValidatedData,
    setValue,
  ]);

  return (
    <VflzCreateFormFields
      message={t("vflz.split.message")}
      title={t("vflz.split.title")}
      vftypDisabled
    />
  );
}

export default function VflzSplitPage() {
  const { permissions } = useCurrentUser();
  const { t } = useI18n();
  const router = useRouter();
  const { vflzId } = router.query;
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const { data, error, mutate } = useSWR<VflzSplitQuery>(
    vflzId && [queryParentVflz, { vflzId }],
  );

  return (
    <Layout error={error as unknown} title={t("vflz.split.title")}>
      <Form<CreateTeilstandortForm>
        className="mt-4 space-y-5"
        disabled={data?.vflz.readOnly || !permissions.canEditVfl}
        model="Vflz"
        onSubmit={async (values, methods) => {
          if (values.zentroid) {
            values.zentroid.coordinates[2] = 0;
          }
          if (values.selectedZentroid) {
            values.selectedZentroid.coordinates[2] = 0;
          }
          const { createTeilstandort } =
            await client.request<CreateTeilstandortMutation>(
              createTeilstandortMutation,
              {
                data: {
                  bezeichnung: values.bezeichnung,
                  combinedId: values.combinedId,
                  flugplatz: values.flugplatz ?? null,
                  gemeinde: { hGemId: values.gemeinde?.hGemId },
                  geometry: values.selectedGeometry,
                  ktu: values.ktu ?? null,
                  parentGeometry: values.geometry,
                  parentVflzId: vflzId,
                  parentZentroid: values.zentroid,
                  zentroid: values.selectedZentroid,
                },
              },
            );
          if (createTeilstandort.__typename === "Vflz") {
            methods.reset(undefined, { keepValues: true });
            setTimeout(() => {
              void router.push(
                `/vflz/${createTeilstandort.vflzId}/data?ignoreDirtyFields=true`,
              );
            }, 100); // wait for reset to complete
          } else {
            return createTeilstandort; // ProblemGroup
          }
        }}
        values={data?.vflz}
      >
        <FormFields parentCombinedId={data?.vflz.combinedId} />
        <VflzMapEditor setSelected vflz={data?.vflz} />
        <VflzActionMenu
          canEditVollzug={data?.vflz.isCurrent && permissions.canEditVfl}
          hideMenu
          mutatePage={mutate}
        />
      </Form>
    </Layout>
  );
}

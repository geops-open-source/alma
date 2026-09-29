import { captureException } from "@sentry/nextjs";
import { gql } from "graphql-request";
import unset from "lodash/unset";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import useSWR from "swr";

import ActionMenu from "@/components/ActionMenu";
import Button from "@/components/Button";
import Checkbox from "@/components/Checkbox";
import CodeListbox from "@/components/CodeListbox";
import Dialog from "@/components/Dialog";
import FieldArray from "@/components/FieldArray";
import Form from "@/components/Form";
import HistorizeIcon from "@/components/icons/HistorizeIcon";
import PlusIcon from "@/components/icons/PlusIcon";
import Input from "@/components/Input";
import MutationInfo, { mutationInfoFragment } from "@/components/MutationInfo";
import Spinner from "@/components/Spinner";
import client from "@/lib/client";
import getVflzUrl from "@/lib/getVflzUrl";
import { useI18n } from "@/lib/i18n";
import removeErfassungMutation from "@/lib/removeErfassungMutation";

import type {
  HistorizeVflzInput,
  HistorizeVflzMutation,
  UpdateVollzugMutation,
  VollzugDialogQuery,
  VollzugFormFieldsFragment,
  VollzugInput,
} from "@/lib/graphql";

function HashIcon() {
  return (
    <svg
      fill="none"
      height="20"
      viewBox="0 0 20 20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="m7.917 2.5-2.5 15m9.166-15-2.5 15m5-10.833H2.917m13.333 6.666H2.083"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.667"
      />
    </svg>
  );
}

function SplitIcon() {
  return (
    <svg
      clipRule="evenodd"
      fillRule="evenodd"
      height="20"
      strokeLinecap="round"
      strokeLinejoin="round"
      viewBox="0 0 20 20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
      xmlSpace="preserve"
    >
      <g fill="none" stroke="#344054" strokeWidth="1.67">
        <path d="M4.158 13.719a1.724 1.724 0 1 0-2.436-2.439 1.724 1.724 0 0 0 2.436 2.439Zm4.532 4.53a1.726 1.726 0 1 0-2.442-2.439 1.726 1.726 0 0 0 2.442 2.439Zm-.176-6.794-.727 3.879M9.834 4.413l-.931 4.963m6.651.758L4.633 12.182M1 7.5V2a1 1 0 0 1 1-1h16a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1h-5.5" />
        <path
          d="M16.5 3.5 13 7"
          strokeDasharray="1.67,3"
          strokeLinejoin="miter"
        />
      </g>
    </svg>
  );
}

const historizeVflzMutation = gql`
  mutation historizeVflz($data: HistorizeVflzInput!) {
    historizeVflz(data: $data) {
      __typename
      ... on Vflz {
        vflzId
      }
    }
  }
`;

function HistorizeDialog({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const { t } = useI18n();
  const router = useRouter();
  return (
    <Dialog
      data-test="HistorizeDialog"
      isOpen={isOpen}
      onClose={onClose}
      title={t("VflzActionMenu.HistorizeDialog.title")}
    >
      <Form<HistorizeVflzInput>
        className="min-w-96"
        model="Vflz"
        onSubmit={({ message }) => {
          client
            .request<HistorizeVflzMutation>(historizeVflzMutation, {
              data: { message, vflzId: router.query.vflzId },
            })
            .then(async ({ historizeVflz }) => {
              if (historizeVflz.__typename === "Vflz") {
                await router.push(getVflzUrl(historizeVflz.vflzId));
                onClose();
              } else {
                throw new Error("Historize failed");
              }
            })
            .catch((error) => {
              console.error(error);
              // TODO: show error dialog
            });
        }}
      >
        <Input name="message" />
        <div className="mt-8 flex justify-end gap-4">
          <Button onClick={onClose} outline>
            {t("cancel")}
          </Button>
          <Button type="submit">
            {t("VflzActionMenu.HistorizeDialog.submit")}
          </Button>
        </div>
      </Form>
    </Dialog>
  );
}

const emptyVollzug: VollzugInput = {
  aktiv: false,
  behoerde: null,
  combinedId: "",
  vflnrId: null,
};

const vollzugFormFieldsFragment = gql`
  fragment VollzugFormFields on Vflz {
    vflzId
    vollzug {
      aktiv
      behoerde
      combinedId
      isDeleteable
      vflnrId
      erfassungMutation {
        ...MutationInfo
      }
    }
  }
  ${mutationInfoFragment}
`;

const queryVollzug = gql`
  query VollzugDialog($vflzId: ID!) {
    vflz(vflzId: $vflzId) {
      ...VollzugFormFields
    }
  }
  ${vollzugFormFieldsFragment}
`;

const updateVollzugMutation = gql`
  mutation updateVollzug($data: UpdateVflzVollzugInput!) {
    updateVflzVollzug(data: $data) {
      __typename
      ... on ProblemGroup {
        problems {
          field
          problemCode
        }
      }
    }
  }
`;

function VollzugFormFields() {
  const { t } = useI18n();
  const { control, setValue } = useFormContext<VollzugFormFieldsFragment>();
  const vollzug = useWatch({ control, name: "vollzug" });

  useEffect(() => {
    const noneActive = vollzug.every((v) => {
      return v.aktiv === false;
    });
    if (noneActive && vollzug.length > 0) {
      setValue("vollzug.0.aktiv", true);
    }
  }, [vollzug, setValue]);

  const handleCheckboxChange = (index: number) => {
    vollzug.forEach((_, i) => {
      return setValue(`vollzug.${i}.aktiv`, i === index);
    });
  };

  const requiredIndex = vollzug.findIndex((v) => {
    return v.isDeleteable === false;
  });

  return (
    <FieldArray<VollzugInput>
      addLabel={t("VflzActionMenu.VollzugDialog.addLabel")}
      model="Vollzug"
      name="vollzug"
      required={requiredIndex}
      value={emptyVollzug}
    >
      {(index) => {
        return (
          <div className="grid grid-cols-3 gap-x-8">
            <MutationInfo
              className={`absolute top-2 ${index === requiredIndex ? "right-2" : "right-14"}`}
              {...vollzug[index]?.erfassungMutation}
            />
            <Input name={`vollzug.${index}.combinedId`} required />
            <CodeListbox
              disabled={index === requiredIndex}
              name={`vollzug.${index}.behoerde`}
              required
            />
            <div className="mt-7 pt-px">
              <Checkbox
                checked={vollzug[index]?.aktiv ?? false}
                label={t("fields.Vollzug.aktiv")}
                onChange={() => {
                  return handleCheckboxChange(index);
                }}
              />
            </div>
          </div>
        );
      }}
    </FieldArray>
  );
}

type VollzugDialogStatusType = "error" | "loading" | "problemBehoerde";

function VollzugDialog({
  isOpen,
  mutatePage,
  onClose,
}: {
  isOpen: boolean;
  mutatePage?: () => Promise<unknown>;
  onClose: () => void;
}) {
  const { t } = useI18n();
  const vflzId = useRouter().query.vflzId;
  const [status, setStatus] = useState<VollzugDialogStatusType>();
  const { data, mutate } = useSWR<VollzugDialogQuery>(
    vflzId && [queryVollzug, { vflzId }],
  );
  return (
    <Dialog
      data-test="VollzugDialog"
      isOpen={isOpen}
      onClose={onClose}
      title={t("VflzActionMenu.VollzugDialog.title")}
    >
      <Form<VollzugFormFieldsFragment>
        className="min-w-96"
        model="Vflz"
        onSubmit={({ vollzug }) => {
          setStatus("loading");
          client
            .request<UpdateVollzugMutation>(updateVollzugMutation, {
              data: {
                vflzId,
                vollzug: vollzug.map((v) => {
                  unset(v, "isDeleteable");
                  return removeErfassungMutation(v);
                }),
              },
            })
            .then(({ updateVflzVollzug }) => {
              if (updateVflzVollzug.__typename === "Vflz") {
                onClose();
                setStatus(undefined);
                void mutate();
                void mutatePage?.();
              } else if (updateVflzVollzug.__typename === "ProblemGroup") {
                setStatus("problemBehoerde");
              } else {
                throw new Error("Vollzug failed");
              }
            })
            .catch((error) => {
              captureException(error);
              setStatus("error");
            });
        }}
        values={data?.vflz}
      >
        <VollzugFormFields />
        <div className="mt-8 flex items-center justify-between">
          <div className="text-red-5 max-w-90 text-sm">
            {status === "problemBehoerde"
              ? t("VflzActionMenu.VollzugDialog.problemBehoerde")
              : null}
            {status === "error" ? t("Form.exceptionMessage") : null}
            {status === "loading" ? <Spinner className="h-8" /> : null}
          </div>
          <div className="flex justify-end gap-4">
            <Button onClick={onClose} outline>
              {t("cancel")}
            </Button>
            <Button type="submit">
              {t("VflzActionMenu.VollzugDialog.submit")}
            </Button>
          </div>
        </div>
      </Form>
    </Dialog>
  );
}

type DialogOpenType = "historize" | "vollzug" | false;

export default function VflzActionMenu({
  canEditVollzug,
  hideMenu,
  mutatePage,
  onReset,
}: {
  canEditVollzug?: boolean;
  hideMenu?: boolean;
  mutatePage?: () => Promise<unknown>;
  onReset?: () => void;
}) {
  const { formState } = useFormContext();
  const { t } = useI18n();
  const { query } = useRouter();
  const [isDialogOpen, setIsDialogOpen] = useState<DialogOpenType>(false);
  return (
    <>
      <ActionMenu hideMenu={hideMenu}>
        <ActionMenu.Item href="/vflz/create">
          <PlusIcon />
          <span>{t("vflz.create.title")}</span>
        </ActionMenu.Item>
        {formState.disabled ? null : (
          <ActionMenu.Item href={`/vflz/${query.vflzId?.toString()}/split`}>
            <SplitIcon />
            <span>{t("vflz.split.title")}</span>
          </ActionMenu.Item>
        )}
        {canEditVollzug ? (
          <ActionMenu.Item
            data-test="VflzActionMenu-vollzug"
            onClick={() => {
              return setIsDialogOpen("vollzug");
            }}
          >
            <HashIcon />
            <span>{t("VflzActionMenu.vollzug")}</span>
          </ActionMenu.Item>
        ) : null}
        {formState.disabled ? null : (
          <ActionMenu.Item
            data-test="VflzActionMenu-historize"
            onClick={() => {
              return setIsDialogOpen("historize");
            }}
          >
            <HistorizeIcon />
            <span>{t("VflzActionMenu.historize")}</span>
          </ActionMenu.Item>
        )}
        <ActionMenu.ResetActionItem onReset={onReset} />
      </ActionMenu>
      <HistorizeDialog
        isOpen={isDialogOpen === "historize"}
        onClose={() => {
          return setIsDialogOpen(false);
        }}
      />
      <VollzugDialog
        isOpen={isDialogOpen === "vollzug"}
        mutatePage={mutatePage}
        onClose={() => {
          return setIsDialogOpen(false);
        }}
      />
    </>
  );
}

import { gql } from "graphql-request";
import { useCallback, useEffect, useState } from "react";
import { useFormContext } from "react-hook-form";

import Button from "@/components/Button";
import Field from "@/components/Field";
import Link from "@/components/Link";
import { useI18n } from "@/lib/i18n";
import useDocumentFile, { getDocumentHeaders } from "@/lib/useDocumentFile";
import useSetting from "@/lib/useSetting";

import ClickableUrlField from "../ClickableUrlField";

import TaskForm from "./TaskForm";

import type { UpdateDokumentMutation } from "@/lib/graphql";

import type { TaskProps } from "./Task";

const updateDokumentMutation = gql`
  mutation updateDokument($data: UpdateDokumentInput!) {
    task: updateDokument(data: $data) {
      ... on Dokument {
        __typename
        ...TaskEvents
      }
    }
  }
  ${TaskForm.eventsFragment}
`;

function FileIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="40"
      width="32"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M4 .75h16c.1 0 .18.03.25.08l.07.05 10.8 10.8c.08.08.13.2.13.32v24c0 1.8-1.46 3.25-3.25 3.25H4A3.25 3.25 0 0 1 .75 36V4C.75 2.2 2.21.75 4 .75Z"
        stroke="#D0D5DD"
        strokeWidth="1.5"
      />
      <path d="M20 .5V8a4 4 0 0 0 4 4h7.5" stroke="#D0D5DD" strokeWidth="1.5" />
    </svg>
  );
}

function DocumentSync({
  onDocumentLoad,
}: {
  onDocumentLoad: (data: { dokumentId: string; name: string }) => void;
}) {
  const { watch } = useFormContext();
  const dokument = watch("dokument") as string;
  const documentFile = useDocumentFile(dokument);

  useEffect(() => {
    if (!documentFile) {
      onDocumentLoad({ dokumentId: "", name: "" });
      return;
    }

    onDocumentLoad({
      dokumentId: documentFile.id,
      name: documentFile.metadata.title,
    });
  }, [documentFile, onDocumentLoad]);

  return null;
}

function FileUploadField({ name }: { name: string }) {
  const { t } = useI18n();
  const { setValue, watch } = useFormContext();
  const [dragging, setDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const dokument = watch("dokument") as string;
  const documentFile = useDocumentFile(dokument);
  const displayedMetadata = documentFile?.metadata;
  const title = watch("title") as string;
  const [uploadError, setUploadError] = useState<null | string>(null);

  const onFileSelect = useCallback(
    (file: File) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.set("file", file);
      formData.set("title", file.name);

      xhr.open("POST", "/api/documents");
      if (process.env.NEXT_PUBLIC_ALMA_E2E_TEST_USER) {
        xhr.setRequestHeader(
          "alma-e2e-test-user",
          process.env.NEXT_PUBLIC_ALMA_E2E_TEST_USER,
        );
      }
      setUploadError(null);
      setIsUploading(true);
      xhr.upload.onprogress = function (event) {
        if (event.lengthComputable) {
          const percentComplete = (event.loaded / event.total) * 100;
          setUploadProgress(percentComplete);
        }
      };

      xhr.onload = function () {
        if (xhr.status === 200) {
          setValue("dokument", xhr.responseText, { shouldDirty: true });
          if (title === t("workflow.create.DOKUMENT")) {
            const newTitle =
              file.name.split(".").slice(0, -1).join(".") || file.name;
            setValue("title", newTitle);
          }
        } else {
          if (xhr.status === 413) {
            setUploadError("tooLarge");
          } else {
            setUploadError("generic");
          }
          setUploadProgress(0);
          setValue("dokument", null, { shouldDirty: true });
        }
        setIsUploading(false);
      };

      xhr.onerror = function () {
        setUploadError("generic");
        setIsUploading(false);
        setUploadProgress(0);
      };

      xhr.send(formData);
    },
    [setValue, t, title],
  );

  function handleDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(true);
  }

  function handleDragLeave() {
    setDragging(false);
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files[0]);
    }
  };
  return (
    <Field name={name}>
      <div
        className={`${
          dragging
            ? "border-blue-5 bg-blue-1 border-solid"
            : "border-gray-5 border-dashed hover:border-solid"
        } ${
          displayedMetadata
            ? "flex items-start justify-between"
            : "hover:bg-blue-1 rounded-md border-2"
        }`}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {displayedMetadata ? (
          <>
            <Link
              className="hover:bg-blue-1 mr-2 flex grow gap-2 rounded-lg"
              download={documentFile?.metadata.title}
              href={`/api/documents/${documentFile?.id}/file`}
            >
              <div className="flex items-center gap-2">
                <FileIcon className="shrink-0" />
                <div className="text-xs">
                  <span className="text-gray-8 block font-medium">
                    {displayedMetadata.title}
                  </span>
                  <span className="text-gray-7 block">
                    {`${Math.ceil((displayedMetadata.file_size ?? 0) / 1024)} KB`}
                  </span>
                </div>
              </div>
            </Link>
            <label
              className="border-gray-5 text-gray-7 hover:text-gray-8 inline-flex cursor-pointer items-center justify-center rounded-l-lg border px-3 py-2 text-xs font-semibold hover:bg-white"
              htmlFor="file-upload"
            >
              {t("fields.Task.upload.replace")}
            </label>
            <Button
              className="rounded-l-none"
              download={documentFile?.metadata.title}
              href={`/api/documents/${documentFile?.id}/file`}
            >
              {t("fields.Task.upload.download")}
            </Button>
          </>
        ) : (
          <label
            className="block cursor-pointer p-4 text-center text-sm"
            htmlFor="file-upload"
          >
            {t("fields.Task.upload.selectFile")}
          </label>
        )}
        <input
          className="hidden"
          id="file-upload"
          onChange={handleFileChange}
          type="file"
        />
      </div>
      {isUploading && (
        <div className="bg-blue-1 mt-2 h-1 rounded-full">
          <div
            className="bg-blue-5 h-1 rounded-full"
            style={{ width: `${uploadProgress}%` }}
          />
        </div>
      )}
      {uploadError && (
        <div className="text-red-6 text-xs" data-test="uploadError">
          <span>{t(`fields.Task.upload.error.${uploadError}`)}</span>
        </div>
      )}
    </Field>
  );
}

function DocumentPreview({
  dokument,
  fileName,
}: {
  dokument: string;
  fileName?: string;
}) {
  const { t } = useI18n();
  const [documentPreview, setDocumentPreview] = useState<null | string>(null);

  useEffect(() => {
    if (!dokument) {
      return;
    }
    async function fetchDocumentPreview() {
      const documentPreviewResponse = await fetch(
        `/api/documents/${dokument}/preview`,
        { ...getDocumentHeaders() },
      );
      if (documentPreviewResponse.ok) {
        const preview = await documentPreviewResponse.blob();
        const url = URL.createObjectURL(preview);
        setDocumentPreview(url);
      } else {
        setDocumentPreview(null);
      }
    }
    void fetchDocumentPreview();
  }, [dokument]);

  if (!dokument) {
    return null;
  }

  return (
    <div className="max-w-sm pt-0 lg:pt-10">
      <Link download={fileName} href={`/api/documents/${dokument}/file`}>
        <Field label={t("fields.Task.upload.preview")}>
          <div className="border-gray-5 hover:border-blue-5 overflow-hidden rounded-md border">
            {documentPreview ? (
              <img alt={fileName} src={documentPreview} />
            ) : (
              <div className="mx-auto flex h-96 min-w-64 items-center p-4">
                <span className="text-gray-7 w-full text-center text-sm italic">
                  {t("fields.Task.upload.noPreview")}
                </span>
              </div>
            )}
          </div>
        </Field>
      </Link>
    </div>
  );
}

export default function TaskDokument({ task, ...props }: TaskProps) {
  const [dokument, setDokument] = useState("");
  const [fileName, setFileName] = useState("");
  const [uploadDokumentHidden] = useSetting(
    "ui.fields.task.dokument.hidden",
    false,
  );

  return (
    <div className="flex flex-wrap gap-6 lg:flex-nowrap">
      <TaskForm<UpdateDokumentMutation>
        className="grow space-y-2"
        mutation={updateDokumentMutation}
        showKategorieFields
        task={{
          ...task,
          dokument: "dokument" in task ? task.dokument : null,
        }}
        {...props}
      >
        <DocumentSync
          onDocumentLoad={({ dokumentId, name }) => {
            setDokument(dokumentId);
            setFileName(name);
          }}
        />
        {uploadDokumentHidden ? null : <FileUploadField name="dokument" />}
        <ClickableUrlField name="url" />
      </TaskForm>
      <DocumentPreview dokument={dokument} fileName={fileName} />
    </div>
  );
}

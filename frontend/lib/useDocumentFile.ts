import useSWR from "swr";

interface DocumentMetadata {
  file_size?: number;
  file_type?: string;
  title: string;
}

export interface DocumentFile {
  id: string;
  metadata: DocumentMetadata;
}

function parseDocumentMetadata(value: unknown): DocumentMetadata | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const metadata = value as Record<string, unknown>;
  if (typeof metadata.title !== "string") {
    return null;
  }

  return {
    file_size:
      typeof metadata.file_size === "number" ? metadata.file_size : undefined,
    file_type:
      typeof metadata.file_type === "string" ? metadata.file_type : undefined,
    title: metadata.title,
  };
}

export function getDocumentHeaders() {
  return process.env.NEXT_PUBLIC_ALMA_E2E_TEST_USER
    ? {
        headers: {
          "alma-e2e-test-user": process.env.NEXT_PUBLIC_ALMA_E2E_TEST_USER,
        },
      }
    : {};
}

export function normalizeDocumentId(
  dokument: null | string | undefined,
): string {
  const trimmed = (dokument ?? "").trim();
  if (!trimmed) {
    return "";
  }

  try {
    const parsed: unknown = JSON.parse(trimmed);
    if (typeof parsed === "string") {
      return parsed.trim();
    }
  } catch {
    // Ignore parse errors and fall back to string cleanup below.
  }

  return trimmed.replace(/^"+|"+$/g, "").trim();
}

export default function useDocumentFile(
  dokument: null | string | undefined,
): DocumentFile | null {
  const documentId = normalizeDocumentId(dokument);

  const { data } = useSWR<DocumentFile | null>(
    documentId ? `/api/documents/${documentId}` : null,
    async (url: string) => {
      const response = await fetch(url, {
        ...getDocumentHeaders(),
      });

      if (!response.ok) {
        return null;
      }

      const body: unknown = await response.json();
      const metadata = parseDocumentMetadata(body);
      if (!metadata) {
        return null;
      }

      return {
        id: documentId,
        metadata,
      };
    },
  );

  return data ?? null;
}

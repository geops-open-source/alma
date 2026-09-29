import { Input } from "@headlessui/react";
import { useEffect, useRef, useState } from "react";
import { useFormContext } from "react-hook-form";

import Button from "./Button";
import Field from "./Field";
import EditIcon from "./icons/EditIcon";

export function getValidUrl(value: string): null | string {
  const input = value.trim();
  if (!input) {
    return null;
  }

  // Only accept URLs with explicit protocol or starting with www.
  if (!/^https?:\/\/|^www\./i.test(input)) {
    return null;
  }

  // If the input doesn't have a protocol, prepend https:// to it.
  const urlString = /^https?:\/\//i.test(input) ? input : `https://${input}`;

  try {
    const url = new URL(urlString);
    if (url.username || url.password) {
      return null;
    }
    const hostnameParts = url.hostname.split(".");
    const hasCompleteHostname =
      hostnameParts.length > 1 &&
      hostnameParts.every((part) => {
        return part.length > 0;
      });
    if (
      (url.protocol === "http:" || url.protocol === "https:") &&
      hasCompleteHostname
    ) {
      return url.toString();
    }
    return null;
  } catch {
    return null;
  }
}

export default function ClickableUrlField({ name }: { name: string }) {
  const { setValue, watch } = useFormContext();
  const value = watch(name) as string | undefined;
  const validUrl = getValidUrl(value ?? "");
  const [isEditing, setIsEditing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const prevIsEditingRef = useRef(isEditing);

  useEffect(() => {
    if (isEditing && !prevIsEditingRef.current) {
      inputRef.current?.focus();
    }
    prevIsEditingRef.current = isEditing;
  }, [isEditing]);

  return (
    <Field className="h-18 w-full" name={name}>
      {validUrl && !isEditing ? (
        <div className="flex w-full items-center justify-between gap-2">
          <a
            className="border-gray-5 text-blue-7 w-full rounded-lg border px-3 py-2 text-xs shadow-xs"
            data-test="urlAnchor"
            href={validUrl ?? ""}
            rel="noopener noreferrer"
            target="_blank"
          >
            {value}
          </a>
          <Button
            aria-label="Url edit"
            className="text-gray-8 hover:bg-gray-2! h-8.5 bg-white"
            data-test="urlEditBtn"
            onClick={() => {
              setIsEditing(true);
            }}
            outline
          >
            <EditIcon />
          </Button>
        </div>
      ) : (
        <Input
          className={`border-gray-5 focus:border-blue-4 focus:ring-blue-6/25 disabled:bg-gray-2 disabled:text-gray-6 w-full rounded-lg border bg-white px-3 py-2 text-xs shadow-xs focus:ring-4 focus:outline-hidden`}
          data-test="urlInput"
          name={name}
          onBlur={() => {
            setIsEditing(false);
          }}
          onChange={(evt) => {
            return setValue(name, evt.target.value, { shouldDirty: true });
          }}
          onFocus={() => {
            setIsEditing(true);
          }}
          ref={inputRef}
          value={value ?? ""}
        />
      )}
    </Field>
  );
}

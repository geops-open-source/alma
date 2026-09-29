import { Menu, MenuButton, MenuItems } from "@headlessui/react";
import { useRouter } from "next/router";
import { useCallback, useEffect, useRef, useState } from "react";
import { useFormContext, useFormState } from "react-hook-form";

import Button, { getClassName } from "@/components/Button";
import Dialog from "@/components/Dialog";
import ResetIcon from "@/components/icons/ResetIcon";
import SaveIcon from "@/components/icons/SaveIcon";
import { MenuItem, menuItemsClassName } from "@/components/Menu";
import { useI18n } from "@/lib/i18n";

import type { MenuItemsProps } from "@headlessui/react";

import type { MenuItemProps } from "@/components/Menu";

function DotsIcon() {
  return (
    <svg fill="none" height="20" width="20" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M10.001 10.833a.833.833 0 1 0 0-1.666.833.833 0 0 0 0 1.666ZM10.001 5a.833.833 0 1 0 0-1.667.833.833 0 0 0 0 1.667ZM10.001 16.667a.833.833 0 1 0 0-1.667.833.833 0 0 0 0 1.667Z"
        stroke="#fff"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.667"
      />
    </svg>
  );
}

const anchor: MenuItemsProps["anchor"] = {
  gap: "24px",
  padding: "8px",
  to: "top end",
};

function DirtyFieldsDialog({
  isDirty,
  submitForm,
}: {
  isDirty: boolean;
  submitForm: () => Promise<boolean>;
}) {
  const { t } = useI18n();
  const router = useRouter();
  const [ignore, setIgnore] = useState(false);
  const [nextPath, setNextPath] = useState<string>();

  useEffect(() => {
    const checkDirtyFields = (
      newNextPath: string,
      { shallow }: { shallow: boolean },
    ) => {
      const searchParams = new URLSearchParams(newNextPath.split("?")[1]);
      const ignoreDirtyFields =
        searchParams.get("ignoreDirtyFields") === "true";

      if (
        isDirty &&
        ignore === false &&
        shallow === false &&
        ignoreDirtyFields === false
      ) {
        setNextPath(newNextPath);
        router.events.emit("routeChangeError");
        // eslint-disable-next-line @typescript-eslint/only-throw-error
        throw "cancelRouteChange"; // the way to cancel a route change in Next.js
      }
    };
    router.events.on("routeChangeStart", checkDirtyFields);
    return () => {
      return router.events.off("routeChangeStart", checkDirtyFields);
    };
  }, [ignore, isDirty, router]);

  const discard = useCallback(() => {
    setIgnore(true);
    if (nextPath) {
      void router.push(nextPath);
    }
  }, [nextPath, router]);

  const save = useCallback(async () => {
    const isValid = await submitForm();
    if (isValid) {
      setIgnore(true);
      if (nextPath && window.location.pathname.startsWith("/vflz/")) {
        const vflzId = window.location.pathname.split("/")[2];
        void router.push(nextPath.replace(/\/vflz\/[^/]+/, `/vflz/${vflzId}`));
      } else if (nextPath) {
        void router.push(nextPath);
      }
    } else {
      setNextPath(undefined);
    }
  }, [nextPath, router, submitForm]);

  return (
    <Dialog
      data-test="DirtyFieldsDialog"
      isOpen={nextPath !== undefined}
      onClose={() => {
        return setNextPath(undefined);
      }}
      title={t("VflzActionMenu.DirtyFieldsDialog.title")}
    >
      {t("VflzActionMenu.DirtyFieldsDialog.message")}
      <div className="mt-6 flex justify-end space-x-4">
        <Button data-test="DirtyFieldsDialog-discard" onClick={discard} outline>
          {t("VflzActionMenu.DirtyFieldsDialog.discard")}
        </Button>
        <Button
          onClick={() => {
            return void save();
          }}
        >
          {t("VflzActionMenu.DirtyFieldsDialog.save")}
        </Button>
      </div>
    </Dialog>
  );
}

function useSubmitForm() {
  const submitButtonRef = useRef<HTMLButtonElement>(null);
  const { errors, isSubmitting } = useFormState();
  const errorsRef = useRef(errors);
  const isStarted = useRef(false);

  useEffect(() => {
    errorsRef.current = errors;
  }, [errors]);

  useEffect(() => {
    if (isSubmitting === false) {
      // Reset the isStarted flag after submission
      isStarted.current = false;
    }
  }, [isSubmitting]);

  // submit form and return if form is valid after submission
  const submitForm = async () => {
    isStarted.current = true;
    submitButtonRef.current?.click();
    return new Promise<boolean>((resolve) => {
      function checkForm() {
        if (isStarted.current === false) {
          resolve(Object.keys(errorsRef.current).length === 0);
        } else {
          setTimeout(checkForm, 200);
        }
      }

      checkForm();
    });
  };

  return { submitButtonRef, submitForm };
}

function ActionMenu({
  children,
  disableSubmit,
  hideMenu,
}: React.PropsWithChildren<{ disableSubmit?: boolean; hideMenu?: boolean }>) {
  const { formState } = useFormContext();
  const { t } = useI18n();
  const isDirty = Object.keys(formState.dirtyFields).length > 0;
  const { submitButtonRef, submitForm } = useSubmitForm();

  return (
    <>
      <div className="pointer-events-none fixed bottom-0 left-0 z-20 w-full">
        <div className="flex flex-row-reverse pr-8 pb-8 2xl:container 2xl:mx-auto">
          <div
            className="pointer-events-auto space-x-px rounded-xl bg-white/80 p-1 text-right shadow-xl backdrop-blur-sm"
            data-test="ActionMenu"
          >
            <Button
              className={`space-x-2 ${hideMenu ? "" : "rounded-r-none"}`}
              disabled={isDirty === false || disableSubmit}
              ref={submitButtonRef}
              type="submit"
            >
              <SaveIcon />
              <span>{t("VflzActionMenu.save")}</span>
            </Button>
            {hideMenu ? null : (
              <Menu>
                <MenuButton
                  className={getClassName("bg-blue-7 rounded-l-none")}
                >
                  <DotsIcon />
                </MenuButton>
                <MenuItems
                  anchor={anchor}
                  className={`${menuItemsClassName} z-30`}
                  modal={false}
                >
                  {children}
                </MenuItems>
              </Menu>
            )}
          </div>
        </div>
      </div>
      <DirtyFieldsDialog isDirty={isDirty} submitForm={submitForm} />
    </>
  );
}

ActionMenu.Item = function ActionMenuItem({
  children,
  ...props
}: { children: React.ReactNode } & MenuItemProps) {
  return (
    <MenuItem {...props} className="flex space-x-2">
      {children}
    </MenuItem>
  );
};

ActionMenu.ResetActionItem = function ActionMenuResetItem({
  onReset,
}: {
  onReset?: () => void;
}) {
  const { t } = useI18n();
  const { formState, reset } = useFormContext();
  const isDirty = Object.keys(formState.dirtyFields).length > 0;
  return (
    <ActionMenu.Item
      disabled={!isDirty}
      onClick={() => {
        reset();
        if (onReset) {
          onReset();
        }
      }}
    >
      <ResetIcon />
      <span>{t("VflzActionMenu.reset")}</span>
    </ActionMenu.Item>
  );
};

export default ActionMenu;

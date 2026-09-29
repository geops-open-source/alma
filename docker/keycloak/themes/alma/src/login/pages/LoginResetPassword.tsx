import { getKcClsx } from "keycloakify/login/lib/kcClsx";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import type { PageProps } from "keycloakify/login/pages/PageProps";
import type { KcContext } from "../KcContext";
import type { I18n } from "../i18n";

export default function LoginResetPassword(
  props: PageProps<
    Extract<KcContext, { pageId: "login-reset-password.ftl" }>,
    I18n
  >,
) {
  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { kcClsx } = getKcClsx({
    doUseDefaultCss,
    classes,
  });

  const { url, realm, auth, messagesPerField } = kcContext;

  const { msg, msgStr } = i18n;

  return (
    <Template
      kcContext={kcContext}
      i18n={i18n}
      doUseDefaultCss={doUseDefaultCss}
      classes={classes}
      displayInfo
      displayMessage={!messagesPerField.existsError("username")}
      infoNode={
        realm.duplicateEmailsAllowed
          ? msg("emailInstructionUsername")
          : msg("emailInstruction")
      }
      headerNode={msg("emailForgotTitle")}
    >
      <form
        id="kc-reset-password-form"
        className={kcClsx("kcFormClass")}
        action={url.loginAction}
        method="post"
      >
        <div className={kcClsx("kcFormGroupClass")}>
          <div className={kcClsx("kcInputWrapperClass")}>
            <input
              type="text"
              id="username"
              name="username"
              className={kcClsx("kcInputClass")}
              autoFocus
              defaultValue={auth.attemptedUsername ?? ""}
              aria-invalid={messagesPerField.existsError("username")}
              placeholder={
                !realm.loginWithEmailAllowed
                  ? msgStr("username")
                  : !realm.registrationEmailAsUsername
                    ? msgStr("usernameOrEmail")
                    : msgStr("email")
              }
            />
            {messagesPerField.existsError("username") && (
              <span
                id="input-error-username"
                className={kcClsx("kcInputErrorMessageClass")}
                aria-live="polite"
                dangerouslySetInnerHTML={{
                  __html: kcSanitize(messagesPerField.get("username")),
                }}
              />
            )}
          </div>
        </div>
        <div className={kcClsx("kcFormGroupClass", "kcFormSettingClass")}>
          <div className="p-6 text-center">
            <a href={url.loginUrl} className="text-blue-650 hover:text-blue-700 font-semibold">
              {msg("backToLogin")}
            </a>
          </div>

          <div id="kc-form-buttons" className={kcClsx("kcFormButtonsClass")}>
            <input
              className="cursor-pointer border-none bg-blue-600 font-semibold text-white shadow-xs hover:bg-blue-700"
              type="submit"
              value={msgStr("doSubmit")}
            />
          </div>
        </div>
      </form>
    </Template>
  );
}

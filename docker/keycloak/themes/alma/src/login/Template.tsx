import { useEffect } from "react";
import { clsx } from "keycloakify/tools/clsx";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import type { TemplateProps } from "keycloakify/login/TemplateProps";
import { getKcClsx } from "keycloakify/login/lib/kcClsx";
import { useSetClassName } from "keycloakify/tools/useSetClassName";
import { useInitialize } from "keycloakify/login/Template.useInitialize";
import type { I18n } from "./i18n";
import type { KcContext } from "./KcContext";

import background from "./background.svg";
import logo from "./logo.svg";

export default function Template(props: TemplateProps<KcContext, I18n>) {
  const {
    displayInfo = false,
    displayMessage = true,
    displayRequiredFields = false,
    headerNode,
    socialProvidersNode = null,
    infoNode = null,
    documentTitle,
    kcContext,
    i18n,
    doUseDefaultCss,
    classes,
    children,
  } = props;

  const { kcClsx } = getKcClsx({ doUseDefaultCss, classes });

  const { msg, msgStr } = i18n;

  const { realm, auth, url, message, isAppInitiatedAction } = kcContext;

  useEffect(() => {
    document.title = documentTitle ?? msgStr("loginTitle", realm.displayName);
  }, []);

  useSetClassName({
    qualifiedName: "body",
    className: "bg-gray-300",
  });

  const { isReadyToRender } = useInitialize({ kcContext, doUseDefaultCss });

  if (!isReadyToRender) {
    return null;
  }

  return (
    <div className="h-screen overflow-scroll">
      <img className="absolute top-0 left-0" src={background} />
      <div className="relative top-1/2 left-1/2 flex w-md -translate-x-1/2 -translate-y-1/2 flex-col rounded-2xl border border-white/50 bg-white/20 p-8 shadow-sm inset-shadow-sm backdrop-blur-sm">
        <div className="mb-8 flex justify-center">
          <img alt="alma Logo" src={logo} />
        </div>
        <div className={kcClsx("kcFormCardClass")}>
          <header className={kcClsx("kcFormHeaderClass")}>
            {(() => {
              const node = !(
                auth !== undefined &&
                auth.showUsername &&
                !auth.showResetCredentials
              ) ? (
                <h1 className="mb-8 text-center text-2xl font-semibold text-gray-900">
                  {headerNode}
                </h1>
              ) : (
                <div id="kc-username" className={kcClsx("kcFormGroupClass")}>
                  <label id="kc-attempted-username" className="text-center text-2xl font-semibold text-gray-900 block">
                    {auth.attemptedUsername}
                  </label>
                  <div className="p-6 text-center">
                    <a
                      className="text-blue-650 hover:text-blue-700 font-semibold"
                      id="reset-login"
                      href={url.loginRestartFlowUrl}
                      aria-label={msgStr("restartLoginTooltip")}
                    >
                      <div className="kc-login-tooltip">
                        <i className={kcClsx("kcResetFlowIcon")}></i>
                        <span className="kc-tooltip-text">
                          {msg("restartLoginTooltip")}
                        </span>
                      </div>
                    </a>
                  </div>
                </div>
              );

              if (displayRequiredFields) {
                return (
                  <div className={kcClsx("kcContentWrapperClass")}>
                    <div
                      className={clsx(
                        kcClsx("kcLabelWrapperClass"),
                        "subtitle",
                      )}
                    >
                      <span className="subtitle">
                        <span className="required">*</span>
                        {msg("requiredFields")}
                      </span>
                    </div>
                    <div className="col-md-10">{node}</div>
                  </div>
                );
              }

              return node;
            })()}
          </header>
          <div id="kc-content">
            <div id="kc-content-wrapper">
              {/* App-initiated actions should not see warning messages about the need to complete the action during login. */}
              {displayMessage &&
                message !== undefined &&
                (message.type !== "warning" || !isAppInitiatedAction) && (
                  <div
                    className={clsx(
                      `alert-${message.type}`,
                      kcClsx("kcAlertClass"),
                      `pf-m-${message?.type === "error" ? "danger" : message.type}`,
                    )}
                  >
                    <div className="pf-c-alert__icon">
                      {message.type === "success" && (
                        <span
                          className={kcClsx("kcFeedbackSuccessIcon")}
                        ></span>
                      )}
                      {message.type === "warning" && (
                        <span
                          className={kcClsx("kcFeedbackWarningIcon")}
                        ></span>
                      )}
                      {message.type === "error" && (
                        <span className={kcClsx("kcFeedbackErrorIcon")}></span>
                      )}
                      {message.type === "info" && (
                        <span className={kcClsx("kcFeedbackInfoIcon")}></span>
                      )}
                    </div>
                    <span
                      className={kcClsx("kcAlertTitleClass")}
                      dangerouslySetInnerHTML={{
                        __html: kcSanitize(message.summary),
                      }}
                    />
                  </div>
                )}
              {socialProvidersNode}
              {children}
              {auth !== undefined && auth.showTryAnotherWayLink && (
                <form
                  id="kc-select-try-another-way-form"
                  action={url.loginAction}
                  method="post"
                >
                  <div className={kcClsx("kcFormGroupClass")}>
                    <input type="hidden" name="tryAnotherWay" value="on" />
                    <a
                      href="#"
                      id="try-another-way"
                      onClick={() => {
                        document.forms[
                          "kc-select-try-another-way-form" as never
                        ].requestSubmit();
                        return false;
                      }}
                    >
                      {msg("doTryAnotherWay")}
                    </a>
                  </div>
                </form>
              )}
              {displayInfo && (
                <div id="kc-info" className="mt-6 text-center text-sm">
                  <div
                    id="kc-info-wrapper"
                    className={kcClsx("kcInfoAreaWrapperClass")}
                  >
                    {infoNode}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

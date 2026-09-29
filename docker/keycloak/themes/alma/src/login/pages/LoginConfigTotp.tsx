import { getKcClsx, KcClsx } from "keycloakify/login/lib/kcClsx";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import type { PageProps } from "keycloakify/login/pages/PageProps";
import type { KcContext } from "../KcContext";
import type { I18n } from "../i18n";

export default function LoginConfigTotp(
  props: PageProps<
    Extract<KcContext, { pageId: "login-config-totp.ftl" }>,
    I18n
  >,
) {
  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { kcClsx } = getKcClsx({
    doUseDefaultCss,
    classes,
  });

  const { url, isAppInitiatedAction, totp, mode, messagesPerField } = kcContext;

  const { msg, msgStr, advancedMsg } = i18n;

  return (
    <Template
      kcContext={kcContext}
      i18n={i18n}
      doUseDefaultCss={doUseDefaultCss}
      classes={classes}
      headerNode={msg("loginTotpTitle")}
      displayMessage={!messagesPerField.existsError("totp", "userLabel")}
    >
      <>
        <ol id="kc-totp-settings" className="list-decimal space-y-2 ml-4">
          <li>
            <p>{msg("loginTotpStep1")}</p>

            <ul id="kc-totp-supported-apps" className="list-disc list-inside">
              {totp.supportedApplications.map((app) => (
                <li key={app}>{advancedMsg(app)}</li>
              ))}
            </ul>
          </li>

          {mode == "manual" ? (
            <>
              <li>
                <p>{msg("loginTotpManualStep2")}</p>
                <p className="font-mono py-1">
                  <span id="kc-totp-secret-key">{totp.totpSecretEncoded}</span>
                </p>
                <p>
                  <a href={totp.qrUrl} id="mode-barcode" className="text-blue-650 hover:text-blue-700 font-semibold">
                    {msg("loginTotpScanBarcode")}
                  </a>
                </p>
              </li>
              <li>
                <p>{msg("loginTotpManualStep3")}</p>
                <ul className="list-disc list-inside">
                  <li id="kc-totp-type">
                    {msg("loginTotpType")}:{" "}
                    {msg(`loginTotp.${totp.policy.type}`)}
                  </li>
                  <li id="kc-totp-algorithm">
                    {msg("loginTotpAlgorithm")}: {totp.policy.getAlgorithmKey()}
                  </li>
                  <li id="kc-totp-digits">
                    {msg("loginTotpDigits")}: {totp.policy.digits}
                  </li>
                  {totp.policy.type === "totp" ? (
                    <li id="kc-totp-period">
                      {msg("loginTotpInterval")}: {totp.policy.period}
                    </li>
                  ) : (
                    <li id="kc-totp-counter">
                      {msg("loginTotpCounter")}: {totp.policy.initialCounter}
                    </li>
                  )}
                </ul>
              </li>
            </>
          ) : (
            <li>
              <p>{msg("loginTotpStep2")}</p>
              <img
                id="kc-totp-secret-qr-code"
                src={`data:image/png;base64, ${totp.totpSecretQrCode}`}
                alt="Figure: Barcode"
              />
              <p className="mt-2">
                <a href={totp.manualUrl} id="mode-manual" className="text-blue-650 hover:text-blue-700 font-semibold">
                  {msg("loginTotpUnableToScan")}
                </a>
              </p>
            </li>
          )}
          <li>
            <p>{msg("loginTotpStep3")}</p>
            <p>{msg("loginTotpStep3DeviceName")}</p>
          </li>
        </ol>

        <form
          action={url.loginAction}
          className="space-y-4 mt-4"
          id="kc-totp-settings-form"
          method="post"
        >
          <div className={kcClsx("kcFormGroupClass")}>
            <div className={kcClsx("kcInputWrapperClass")}>
              <input
                type="text"
                id="totp"
                name="totp"
                autoComplete="off"
                className={kcClsx("kcInputClass")}
                aria-invalid={messagesPerField.existsError("totp")}
                placeholder={msgStr("authenticatorCode") + " *"}
              />

              {messagesPerField.existsError("totp") && (
                <span
                  id="input-error-otp-code"
                  className={kcClsx("kcInputErrorMessageClass")}
                  aria-live="polite"
                  dangerouslySetInnerHTML={{
                    __html: kcSanitize(messagesPerField.get("totp")),
                  }}
                />
              )}
            </div>
            <input
              type="hidden"
              id="totpSecret"
              name="totpSecret"
              value={totp.totpSecret}
            />
            {mode && <input type="hidden" id="mode" value={mode} />}
          </div>

          <div className={kcClsx("kcFormGroupClass")}>
            <div className={kcClsx("kcInputWrapperClass")}>
              <input
                type="text"
                id="userLabel"
                name="userLabel"
                autoComplete="off"
                className={kcClsx("kcInputClass")}
                aria-invalid={messagesPerField.existsError("userLabel")}
                placeholder={msgStr("loginTotpDeviceName") + (totp.otpCredentials.length >= 1 ? " *" : "")}
              />
              {messagesPerField.existsError("userLabel") && (
                <span
                  id="input-error-otp-label"
                  className={kcClsx("kcInputErrorMessageClass")}
                  aria-live="polite"
                  dangerouslySetInnerHTML={{
                    __html: kcSanitize(messagesPerField.get("userLabel")),
                  }}
                />
              )}
            </div>
          </div>

          <div className={kcClsx("kcFormGroupClass")}>
            <LogoutOtherSessions kcClsx={kcClsx} i18n={i18n} />
          </div>

          {isAppInitiatedAction ? (
            <>
              <input
                type="submit"
                className={kcClsx(
                  "kcButtonClass",
                  "kcButtonPrimaryClass",
                  "kcButtonLargeClass",
                )}
                id="saveTOTPBtn"
                value={msgStr("doSubmit")}
              />
              <button
                type="submit"
                className={kcClsx(
                  "kcButtonClass",
                  "kcButtonDefaultClass",
                  "kcButtonLargeClass",
                  "kcButtonLargeClass",
                )}
                id="cancelTOTPBtn"
                name="cancel-aia"
                value="true"
              >
                {msg("doCancel")}
              </button>
            </>
          ) : (
            <input
              type="submit"
              className="cursor-pointer font-semibold shadow-xs border-none bg-blue-600 text-white hover:bg-blue-700"
              id="saveTOTPBtn"
              value={msgStr("doSubmit")}
            />
          )}
        </form>
      </>
    </Template>
  );
}

function LogoutOtherSessions(props: { kcClsx: KcClsx; i18n: I18n }) {
  const { kcClsx, i18n } = props;

  const { msg } = i18n;

  return (
    <div id="kc-form-options" className={kcClsx("kcFormOptionsClass")}>
      <div className={kcClsx("kcFormOptionsWrapperClass")}>
        <div className="checkbox">
          <label className="flex items-center">
            <input
              type="checkbox"
              id="logout-sessions"
              name="logout-sessions"
              value="on"
              defaultChecked={true}
              className="shadow-none w-fit mr-2"
            />
            {msg("logoutOtherSessions")}
          </label>
        </div>
      </div>
    </div>
  );
}

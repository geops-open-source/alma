/**
 * Combined Username + Password login page (login.ftl) with optional WebAuthn passkey support.
 * Renders standard login form plus conditional passkey authenticator section.
 */
import type { JSX } from "keycloakify/tools/JSX";
import { useState } from "react";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import { useIsPasswordRevealed } from "keycloakify/tools/useIsPasswordRevealed";
import { clsx } from "keycloakify/tools/clsx";
import type { PageProps } from "keycloakify/login/pages/PageProps";
import { getKcClsx, type KcClsx } from "keycloakify/login/lib/kcClsx";
import type { KcContext } from "../KcContext";
import type { I18n } from "../i18n";
import { useScript } from "keycloakify/login/pages/Login.useScript";

export default function Login(
  props: PageProps<Extract<KcContext, { pageId: "login.ftl" }>, I18n>,
) {
  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { kcClsx } = getKcClsx({
    doUseDefaultCss,
    classes,
  });

  const {
    social,
    realm,
    url,
    usernameHidden,
    login,
    auth,
    registrationDisabled,
    messagesPerField,
    enableWebAuthnConditionalUI,
    authenticators,
  } = kcContext;

  const { msg, msgStr } = i18n;

  const [isLoginButtonDisabled, setIsLoginButtonDisabled] = useState(false);

  const webAuthnButtonId = "authenticateWebAuthnButton";

  useScript({
    webAuthnButtonId,
    kcContext,
    i18n,
  });

  const params = new URLSearchParams(window.location.search);
  const username = params.get("username") ?? "";
  const password = params.get("password") ?? "";

  return (
    <Template
      kcContext={kcContext}
      i18n={i18n}
      doUseDefaultCss={doUseDefaultCss}
      classes={classes}
      displayMessage={!messagesPerField.existsError("username", "password")}
      headerNode={msg("loginAccountTitle")}
      displayInfo={
        realm.password && realm.registrationAllowed && !registrationDisabled
      }
      infoNode={
        <div id="kc-registration-container">
          <div id="kc-registration">
            <span>
              {msg("noAccount")}{" "}
              <a tabIndex={8} href={url.registrationUrl}>
                {msg("doRegister")}
              </a>
            </span>
          </div>
        </div>
      }
      socialProvidersNode={
        <>
          {realm.password &&
            social?.providers !== undefined &&
            social.providers.length !== 0 && (
              <div
                id="kc-social-providers"
                className={kcClsx("kcFormSocialAccountSectionClass")}
              >
                <ul className="space-y-4">
                  {social.providers.map((...[p]) => (
                    <li key={p.alias}>
                      <a
                        id={`social-${p.alias}`}
                        className="block rounded-lg border-none bg-blue-600 px-3.5 py-2.5 text-center font-semibold text-white shadow-xs hover:bg-blue-700"
                        type="button"
                        href={p.loginUrl}
                      >
                        {p.iconClasses && (
                          <i
                            className={clsx(
                              kcClsx("kcCommonLogoIdP"),
                              p.iconClasses,
                            )}
                            aria-hidden="true"
                          ></i>
                        )}
                        <span
                          className={clsx(
                            kcClsx("kcFormSocialAccountNameClass"),
                            p.iconClasses && "kc-social-icon-text",
                          )}
                          dangerouslySetInnerHTML={{
                            __html: kcSanitize(p.displayName),
                          }}
                        ></span>
                      </a>
                    </li>
                  ))}
                </ul>
                <hr className="z-10 my-8 text-gray-500" />
              </div>
            )}
        </>
      }
    >
      <div id="kc-form">
        <div id="kc-form-wrapper">
          {realm.password && (
            <form
              id="kc-form-login"
              onSubmit={() => {
                setIsLoginButtonDisabled(true);
                return true;
              }}
              action={url.loginAction}
              method="post"
            >
              <div className="space-y-4">
                {!usernameHidden && (
                  <div>
                    <input
                      tabIndex={2}
                      id="username"
                      name="username"
                      defaultValue={login.username ?? username}
                      type="text"
                      autoFocus
                      autoComplete="username"
                      aria-invalid={messagesPerField.existsError(
                        "username",
                        "password",
                      )}
                      placeholder={
                        !realm.loginWithEmailAllowed
                          ? msgStr("username")
                          : !realm.registrationEmailAsUsername
                            ? msgStr("usernameOrEmail")
                            : msgStr("email")
                      }
                    />
                    {messagesPerField.existsError("username", "password") && (
                      <span
                        id="input-error"
                        className={kcClsx("kcInputErrorMessageClass")}
                        aria-live="polite"
                        dangerouslySetInnerHTML={{
                          __html: kcSanitize(
                            messagesPerField.getFirstError(
                              "username",
                              "password",
                            ),
                          ),
                        }}
                      />
                    )}
                  </div>
                )}

                <div>
                  <PasswordWrapper
                    kcClsx={kcClsx}
                    i18n={i18n}
                    passwordInputId="password"
                  >
                    <input
                      tabIndex={3}
                      id="password"
                      className={kcClsx("kcInputClass")}
                      name="password"
                      type="password"
                      defaultValue={password}
                      autoComplete="current-password"
                      aria-invalid={messagesPerField.existsError(
                        "username",
                        "password",
                      )}
                      placeholder={msgStr("password")}
                    />
                  </PasswordWrapper>
                  {usernameHidden &&
                    messagesPerField.existsError("username", "password") && (
                      <span
                        id="input-error"
                        className={kcClsx("kcInputErrorMessageClass")}
                        aria-live="polite"
                        dangerouslySetInnerHTML={{
                          __html: kcSanitize(
                            messagesPerField.getFirstError(
                              "username",
                              "password",
                            ),
                          ),
                        }}
                      />
                    )}
                </div>
              </div>

              <div className={kcClsx("kcFormGroupClass", "kcFormSettingClass")}>
                <div id="kc-form-options">
                  {realm.rememberMe && !usernameHidden && (
                    <div className="checkbox">
                      <label>
                        <input
                          tabIndex={5}
                          id="rememberMe"
                          name="rememberMe"
                          type="checkbox"
                          defaultChecked={!!login.rememberMe}
                        />{" "}
                        {msg("rememberMe")}
                      </label>
                    </div>
                  )}
                </div>
                <div className="p-6 text-center">
                  {realm.resetPasswordAllowed && (
                    <span>
                      <a
                        tabIndex={6}
                        href={url.loginResetCredentialsUrl}
                        className="text-blue-650 hover:text-blue-700 font-semibold"
                      >
                        {msg("doForgotPassword")}
                      </a>
                    </span>
                  )}
                </div>
              </div>

              <div id="kc-form-buttons" className={kcClsx("kcFormGroupClass")}>
                <input
                  type="hidden"
                  id="id-hidden-input"
                  name="credentialId"
                  value={auth.selectedCredential}
                />
                <input
                  tabIndex={7}
                  disabled={isLoginButtonDisabled}
                  className={`cursor-pointer font-semibold shadow-xs ${
                    realm.password &&
                    social?.providers !== undefined &&
                    social.providers.length !== 0
                      ? "border border-gray-500 text-gray-700 hover:text-gray-900"
                      : "border-none bg-blue-600 text-white hover:bg-blue-700"
                  }`}
                  name="login"
                  id="kc-login"
                  type="submit"
                  value={msgStr("doLogIn")}
                />
              </div>
            </form>
          )}
        </div>
      </div>
      {enableWebAuthnConditionalUI && (
        <>
          <form id="webauth" action={url.loginAction} method="post">
            <input type="hidden" id="clientDataJSON" name="clientDataJSON" />
            <input
              type="hidden"
              id="authenticatorData"
              name="authenticatorData"
            />
            <input type="hidden" id="signature" name="signature" />
            <input type="hidden" id="credentialId" name="credentialId" />
            <input type="hidden" id="userHandle" name="userHandle" />
            <input type="hidden" id="error" name="error" />
          </form>

          {authenticators !== undefined &&
            authenticators.authenticators.length !== 0 && (
              <>
                <form id="authn_select" className={kcClsx("kcFormClass")}>
                  {authenticators.authenticators.map((authenticator, i) => (
                    <input
                      key={i}
                      type="hidden"
                      name="authn_use_chk"
                      readOnly
                      value={authenticator.credentialId}
                    />
                  ))}
                </form>
              </>
            )}
          <br />

          <input
            id={webAuthnButtonId}
            type="button"
            className={kcClsx(
              "kcButtonClass",
              "kcButtonDefaultClass",
              "kcButtonBlockClass",
              "kcButtonLargeClass",
            )}
            value={msgStr("passkey-doAuthenticate")}
          />
        </>
      )}
    </Template>
  );
}

function PasswordWrapper(props: {
  kcClsx: KcClsx;
  i18n: I18n;
  passwordInputId: string;
  children: JSX.Element;
}) {
  const { kcClsx, i18n, passwordInputId, children } = props;

  const { msgStr } = i18n;

  const { isPasswordRevealed, toggleIsPasswordRevealed } =
    useIsPasswordRevealed({ passwordInputId });

  return (
    <div className={kcClsx("kcInputGroup")}>
      {children}
      <button
        type="button"
        className={kcClsx("kcFormPasswordVisibilityButtonClass")}
        aria-label={msgStr(
          isPasswordRevealed ? "hidePassword" : "showPassword",
        )}
        aria-controls={passwordInputId}
        onClick={toggleIsPasswordRevealed}
      >
        <i
          className={kcClsx(
            isPasswordRevealed
              ? "kcFormPasswordVisibilityIconHide"
              : "kcFormPasswordVisibilityIconShow",
          )}
          aria-hidden
        />
      </button>
    </div>
  );
}

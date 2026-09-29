import { Suspense, lazy } from "react";
import type { ClassKey } from "keycloakify/login";
import type { KcContext } from "./KcContext";
import { useI18n } from "./i18n";
import DefaultPage from "keycloakify/login/DefaultPage";
import Template from "./Template";

import "./tailwind.css";

const Error = lazy(() => import("./pages/Error"));
const Login = lazy(() => import("./pages/Login"));
const LoginConfigTotp = lazy(() => import("./pages/LoginConfigTotp"));
const LoginIdpLinkConfirm = lazy(() => import("./pages/LoginIdpLinkConfirm"));
const LoginOtp = lazy(() => import("./pages/LoginOtp"));
const LoginResetPassword = lazy(() => import("./pages/LoginResetPassword"));

const UserProfileFormFields = lazy(
  () => import("keycloakify/login/UserProfileFormFields"),
);

const doMakeUserConfirmPassword = true;

export default function KcPage(props: { kcContext: KcContext }) {
  const { kcContext } = props;

  const { i18n } = useI18n({ kcContext });

  return (
    <Suspense>
      {(() => {
        switch (kcContext.pageId) {
          case "error.ftl": return (
            <Error
              kcContext={kcContext}
              i18n={i18n}
              classes={classes}
              Template={Template}
              doUseDefaultCss={false}
            />
          );
          case "login.ftl":
            return (
              <Login
                kcContext={kcContext}
                i18n={i18n}
                classes={classes}
                Template={Template}
                doUseDefaultCss={false}
              />
            );
          case "login-config-totp.ftl": return (
            <LoginConfigTotp
              kcContext={kcContext}
              i18n={i18n}
              classes={classes}
              Template={Template}
              doUseDefaultCss={false}
            />
          );
          case "login-idp-link-confirm.ftl": return (
            <LoginIdpLinkConfirm
              kcContext={kcContext}
              i18n={i18n}
              classes={classes}
              Template={Template}
              doUseDefaultCss={false}
            />
          );
          case "login-otp.ftl": return (
            <LoginOtp
              kcContext={kcContext}
              i18n={i18n}
              classes={classes}
              Template={Template}
              doUseDefaultCss={false}
            />
          );
          case "login-reset-password.ftl":
            return (
              <LoginResetPassword
                kcContext={kcContext}
                i18n={i18n}
                classes={classes}
                Template={Template}
                doUseDefaultCss={false}
              />
            );
          default:
            return (
              <DefaultPage
                kcContext={kcContext}
                i18n={i18n}
                classes={classes}
                Template={Template}
                doUseDefaultCss={false}
                UserProfileFormFields={UserProfileFormFields}
                doMakeUserConfirmPassword={doMakeUserConfirmPassword}
              />
            );
        }
      })()}
    </Suspense>
  );
}

const classes = {} satisfies { [key in ClassKey]?: string };

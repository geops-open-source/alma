import type { PageProps } from "keycloakify/login/pages/PageProps";
import type { KcContext } from "../KcContext";
import type { I18n } from "../i18n";

export default function LoginIdpLinkConfirm(
  props: PageProps<
    Extract<KcContext, { pageId: "login-idp-link-confirm.ftl" }>,
    I18n
  >,
) {
  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { url, idpAlias } = kcContext;

  const { msg } = i18n;

  return (
    <Template
      kcContext={kcContext}
      i18n={i18n}
      doUseDefaultCss={doUseDefaultCss}
      classes={classes}
      headerNode={msg("confirmLinkIdpTitle")}
    >
      <form id="kc-register-form" action={url.loginAction} method="post">
        <div className="space-y-8 mt-8">
          <button
            type="submit"
            className="text-blue-650 hover:text-blue-700 cursor-pointer font-semibold text-center w-full"
            name="submitAction"
            id="updateProfile"
            value="updateProfile"
          >
            {msg("confirmLinkIdpReviewProfile")}
          </button>
          <button
            type="submit"
            className="w-full rounded-lg px-3.5 py-2.5  focus:outline-none cursor-pointer font-semibold shadow-xs border-none bg-blue-600 text-white hover:bg-blue-700"
            name="submitAction"
            id="linkAccount"
            value="linkAccount"
          >
            {msg("confirmLinkIdpContinue", idpAlias)}
          </button>
        </div>
      </form>
    </Template>
  );
}

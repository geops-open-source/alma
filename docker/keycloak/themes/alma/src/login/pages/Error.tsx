import type { PageProps } from "keycloakify/login/pages/PageProps";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import type { KcContext } from "../KcContext";
import type { I18n } from "../i18n";

export default function Error(
  props: PageProps<Extract<KcContext, { pageId: "error.ftl" }>, I18n>,
) {
  const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

  const { message, client, skipLink } = kcContext;

  const { msg } = i18n;

  return (
    <Template
      kcContext={kcContext}
      i18n={i18n}
      doUseDefaultCss={doUseDefaultCss}
      classes={classes}
      displayMessage={false}
      headerNode={msg("errorTitle")}
    >
      <div id="kc-error-message">
        <p
          className="text-center"
          dangerouslySetInnerHTML={{ __html: kcSanitize(message.summary) }}
        />
        {!skipLink && client !== undefined && client.baseUrl !== undefined && (
          <div className="p-6 text-center">
            <a id="backToApplication" href={client.baseUrl} className="text-blue-650 hover:text-blue-700 font-semibold">
              {msg("backToApplication")}
            </a>
          </div>
        )}
      </div>
    </Template>
  );
}

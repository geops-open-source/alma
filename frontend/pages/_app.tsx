import { SWRConfig, type SWRConfiguration } from "swr";

import client from "@/lib/client";
import fonts from "@/lib/fonts";
import { I18n } from "@/lib/i18n";

import "@/lib/tailwind.css";

import type { RequestDocument, Variables } from "graphql-request";
import type { AppProps } from "next/app";
import type { PropsWithChildren } from "react";

const fetcher = (params: [RequestDocument, Variables] | RequestDocument) => {
  const [document, variables] = Array.isArray(params) ? params : [params];
  return client.request(document, variables);
};

const HTTPStatusUnauthorized = 401;

function onError(error: { response?: { status?: number } }) {
  if (error.response?.status === HTTPStatusUnauthorized) {
    window.location.href = "/api/auth/authorize/";
  }
}

export function AppSWRConfig({
  children,
  ...config
}: PropsWithChildren<SWRConfiguration>) {
  return (
    <SWRConfig value={{ fetcher, onError, ...config }}>{children}</SWRConfig>
  );
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <div className={fonts}>
      <AppSWRConfig>
        <I18n>
          <Component {...pageProps} />
        </I18n>
      </AppSWRConfig>
    </div>
  );
}

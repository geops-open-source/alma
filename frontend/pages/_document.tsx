import { Head, Html, Main, NextScript } from "next/document";

import { defaultLanguage } from "@/lib/i18n";

export default function Document() {
  return (
    <Html lang={defaultLanguage}>
      <Head>
        <link
          href="/apple-touch-icon.png"
          rel="apple-touch-icon"
          sizes="180x180"
        />
        <link
          href="/favicon-32x32.png"
          rel="icon"
          sizes="32x32"
          type="image/png"
        />
        <link
          href="/favicon-16x16.png"
          rel="icon"
          sizes="16x16"
          type="image/png"
        />
        <link href="/site.webmanifest" rel="manifest" />
        <link color="#5bbad5" href="/safari-pinned-tab.svg" rel="mask-icon" />
        <meta content="#344054" name="msapplication-TileColor" />
        <meta content="#344054" name="theme-color" />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}

// This file configures the initialization of Sentry on the client.
// The config you add here will be used whenever a users loads a page in their browser.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

import metadata from "./package.json" with { type: "json" };

// Helper to fetch environment from /alma_customer.txt
async function getSentryEnvironment(): Promise<string | undefined> {
  try {
    const res = await fetch("/alma_customer.txt");
    const contentType = res.headers.get("content-type");
    if (!res.ok || !contentType?.includes("text/plain")) {
      return "production";
    }
    const env = await res.text();
    return env.trim();
  } catch {
    return "production";
  }
}

async function initSentry() {
  if (process.env.NODE_ENV === "production") {
    Sentry.init({
      debug: false,
      dsn: "https://1b726eada8ef188c757b326bfe327c32@sentry.geops.de/47",
      environment: await getSentryEnvironment(),
      ignoreErrors: ["cancelRouteChange"],
      release: process.env.NEXT_PUBLIC_VERSION ?? metadata.version,
    });
  }
}

void initSentry();

export const onRouterTransitionStart =
  process.env.NODE_ENV === "production"
    ? Sentry.captureRouterTransitionStart
    : undefined;

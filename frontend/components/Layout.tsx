import {
  Combobox,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from "@headlessui/react";
import { gql } from "graphql-request";
import debounce from "lodash/debounce";
import Head from "next/head";
import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useMemo, useRef, useState } from "react";
import useSWR from "swr";

import Button from "@/components/Button";
import Dialog from "@/components/Dialog";
import InfoCircleIcon from "@/components/icons/InfoCircleIcon";
import SearchIcon from "@/components/icons/SearchIcon";
import Logo from "@/components/Logo";
import { Menu, MenuItem } from "@/components/Menu";
import MissingPermission from "@/components/MissingPermission";
import StableWidthText from "@/components/StableWidthText";
import VflHistory from "@/components/VflHistory";
import VflzItem from "@/components/VflzItem";
import VflzList from "@/components/VflzList";
import fonts from "@/lib/fonts";
import { SearchExportStatus } from "@/lib/graphql";
import { useI18n } from "@/lib/i18n";
import useCurrentUser from "@/lib/useCurrentUser";
import useSetting from "@/lib/useSetting";
import metadata from "@/package.json";

import MissingData from "./MissingData";

import type { ChangeEvent, PropsWithChildren } from "react";

import type { QuickSearchQuery, SearchExportsQuery } from "@/lib/graphql";

const version = process.env.NEXT_PUBLIC_VERSION ?? metadata.version;

function TopNavItem({
  active,
  children,
  path,
}: PropsWithChildren<{ active?: boolean; path: string }>) {
  const router = useRouter();
  return (
    <li>
      <Link
        className={`${(active ?? router.pathname === path) ? "border-b-gray-7 font-bold" : "border-b-white font-medium"} text-gray-7 hover:border-b-gray-7 block border-b-2 py-2 text-base`}
        href={path}
      >
        {children}
      </Link>
    </li>
  );
}

const queryQuickSearch = gql`
  query quickSearch($query: String!, $lang: Language!) {
    search(query: $query, lang: $lang, perPage: 10) {
      directMatch
      graph {
        results {
          ...VflzItem
        }
      }
    }
  }
  ${VflzItem.fragment}
`;

function QuickSearch() {
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const { activeLocale, t } = useI18n();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const handleInputChange = useMemo(() => {
    return debounce((event: ChangeEvent<HTMLInputElement>) => {
      setQuery(event.target.value);
    }, 300);
  }, []);
  const { data, isLoading } = useSWR<QuickSearchQuery>(
    query && [queryQuickSearch, { lang: activeLocale.toUpperCase(), query }],
  );

  useEffect(() => {
    if (data?.search.directMatch) {
      const vflzId = data?.search.graph.results.at(0)?.vflzId;
      void router.push(`/vflz/${vflzId}`);
    }
  }, [data?.search, router]);

  useEffect(() => {
    const closeSearch = () => {
      inputRef.current?.blur();
      setOpen(false);
    };
    router.events.on("routeChangeComplete", closeSearch);
    return () => {
      return router.events.off("routeChangeComplete", closeSearch);
    };
  }, [router]);

  return (
    <Combobox
      immediate
      onChange={(value) => {
        setQuery("");
        if (value === "search") {
          void router.push(`/search?q=${query}`);
        } else if (value) {
          void router.push(`/vflz/${value}`);
        }
      }}
      onClose={() => {
        return setQuery("");
      }}
      value={query}
    >
      <div className="relative">
        <SearchIcon className="text-gray-6 absolute top-2.5 left-2.5" />
        <ComboboxInput
          autoComplete="off"
          className="border-gray-5 w-40 rounded-lg border px-3 py-2.5 pl-8 text-xs font-medium shadow-xs transition-[width] focus:outline-hidden data-open:w-64"
          name="quickSearch"
          onBlur={() => {
            setOpen(false);
          }}
          onChange={handleInputChange}
          onFocus={() => {
            setOpen(true);
          }}
          placeholder={t("quickSearch.placeholder")}
          ref={inputRef}
        />
      </div>
      {open && (
        <ComboboxOptions
          anchor={{ gap: 8, offset: 0, to: "bottom end" }}
          className={`${fonts} border-gray-5 z-60 w-64 rounded-xl border bg-white shadow-lg`}
          data-test="Layout-QuickSearch"
          static
        >
          <div className="text-gray-6 my-2 ml-3 text-xs font-semibold uppercase">
            {t(isLoading || data ? "quickSearch.results" : "history")}
          </div>
          {isLoading || data ? (
            <>
              <ComboboxOption className="mb-2 ml-3" value="search">
                <Link
                  className="text-blue-7 text-sm font-semibold"
                  href={`/search?q=${query}`}
                >
                  {t("quickSearch.openSearch")}
                </Link>
              </ComboboxOption>
              <VflzList
                isCombobox
                items={
                  isLoading || data?.search.directMatch
                    ? undefined
                    : data?.search.graph.results
                }
                noResults={t("quickSearch.noResults")}
              />
            </>
          ) : (
            <VflHistory isCombobox max={10} />
          )}
        </ComboboxOptions>
      )}
    </Combobox>
  );
}

function LayoutContent({
  children,
  container,
}: PropsWithChildren<{ container?: boolean }>) {
  return (
    <main
      className={`border-gray-3 border-t ${container ? "p-4 2xl:container 2xl:mx-auto" : ""}`}
    >
      {children}
    </main>
  );
}

function logout() {
  window.location.href = "/api/auth/logout/";
}

const querySearchExports = gql`
  query searchExports($exportId: ID) {
    searchExports(exportId: $exportId) {
      exportId
      downloadUrl
      format
      startedAt
      status
    }
  }
`;

function hasExportFinished(
  result: SearchExportsQuery | undefined,
  exportId: string | undefined,
): boolean {
  return (
    result?.searchExports.some((item) => {
      if (
        exportId === item.exportId &&
        (item.status === SearchExportStatus.Success ||
          item.status === SearchExportStatus.Error)
      ) {
        localStorage.removeItem("alma-export-id");
        return true;
      }
      return false;
    }) ?? false
  );
}

/**
 * Dialog to show download link for search export.
 * Implemented as a global component with localStorage and BroadcastChannel listener
 * to support long running exports while the user navigates the app.
 */
function SearchExportDialog() {
  const { t } = useI18n();
  const [isOpen, setIsOpen] = useState(false);
  const [exportId, setExportId] = useState<string | undefined>(() => {
    if (typeof window === "undefined") {
      return undefined;
    }
    return localStorage.getItem("alma-export-id") ?? undefined;
  });
  const [pollExportInterval] = useSetting("frontend.pollExportInterval", 1000);

  const { data } = useSWR<SearchExportsQuery>(
    exportId ? [querySearchExports, { exportId }] : null,
    {
      refreshInterval: (result) => {
        if (hasExportFinished(result, exportId)) {
          setIsOpen(true);
          return 0;
        }
        return pollExportInterval;
      },
    },
  );

  useEffect(() => {
    const bc = new BroadcastChannel("SearchExport");
    bc.onmessage = (
      e: MessageEvent<{ exportId?: string; type?: SearchExportStatus }>,
    ) => {
      if (e.data.exportId && e.data.type === SearchExportStatus.Started) {
        localStorage.setItem("alma-export-id", e.data.exportId);
        setExportId(e.data.exportId);
      } else if (e.data.type === SearchExportStatus.Error) {
        setIsOpen(true);
      }
    };
    return () => {
      bc.close();
    };
  }, []);

  const currentExport = data?.searchExports.find((item) => {
    return item.exportId === exportId;
  });

  return (
    <Dialog
      closeOnClickOutside={false}
      isOpen={isOpen && currentExport !== undefined}
      onClose={(value) => {
        if (value === false) {
          setExportId(undefined);
          setIsOpen(false);
        }
      }}
      title={t("SearchExportDialog.title")}
    >
      {currentExport?.status === SearchExportStatus.Success ? (
        <>
          <p className="text-sm">
            {t(`SearchExportDialog.${currentExport.format}`, {
              startedAt: new Date(currentExport.startedAt).toLocaleTimeString(
                "de",
                { hour: "2-digit", minute: "2-digit" },
              ),
            })}
          </p>
          <div className="mt-4 flex justify-end space-x-2">
            <Button
              onClick={() => {
                window.open(currentExport.downloadUrl ?? "", "_blank");
                setExportId(undefined);
                setIsOpen(false);
              }}
            >
              {t("SearchExportDialog.download")}
            </Button>
          </div>
        </>
      ) : null}
      {currentExport?.status === SearchExportStatus.Error ? (
        <p className="text-red-7 text-sm">{t("SearchExportDialog.ERROR")}</p>
      ) : null}
    </Dialog>
  );
}

const versionFetcher = (url: string) => {
  return window.location.hostname === "localhost"
    ? "" // do not run version check on localhost
    : fetch(url, { cache: "no-store" }).then((response) => {
        return response.ok ? response.text() : "";
      });
};

function VersionUpdateBanner() {
  const { t } = useI18n();
  const { data } = useSWR<string>("/version.txt", versionFetcher, {
    refreshInterval: 20000, // refresh every 20 seconds
  });

  if (!data || data === process.env.NEXT_PUBLIC_VERSION) {
    return null;
  }

  return (
    <div className="bg-gray-4 sticky top-0 z-60">
      <div className="flex justify-between space-x-8 p-4 2xl:container 2xl:mx-auto">
        <div className="text-gray-8 flex items-center space-x-4">
          <InfoCircleIcon />
          <span>{t("Layout.versionUpdateMessage")}</span>
        </div>
        <Button
          onClick={() => {
            return window.location.reload();
          }}
        >
          {t("Layout.versionUpdateButton")}
        </Button>
      </div>
    </div>
  );
}

export default function Layout({
  children,
  container,
  error,
  isLoading = false,
  title,
}: PropsWithChildren<{
  container?: boolean;
  error?: unknown;
  isLoading?: boolean;
  title: string;
}>) {
  const { locale, t } = useI18n();
  const router = useRouter();
  const currentUser = useCurrentUser();
  const logoSetting = useSetting("ui.logo", "/customer-logo.svg");
  const [showTestBadge] = useSetting("ui.showTestBadge", false);
  return (
    <>
      <Head>
        <title>
          {currentUser.permissions.canViewVfl ? `${title} - alma` : "alma"}
        </title>
      </Head>
      <SearchExportDialog />
      <VersionUpdateBanner />
      <div className="peer sticky top-0 z-40 -mb-16 h-16" />
      <header className="group sticky -top-20 z-50 bg-white transition-[top] peer-hover:top-0 hover:top-0 has-[button[data-active]]:top-0 has-[input:focus]:top-0">
        {showTestBadge ? (
          <div className="bg-red-6/80 absolute top-3 -left-6 -rotate-45 px-8 text-sm leading-6 font-bold text-white">
            Test
          </div>
        ) : null}
        <div className="flex justify-between p-4 2xl:container 2xl:mx-auto">
          <nav className="flex items-center space-x-8">
            <div className="flex flex-col items-end">
              <Logo className="-mt-0.5 -mb-1" />
              <div
                className="text-gray-6 w-20 truncate text-right text-xs leading-3"
                title={t("version", { version })}
              >
                {t("version", { version })}
              </div>
            </div>
            <ul className="flex space-x-6">
              {currentUser.permissions.canViewVfl ? (
                <>
                  <TopNavItem path="/">
                    <StableWidthText value={t("dashboard.title")} />
                  </TopNavItem>
                  <TopNavItem
                    active={router.pathname.startsWith("/vflz")}
                    path={
                      localStorage.getItem("last-search-mode") === "advanced"
                        ? "/search/advanced"
                        : "/search"
                    }
                  >
                    <StableWidthText value={t("search.title")} />
                  </TopNavItem>
                  <TopNavItem path="/pools">
                    <StableWidthText value={t("pools.title")} />
                  </TopNavItem>
                </>
              ) : null}
              {currentUser.permissions.canViewProcess ? (
                <TopNavItem path="/workflow">
                  <StableWidthText value={t("workflow.title")} />
                </TopNavItem>
              ) : null}
            </ul>
          </nav>
          <div className="flex items-center space-x-4">
            {currentUser.permissions.canViewVfl ? <QuickSearch /> : null}
            <Menu
              data-test="Layout-userMenu"
              title={currentUser.username ?? t("Layout.userMenu")}
            >
              <MenuItem
                onClick={() => {
                  return locale("de");
                }}
              >
                Deutsch
              </MenuItem>
              <MenuItem
                onClick={() => {
                  return locale("fr");
                }}
              >
                Français
              </MenuItem>
              <MenuItem
                onClick={() => {
                  return locale("it");
                }}
              >
                Italiano
              </MenuItem>
              {currentUser.permissions.canViewVfl ? (
                <>
                  <div className="border-gray-4 -mx-1 border-t" />
                  <MenuItem href="/user">{t("user.settings")}</MenuItem>
                </>
              ) : null}
              {currentUser.permissions.canEditUser ? (
                <MenuItem href="/admin/users">{t("admin.title")}</MenuItem>
              ) : null}
              <div className="border-gray-4 -mx-1 border-t" />
              <MenuItem onClick={logout}>{t("Layout.logout")}</MenuItem>
            </Menu>
            {logoSetting.at(2) ? null : (
              <img
                alt=""
                className="max-h-11 max-w-56 pl-4"
                src={logoSetting.at(0) as string}
              />
            )}
          </div>
        </div>
      </header>
      {currentUser.permissions.canViewVfl && !error && !isLoading && (
        <LayoutContent container={container}>{children}</LayoutContent>
      )}
      {!currentUser.permissions.canViewVfl && <MissingPermission />}
      {!!error && !isLoading && <MissingData />}
    </>
  );
}

Layout.NavList = function NavList({ children }: PropsWithChildren) {
  return (
    <ul className="border-gray-4 bg-gray-2 flex grow space-x-1 rounded-lg border p-1">
      {children}
    </ul>
  );
};

Layout.NavItem = function NavItem({
  children,
  href,
  pathname,
}: PropsWithChildren<{ href: string; pathname?: string }>) {
  const router = useRouter();
  return (
    <li>
      <Link
        className={`${router.pathname === (pathname ?? href) ? "text-gray-8 bg-white font-bold shadow-xs" : "font-medium"} text-gray-6 hover:text-gray-8 block rounded-md px-3 py-2 text-sm hover:bg-white hover:shadow-xs`}
        href={href}
      >
        {children}
      </Link>
    </li>
  );
};

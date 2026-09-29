export interface GetVflzUrlOptions {
  doNotAppendHash?: boolean;
  doNotAppendSearch?: boolean;
}

export default function getVflzUrl(
  vflzId: string,
  options: GetVflzUrlOptions = {
    doNotAppendHash: false,
    doNotAppendSearch: false,
  },
) {
  const pathname = window.location.pathname.startsWith("/vflz/")
    ? window.location.pathname.replace(/\/vflz\/[^/]+/, `/vflz/${vflzId}`)
    : `/vflz/${vflzId}`;
  return (
    pathname +
    (options.doNotAppendHash ? "" : window.location.hash) +
    (options.doNotAppendSearch ? "" : window.location.search)
  );
}

#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$SCRIPT_DIR/reports"
chmod 777 "$SCRIPT_DIR/reports"

ZAP_TARGET="${ZAP_TARGET:-https://test.alma-os.ch}"
ZAP_USERNAME="${ZAP_USERNAME:-test@alma-os.ch}"
ZAP_PASSWORD="${ZAP_PASSWORD:-demo2024}"
ZAP_USERNAME_REGULAR="${ZAP_USERNAME_REGULAR:-test-view_process@alma-os.ch}"
ZAP_PASSWORD_REGULAR="${ZAP_PASSWORD_REGULAR:-demo2024}"
ZAP_NETWORK="${ZAP_NETWORK:-}"

# Timing defaults (full scan); --quick overrides these
spiderDuration="${spiderDuration:-5}"
ajaxDuration="${ajaxDuration:-3}"
passiveWaitDuration="${passiveWaitDuration:-2}"
ruleDuration="${ruleDuration:-5}"
scanDuration="${scanDuration:-10}"

if [ "${1:-}" = "--quick" ]; then
  spiderDuration=1
  ajaxDuration=1
  passiveWaitDuration=5
  ruleDuration=1
  scanDuration=1
fi

# Fetch the OpenAPI spec if not already present (local script generates it via Python)
if [ ! -f "$SCRIPT_DIR/openapi.json" ]; then
  echo "Fetching OpenAPI spec from ${ZAP_TARGET}/openapi.json ..."
  curl -sf "${ZAP_TARGET}/openapi.json" -o "$SCRIPT_DIR/openapi.json"
fi

# Expand only the timing variables; ZAP_TARGET and credentials are left as-is
# for ZAP's own variable substitution at runtime.
export spiderDuration ajaxDuration passiveWaitDuration ruleDuration scanDuration
envsubst '${spiderDuration} ${ajaxDuration} ${passiveWaitDuration} ${ruleDuration} ${scanDuration}' \
  < "$SCRIPT_DIR/zap-automation.yaml.tmpl" \
  > "$SCRIPT_DIR/zap-automation.yaml"

NETWORK_FLAG=""
if [ -n "$ZAP_NETWORK" ]; then
  NETWORK_FLAG="--network $ZAP_NETWORK"
fi

docker run --rm \
  $NETWORK_FLAG \
  -v "$SCRIPT_DIR:/zap/wrk:rw" \
  -e ZAP_TARGET="${ZAP_TARGET}" \
  -e ZAP_USERNAME="${ZAP_USERNAME}" \
  -e ZAP_PASSWORD="${ZAP_PASSWORD}" \
  -e ZAP_USERNAME_REGULAR="${ZAP_USERNAME_REGULAR}" \
  -e ZAP_PASSWORD_REGULAR="${ZAP_PASSWORD_REGULAR}" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap.sh -cmd -autorun /zap/wrk/zap-automation.yaml

#!/bin/bash
set -euo pipefail

# Convenience wrapper around run-zap.sh for scanning a local docker compose stack.
# Assumes the stack is already running (docker compose up -d).
#
# Override defaults via environment variables:
#   ZAP_TARGET            - default: http://nginx
#   ZAP_NETWORK           - default: derived from COMPOSE_PROJECT_NAME (e.g. alma_backend)
#   COMPOSE_PROJECT_NAME  - default: alma

_SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
_PROJECT="${COMPOSE_PROJECT_NAME:-alma}"
_COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

export ZAP_TARGET="${ZAP_TARGET:-http://nginx}"
export ZAP_NETWORK="${ZAP_NETWORK:-${_PROJECT}_backend}"

# Add the ZAP override only if not already present (e.g. set by the CI job).
if [[ "${_COMPOSE_FILE}" != *"docker-compose.zap-override.yml"* ]]; then
  _COMPOSE_FILE="${_COMPOSE_FILE}:${_SCRIPT_DIR}/../docker-compose.zap-override.yml"
fi

# Bring up the stack with the ZAP override, which ensures nginx waits for
# backend to be healthy before starting (avoids "host not found" on upstream).
COMPOSE_FILE="${_COMPOSE_FILE}" docker compose up -d

# Generate the OpenAPI spec from the running backend so ZAP has it as a file.
docker compose exec backend /app/venv/bin/python -c \
  "from alma.api import app; import json; print(json.dumps(app.openapi()))" \
  > "${_SCRIPT_DIR}/openapi.json"

exec "${_SCRIPT_DIR}/run-zap.sh" "$@"

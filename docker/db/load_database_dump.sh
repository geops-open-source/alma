#!/bin/bash
set -eu -o pipefail

if [[ "$#" != 1 ]]; then
    echo "Usage: $0 <filename>" >&2
    exit 1
fi

exec pg_restore -Fc -1 -d "$DB_URL" "$1"

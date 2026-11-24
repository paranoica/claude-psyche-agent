#!/usr/bin/env bash
# Checks skill/psyche and packs it into dist/psyche.zip for claude.ai. See tools/package.py.
set -euo pipefail
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
exec python3 -m tools.package "$@"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
mkdir -p "${PROJECT_ROOT}/.npm-cache"

NPM_CONFIG_CACHE="${PROJECT_ROOT}/.npm-cache" \
npx -y @modelcontextprotocol/inspector \
python3 "${SCRIPT_DIR}/mcp_server.py"

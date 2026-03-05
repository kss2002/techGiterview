#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "[secret-scan] running repository secret scan..."

# Realistic high-risk token patterns (placeholders should not match these lengths/formats)
PATTERN='(ghp_[A-Za-z0-9]{20,}|sk-lf-[A-Za-z0-9-]{20,}|pk-lf-[A-Za-z0-9-]{20,}|AIza[0-9A-Za-z_-]{30,}|sk-[A-Za-z0-9]{20,})'

MATCHES="$(rg -n --hidden \
  -g '!.git' \
  -g '!node_modules' \
  -g '!dist' \
  -g '!coverage' \
  -g '!tests/**' \
  -g '!test_*.py' \
  -g '!README.md' \
  -g '!src/frontend/src/components/ApiKeySetup.tsx' \
  -e "$PATTERN" . || true)"

if [[ -n "$MATCHES" ]]; then
  echo "[secret-scan] potential secrets detected:"
  echo "$MATCHES"
  exit 1
fi

echo "[secret-scan] passed"

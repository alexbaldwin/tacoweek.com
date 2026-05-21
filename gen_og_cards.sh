#!/usr/bin/env bash
# Render the 1200x630 social-share cards from the templates build.py writes into
# public/_ogcards/, saving PNGs to public/images/og/. Requires agent-browser.
set -euo pipefail
cd "$(dirname "$0")"
OG=_ogcards
OUT=public/images/og
mkdir -p "$OUT"

if ! command -v agent-browser >/dev/null 2>&1; then
  echo "agent-browser not found — skipping OG card render (existing PNGs kept)." >&2
  exit 0
fi

agent-browser set viewport 1200 630 >/dev/null 2>&1
for f in "$OG"/*.html; do
  name="$(basename "$f" .html)"
  agent-browser open "file://$(pwd)/$f" >/dev/null 2>&1
  agent-browser screenshot "$(pwd)/$OUT/$name.png" >/dev/null 2>&1
  echo "  rendered $OUT/$name.png"
done
echo "OG cards rendered."

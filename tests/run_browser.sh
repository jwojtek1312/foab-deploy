#!/usr/bin/env bash
# Serve the repo and run a browser test page in headless Chromium.
# Usage: tests/run_browser.sh tests/js.test.html
# The page must write "PASS ..." / "FAIL: ..." lines into <pre id="result">.
set -euo pipefail

page="${1:?usage: tests/run_browser.sh <page>}"
root="$(cd "$(dirname "$0")/.." && pwd)"
port="${PORT:-8765}"
chrome="${CHROME:-$(command -v chromium || command -v chromium-browser || command -v google-chrome)}"

python3 -m http.server "$port" --bind 127.0.0.1 --directory "$root" >/dev/null 2>&1 &
server=$!
trap 'kill "$server" 2>/dev/null || true' EXIT

for _ in $(seq 50); do
  curl -s -o /dev/null "http://127.0.0.1:$port/" && break
  sleep 0.1
done

dom="$("$chrome" --headless=new --disable-gpu --no-first-run --no-default-browser-check \
  --virtual-time-budget=10000 --dump-dom "http://127.0.0.1:$port/$page" 2>/dev/null)"

result="$(printf '%s' "$dom" | python3 -c '
import sys, re, html
m = re.search(r"<pre id=\"result\"[^>]*>(.*?)</pre>", sys.stdin.read(), re.S)
print(html.unescape(m.group(1)).strip() if m else "FAIL: no #result element found")
')"

echo "$result"
if grep -q "FAIL" <<<"$result" || ! grep -q "PASS" <<<"$result"; then
  exit 1
fi

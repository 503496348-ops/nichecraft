#!/usr/bin/env bash
# Preflight check for the nichecraft skill.
# Verifies the tools needed to render an SVG and write it into Feishu as an editable whiteboard.
set -eu
ok=1
echo "▶ Checking prerequisites for nichecraft…"
echo

# Node ≥ 20
if command -v node >/dev/null 2>&1; then
  echo "  ✓ Node $(node -v)"
else
  echo "  ✗ Node.js not found — install Node ≥ 20  (https://nodejs.org)"
  ok=0
fi

# lark-cli  (npm: @larksuite/cli)  — auth + writing to Feishu
if command -v lark-cli >/dev/null 2>&1; then
  echo "  ✓ lark-cli ($(lark-cli --version 2>/dev/null | head -1))"
  if lark-cli auth status >/dev/null 2>&1; then
    echo "    auth: ok"
  else
    echo "    auth: not logged in  (run: lark-cli auth login)"
  fi
else
  echo "  ✗ lark-cli not found — install: npm i -g @larksuite/cli"
  ok=0
fi

echo
if [ "$ok" -eq 0 ]; then
  echo "✗ Some prerequisites missing."
  exit 1
else
  echo "✓ All prerequisites met."
fi

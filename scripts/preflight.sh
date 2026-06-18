     1|#!/usr/bin/env bash
     2|# Preflight check for the nichecraft skill.
     3|# Verifies the tools needed to render an SVG and write it into Feishu as an editable whiteboard.
     4|set -eu
     5|ok=1
     6|echo "▶ Checking prerequisites for nichecraft…"
     7|echo
     8|
     9|# Node ≥ 20
    10|if command -v node >/dev/null 2>&1; then
    11|  echo "  ✓ Node $(node -v)"
    12|else
    13|  echo "  ✗ Node.js not found — install Node ≥ 20  (https://nodejs.org)"
    14|  ok=0
    15|fi
    16|
    17|# lark-cli  (npm: @larksuite/cli)  — auth + writing to Feishu
    18|if command -v lark-cli >/dev/null 2>&1; then
    19|  echo "  ✓ lark-cli ($(lark-cli --version 2>/dev/null | head -1))"
    20|  if lark-cli auth status >/dev/null 2>&1; then
    21|    echo "  ✓ lark-cli appears authenticated"
    22|  else
    23|    echo "  ! lark-cli may not be authenticated. Run:"
    24|    echo "        lark-cli config init     # first-time setup, scan the QR"
    25|    echo "        lark-cli auth login      # authorize your Feishu/Lark account"
    26|  fi
    27|else
    28|  echo "  ✗ lark-cli not found. Install and authenticate:"
    29|  echo "        npm install -g @larksuite/cli"
    30|  echo "        lark-cli config init     # scan the QR"
    31|  echo "        lark-cli auth login"
    32|  ok=0
    33|fi
    34|
    35|# whiteboard-cli  (run via npx, auto-downloads)
    36|if npx -y @larksuite/whiteboard-cli@^0.2.11 -v >/dev/null 2>&1; then
    37|  echo "  ✓ @larksuite/whiteboard-cli reachable via npx"
    38|else
    39|  echo "  ! could not reach @larksuite/whiteboard-cli via npx (needs network on first run)"
    40|fi
    41|
    42|echo
    43|if [ "$ok" = 1 ]; then
    44|  echo "✅ Ready. You also need a Feishu/Lark account — boards are written to your own tenant."
    45|else
    46|  echo "❌ Missing prerequisites above. Install them, then re-run this check."
    47|  exit 1
    48|fi
    49|
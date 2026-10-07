#!/usr/bin/env bash
# Usage: bash qa/lighthouse.sh https://<our-deployment>
set -euo pipefail
OURS="$1"
CHROME_PATH="$(py -3.11 -c 'from playwright.sync_api import sync_playwright as s; p=s().start(); print(p.chromium.executable_path); p.stop()')"
export CHROME_PATH
mkdir -p qa/out
for path in customer-service/blog locations contact; do
  name="${path##*/}"
  for side in ours live; do
    base="$OURS"; [ "$side" = live ] && base="https://www.insureonthespot.com"
    npx --yes lighthouse "$base/$path/" --quiet --form-factor=mobile \
      --only-categories=performance,accessibility,best-practices \
      --chrome-flags="--headless=new" --output=json --output-path="qa/out/lh-$side-$name.json" || true
  done
done
py -3.11 - <<'EOF'
import json, glob
rows = []
for f in sorted(glob.glob("qa/out/lh-*.json")):
    d = json.load(open(f, encoding="utf-8"))
    c = d["categories"]
    rows.append(f"| {f.replace(chr(92), '/').split('lh-')[1][:-5]} | {round(c['performance']['score']*100)} | {round(c['accessibility']['score']*100)} | {round(c['best-practices']['score']*100)} | {d['audits']['largest-contentful-paint']['displayValue']} |")
open("qa/out/summary.md", "w", encoding="utf-8").write("| page | perf | a11y | best practices | LCP |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
print(open("qa/out/summary.md", encoding="utf-8").read())
EOF

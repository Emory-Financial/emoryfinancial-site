#!/usr/bin/env bash
# Rebuild the live site into site/ from src/. Run from the repo root.
#   src/original/  the hand-built site pages (edit these to change existing pages)
#   src/content/   one Markdown file per Insights article (add a file to publish)
#   src/covers/    generated cover images (delete one to re-render it)
#   site/          generated output that Netlify serves -- never edit by hand
set -euo pipefail
cd "$(dirname "$0")"
python3 src/build.py src/original src/content site --manifest-only
if [ ! -d src/tools/node_modules/@fontsource ]; then (cd src/tools && npm install --silent); fi
NODE_PATH="$(npm root -g)" node src/tools/covers.js src/covers-manifest.json src/covers
python3 src/build.py src/original src/content site
sed 's/^  publish = "\."/  publish = "site"/' site/netlify.toml > netlify.toml
rm site/netlify.toml
grep -q 'publish = "site"' netlify.toml
cat site/version.txt

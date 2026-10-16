#!/usr/bin/env bash
# Rebuild the live site into site/ from src/. Run from the repo root.
#   src/original/  the hand-built site pages (edit these to change existing pages)
#   src/content/   one Markdown file per Insights article (add a file to publish)
#   site/          generated output that Netlify serves -- never edit by hand
set -euo pipefail
cd "$(dirname "$0")"
python3 src/build.py src/original src/content site
sed 's/^  publish = "\."/  publish = "site"/' site/netlify.toml > netlify.toml
rm site/netlify.toml
grep -q 'publish = "site"' netlify.toml
cat site/version.txt

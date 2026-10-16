# emoryfinancial.com

Static site for Emory Financial, deployed by Netlify from this repository.

- `site/` is what Netlify publishes. It is generated; do not edit it by hand.
- `src/original/` holds the hand-built pages. Edit these to change existing pages.
- `src/content/` holds one Markdown file per Insights article.
- `publish.sh` rebuilds `site/` (and `netlify.toml`) from `src/`.

## Publishing a new Insights article

1. Add `src/content/<url-slug>.md` with the same front matter as the existing articles
   (`title`, `seo_title`, `description`, `card`, `topic`, `published`, `order`).
2. Run `./publish.sh` (needs Python 3 with the `markdown` package).
3. Commit and push to `main`. Netlify deploys automatically; check `/version.txt`.

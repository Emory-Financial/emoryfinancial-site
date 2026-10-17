# Emory Financial website

Static site for Derek Shao's mortgage brokerage. Netlify deploys every push to `main`
(publish directory `site/`). Confirm each deploy at https://emoryfinancial.com/version.txt.

## How the site is built
- Never edit `site/` directly. Change `src/` and run `./publish.sh`, then commit `src/`, `site/` and `netlify.toml` together.
- `src/original/` is the hand-built site. `src/content/*.md` is one file per Insights article.
- `publish.sh` renders a cover image for any article without one (`src/covers/<slug>.jpg`; delete a cover to re-render
  it after a title change), then rebuilds listing pages (12 per page), topic pages, search index, sitemap, feed and llms.txt.

## Publishing rules (non-negotiable)
- Only publish an article after Derek has approved it, in writing or in the review doc. Drafts never go in this
  public repository; they live in the review doc and the Claude project until approved.
- Facts must come from pages actually opened, preferably primary sources (Fannie Mae/Freddie Mac guides, HUD, IRS,
  California BOE/HCD/DFPI, Federal Reserve, FHFA). Every article ends with "## Sources".
- No rate quotes, APRs or payment examples that would read as an offer of credit (Regulation Z trigger terms).
  National averages must be labeled as such with source and date; hypothetical examples must say so.
- Never include client names, loan data, or anything from the borrower spreadsheet.
- Consultations are always 30 minutes ("Thirty minutes, no credit pull, no obligation"). Never write 15 minutes.
- Be timely: time-sensitive figures (rates, limits, results) carry an "as of" date and source and are re-checked on
  publish day. Elections and ballot measures are covered neutrally (what it does for owners/buyers/renters, both sides,
  official sources); never recommend a vote or endorse a candidate.

## Article format (src/content/<url-slug>.md)
Front matter: `title`, `seo_title` (<60 chars), `description` (<155 chars), `card` (one-line teaser for cards),
`topic` (one of: Buying & remodeling, Home equity, Family & estate, Self-employed & trades, Jobs & income, Planning),
`published` (YYYY-MM-DD, the day it goes live), `order` (tie-break for same-day posts).

Body, in Derek's first-person voice (warm, plain English, California-specific):
1. `**The short answer:**` paragraph (2–4 sentences; this is what AI search quotes)
2. Question-style `##` headings
3. At least one visual: a fenced ```chart block (types: bars, ranges, matrix, steps; see src/charts.py). Use only
   numbers stated and sourced in the article.
4. `## Derek's take` (one paragraph, ends with a low-pressure invitation to call)
5. `## FAQ` with 3–5 `**Question?** Answer` paragraphs (becomes FAQPage schema)
6. Optional italic disclaimer line, then `## Sources` as a bulleted list of links

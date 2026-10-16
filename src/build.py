#!/usr/bin/env python3
"""Build the Emory Financial site update.

Usage: build.py <original_site_dir> <content_dir> <output_dir>

Copies the original site to output_dir, then adds:
  - /insights index + one page per Markdown article in content_dir
  - "Insights" link in every page's nav and footer
  - a "Latest from Insights" block on the homepage
  - sitemap.xml, robots.txt, llms.txt, insights/feed.xml, netlify.toml redirects
  - a small CSS block for article pages
"""
import datetime as dt
import html
import json
import re
import shutil
import sys
from pathlib import Path

import markdown

SITE = "https://emoryfinancial.com"
BUILD_ID = dt.datetime.now().strftime("%m%d-%H%M")
TODAY = dt.date.today().isoformat()

src_dir, content_dir, out_dir = map(Path, sys.argv[1:4])
here = Path(__file__).resolve().parent

# ---------------------------------------------------------------- copy site
if out_dir.exists():
    shutil.rmtree(out_dir)
shutil.copytree(src_dir, out_dir)

# ---------------------------------------------------------------- articles
def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
    meta["slug"] = path.stem
    meta["body_md"] = m.group(2)
    meta["order"] = int(meta.get("order", 99))
    return meta

articles = sorted((parse(p) for p in content_dir.glob("*.md")),
                  key=lambda a: (a["published"], -a["order"]), reverse=True)
# Newest first; same-day ties keep the editorial order (1 first).
articles.sort(key=lambda a: (a["published"], -a["order"]), reverse=True)


def render_body(a):
    body = markdown.markdown(a["body_md"], extensions=["tables", "sane_lists"])
    # Short answer -> highlighted answer box (the paragraph AI tools quote).
    body = re.sub(r"<p><strong>The short answer:</strong>(.*?)</p>",
                  r'<div class="callout answer"><p><strong>The short answer:</strong>\1</p></div>',
                  body, count=1, flags=re.S)
    # FAQ: bold-question paragraphs -> h3 + p, collected for FAQPage schema.
    faqs = []
    def faq_section(m):
        inner = m.group(2)
        def qa(mm):
            q, ans = mm.group(1).strip(), mm.group(2).strip()
            faqs.append((html.unescape(re.sub("<[^>]+>", "", q)),
                         html.unescape(re.sub("<[^>]+>", "", ans))))
            return f'<h3>{q}</h3>\n<p>{ans}</p>'
        inner = re.sub(r"<p><strong>(.+?\?)</strong>\s*(.*?)</p>", qa, inner, flags=re.S)
        return m.group(1) + inner
    body = re.sub(r'(<h2>FAQ</h2>)(.*?)(?=<h2>|$)', faq_section, body, count=1, flags=re.S)
    body = body.replace("<h2>FAQ</h2>", '<h2 id="faq">Frequently asked questions</h2>')
    # Checklists.
    body = re.sub(r"<ul>\s*<li>\[ \]", '<ul class="checklist">\n<li>[ ]', body)
    body = body.replace("<li>[ ] ", "<li>")
    # Sources list styling; external links open in a new tab.
    body = re.sub(r"(<h2>Sources</h2>\s*)<ul>", r'\1<ul class="sources">', body)
    body = re.sub(r'<a href="(https?://(?!emoryfinancial\.com)[^"]+)">',
                  r'<a href="\1" target="_blank" rel="noopener">', body)
    # Tables scroll sideways on phones instead of breaking the layout.
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    # "Derek's take" gets a quiet card treatment.
    body = re.sub(r"<h2>Derek's take</h2>\s*<p>(.*?)</p>",
                  r'<div class="callout take"><p class="eyebrow">Derek\'s take</p><p>\1</p></div>',
                  body, count=1, flags=re.S)
    words = len(re.sub("<[^>]+>", " ", body).split())
    return body, faqs, max(1, round(words / 220))


def nice_date(iso):
    d = dt.date.fromisoformat(iso)
    return d.strftime("%B %-d, %Y")


# ---------------------------------------------------------------- page chrome
ref = (src_dir / "areas" / "arcadia.html").read_text(encoding="utf-8")
chrome_top = ref[ref.index('<a class="skip-link"'):ref.index("</header>") + len("</header>")]
chrome_bottom = ref[ref.index('<footer class="site-footer">'):ref.index("</footer>") + len("</footer>")]
head_common = ref[ref.index('<link rel="icon"'):ref.index('<link rel="stylesheet"') + len('<link rel="stylesheet" href="/assets/css/style.v2.css">')]

CALC_LI = re.compile(r'(<li><a href="(?:https://emoryfinancial\.com)?/calculators"[^>]*>Calculators</a></li>)')


def add_insights_links(page_html, current=False):
    cur = ' aria-current="page"' if current else ""
    if 'href="/insights"' in page_html:
        return page_html
    return CALC_LI.sub(lambda m: m.group(1) + f'\n        <li><a href="/insights"{cur}>Insights</a></li>', page_html)


chrome_top_insights = add_insights_links(chrome_top, current=True)
chrome_bottom_insights = add_insights_links(chrome_bottom)

CTA = """  <section class="section-tight section-ink">
    <div class="wrap center">
      <p class="eyebrow">Next step</p>
      <h2>Start with a conversation.</h2>
      <p class="lede mt-3">Fifteen minutes, no credit pull, no obligation. Tell me what you're weighing and I'll tell you honestly what the numbers say.</p>
      <div class="btn-row mt-5" style="justify-content:center">
        <a class="btn btn-accent btn-lg" data-book target="_blank" rel="noopener" href="https://calendar.app.google/wgMMsLqjjajM1JGF9">Book a consultation</a>
        <a class="btn btn-ghost btn-lg" href="tel:+13108695678">Call 310-869-5678</a>
      </div>
    </div>
  </section>"""

NEWSLETTER = """  <section class="section">
    <div class="wrap">
      <div class="newsletter">
        <div class="split" style="align-items:center">
          <div>
            <p class="eyebrow" style="color:#EFD9AF">The Rate Note</p>
            <h2>Get these articles once a month.</h2>
            <p class="mt-3">One email a month from Derek: the new Insights articles, where California rates actually are, and anything that changed in lending. No spam, unsubscribe in one click.</p>
          </div>
          <div>
            <form action="/thanks/" class="newsletter-form" method="POST" name="newsletter" data-netlify="true" netlify-honeypot="company-website">
              <input type="hidden" name="form-name" value="newsletter">
              <p class="honeypot" aria-hidden="true"><label>Don't fill this out: <input name="company-website" tabindex="-1" autocomplete="off"></label></p>
              <label class="visually-hidden" for="nl-name-{key}">First name</label>
              <input type="text" id="nl-name-{key}" name="first-name" placeholder="First name" autocomplete="given-name">
              <label class="visually-hidden" for="nl-email-{key}">Email address</label>
              <input type="email" id="nl-email-{key}" name="email" placeholder="you@email.com" required autocomplete="email">
              <button class="btn btn-accent" type="submit">Subscribe</button>
            </form>
            <p class="newsletter-fine">By subscribing you agree to receive email from Emory Financial. We never sell your information. See our <a href="/privacy" style="color:#fff">Privacy Policy</a>.</p>
          </div>
        </div>
      </div>
    </div>
  </section>"""

DISCLAIMER = ("This article is general education, not a commitment to lend, an offer of credit, "
              "or tax, legal or investment advice. All loans are subject to credit approval, income and "
              "asset verification, and property appraisal. Programs, rates, terms and limits change "
              "without notice; figures are current as of the publish date. Derek Shao, NMLS #242117, "
              "CA DRE #01358261. Financial Dynamics, Inc. DBA Emory Financial, Company NMLS #393986. "
              "Equal Housing Opportunity.")


def jsonld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, indent=2, ensure_ascii=False) + "\n</script>"


def page(title, description, canonical, og_type, ld_blocks, main, extra_head=""):
    e = html.escape
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="build" content="{BUILD_ID}">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="Emory Financial">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="{SITE}/assets/img/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="Emory Financial Insights" href="{SITE}/insights/feed.xml">
{extra_head}{head_common}
{chr(10).join(jsonld(b) for b in ld_blocks)}
</head>
<body>
{chrome_top_insights}

<main id="main">
{main}
</main>

{chrome_bottom_insights}

<script src="/assets/js/site.v2.js" defer></script>
</body>
</html>
"""


def card(a, heading="h2"):
    return f"""        <a class="card card-link article-card" href="/insights/{a['slug']}">
          <span class="card-tag">{html.escape(a['topic'])}</span>
          <{heading}>{html.escape(a['title'])}</{heading}>
          <p>{html.escape(a['card'])}</p>
          <span class="card-more">Read the article &rarr;</span>
        </a>"""


AUTHOR_BOX = """      <aside class="author-box" aria-label="About the author">
        <img src="/assets/img/derek-shao.jpg" alt="Derek Shao" width="88" height="88" loading="lazy">
        <div>
          <p class="author-name"><a href="/team/derek-shao">Derek Shao</a></p>
          <p class="author-role">Founder &amp; Broker of Record, Emory Financial &middot; NMLS 242117 &middot; DRE 01358261</p>
          <p>Derek has been a licensed California mortgage broker for 20 years and has placed 1,233 home loans across 192 California cities since 2011. He shops the wholesale market across many lenders and answers his own phone.</p>
        </div>
      </aside>"""

org_ref = {"@id": f"{SITE}/#organization"}
author = {"@type": "Person", "@id": f"{SITE}/team/derek-shao#person", "name": "Derek Shao",
          "url": f"{SITE}/team/derek-shao", "jobTitle": "Founder & Broker of Record",
          "identifier": "NMLS 242117 | CA DRE 01358261",
          "image": f"{SITE}/assets/img/derek-shao.jpg", "worksFor": org_ref,
          "sameAs": ["https://www.tiktok.com/@emory.financial"]}

ins_dir = out_dir / "insights"
ins_dir.mkdir(exist_ok=True)

for a in articles:
    body, faqs, minutes = render_body(a)
    a["faqs"] = faqs
    url = f"{SITE}/insights/{a['slug']}"
    a["url"] = url
    others = [o for o in articles if o is not a][:3]
    ld = [
        {"@context": "https://schema.org", "@type": "BlogPosting", "headline": a["title"],
         "description": a["description"], "url": url, "mainEntityOfPage": url,
         "datePublished": a["published"], "dateModified": a.get("updated", a["published"]),
         "author": author, "publisher": org_ref, "image": f"{SITE}/assets/img/og-image.png",
         "inLanguage": "en-US", "articleSection": a["topic"],
         "isPartOf": {"@type": "Blog", "@id": f"{SITE}/insights#blog", "name": "Emory Financial Insights"}},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Insights", "item": f"{SITE}/insights"},
            {"@type": "ListItem", "position": 3, "name": a["title"]}]},
    ]
    if faqs:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}}
            for q, ans in faqs]})
    main = f"""
  <section class="page-head article-head">
    <div class="wrap">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="/insights">Insights</a> <span aria-hidden="true">/</span> {html.escape(a['topic'])}</nav>
      <h1>{html.escape(a['title'])}</h1>
      <p class="byline">By <a href="/team/derek-shao">Derek Shao</a>, NMLS 242117 &middot; <time datetime="{a['published']}">{nice_date(a['published'])}</time> &middot; {minutes} min read</p>
    </div>
  </section>

  <section class="section article-section">
    <article class="wrap-narrow prose article-body">
{body}
      <p class="article-disclaimer">{DISCLAIMER}</p>
{AUTHOR_BOX}
    </article>
  </section>

  <section class="section section-sand">
    <div class="wrap">
      <div class="mb-5">
        <p class="eyebrow">Keep reading</p>
        <h2>More from Insights</h2>
      </div>
      <div class="grid grid-3">
{chr(10).join(card(o, 'h3') for o in others)}
      </div>
      <div class="btn-row mt-5"><a class="btn btn-ghost" href="/insights">All articles</a></div>
    </div>
  </section>

{CTA}
"""
    extra = (f'<meta property="article:published_time" content="{a["published"]}">\n'
             f'<meta property="article:author" content="Derek Shao">\n')
    (ins_dir / f"{a['slug']}.html").write_text(
        page(f"{a['seo_title']} | Emory Financial", a["description"], url, "article", ld, main, extra),
        encoding="utf-8")

# ---------------------------------------------------------------- insights index
idx_desc = ("Plain-English articles from California mortgage broker Derek Shao on homeownership, "
            "home equity, family property and the economy, and what each means for your mortgage.")
idx_ld = [
    {"@context": "https://schema.org", "@type": "Blog", "@id": f"{SITE}/insights#blog",
     "name": "Emory Financial Insights", "url": f"{SITE}/insights", "description": idx_desc,
     "publisher": org_ref, "author": author, "inLanguage": "en-US",
     "blogPost": [{"@type": "BlogPosting", "headline": a["title"], "url": a["url"],
                   "datePublished": a["published"]} for a in articles]},
    {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
        {"@type": "ListItem", "position": 2, "name": "Insights"}]},
]
idx_main = f"""
  <section class="page-head">
    <div class="wrap">
      <p class="eyebrow">Insights</p>
      <h1>Mortgages, money and the California home, in plain English</h1>
      <p>What the economy, the tax rules and your family's plans actually mean for your mortgage. Written by Derek Shao after 20 years and 1,233 California home loans.</p>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="grid grid-3">
{chr(10).join(card(a) for a in articles)}
      </div>
    </div>
  </section>

{NEWSLETTER.replace('{key}', 'insights')}

{CTA}
"""
(ins_dir / "index.html").write_text(
    page("Insights: Mortgage & Homeownership Articles | Emory Financial", idx_desc,
         f"{SITE}/insights", "website", idx_ld, idx_main), encoding="utf-8")

# ---------------------------------------------------------------- RSS feed
def rfc822(iso):
    d = dt.datetime.fromisoformat(iso + "T08:00:00-07:00")
    return d.strftime("%a, %d %b %Y %H:%M:%S %z")

items = "\n".join(f"""    <item>
      <title>{html.escape(a['title'])}</title>
      <link>{a['url']}</link>
      <guid isPermaLink="true">{a['url']}</guid>
      <pubDate>{rfc822(a['published'])}</pubDate>
      <category>{html.escape(a['topic'])}</category>
      <description>{html.escape(a['description'])}</description>
    </item>""" for a in articles)
(ins_dir / "feed.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Emory Financial Insights</title>
    <link>{SITE}/insights</link>
    <atom:link href="{SITE}/insights/feed.xml" rel="self" type="application/rss+xml"/>
    <description>{html.escape(idx_desc)}</description>
    <language>en-us</language>
{items}
  </channel>
</rss>
""", encoding="utf-8")

# ---------------------------------------------------------------- existing pages
latest = f"""  <!-- ============ INSIGHTS ============ -->
  <section class="section section-sand">
    <div class="wrap">
      <div class="process-head">
        <div>
          <p class="eyebrow">Insights</p>
          <h2>What's changing, and what it means for your mortgage</h2>
          <p class="lede mt-3">New articles from Derek on the economy, taxes and family decisions, in plain English.</p>
        </div>
        <a class="btn btn-primary btn-lg" href="/insights">All articles</a>
      </div>
      <div class="grid grid-3">
{chr(10).join(card(a, 'h3') for a in articles[:3])}
      </div>
    </div>
  </section>

"""

for f in out_dir.rglob("*.html"):
    if f.parent == ins_dir:
        continue
    t = f.read_text(encoding="utf-8")
    t = add_insights_links(t)
    t = re.sub(r'<meta name="build" content="[^"]*">', f'<meta name="build" content="{BUILD_ID}">', t)
    t = t.replace('<link rel="stylesheet" href="/assets/css/style.v2.css">',
                  f'<link rel="alternate" type="application/rss+xml" title="Emory Financial Insights" href="{SITE}/insights/feed.xml">\n'
                  '<link rel="stylesheet" href="/assets/css/style.v2.css">', 1)
    if f.name == "index.html" and f.parent == out_dir:
        marker = "  <!-- ============ NEWSLETTER ============ -->"
        assert marker in t, "homepage newsletter marker missing"
        t = t.replace(marker, latest + marker, 1)
        old = ("A short, occasional email: where California rates actually are, what changed in lending "
               "guidelines, and a plain-English breakdown of one thing worth understanding.")
        if old in t:
            t = t.replace(old, "One email a month: the new Insights articles, where California rates "
                               "actually are, and what changed in lending guidelines.")
        t = t.replace("agree to receive occasional email", "agree to receive a monthly email")
    f.write_text(t, encoding="utf-8")

(out_dir / "version.txt").write_text(f"Emory Financial — build {BUILD_ID}\n", encoding="utf-8")

# ---------------------------------------------------------------- sitemap
urls = []
for f in sorted(out_dir.rglob("*.html")):
    rel = f.relative_to(out_dir).as_posix()
    if rel in ("404.html",) or rel.startswith("thanks/"):
        continue
    path = "/" + rel[:-5]
    if path.endswith("/index"):
        path = path[:-6] or "/"
    if path == "/index":
        path = "/"
    pri = "1.0" if path == "/" else "0.8" if path.startswith("/insights") else None
    urls.append((path, pri))
old_pri = dict(re.findall(r"<loc>https://emoryfinancial\.com([^<]*)</loc><lastmod>[^<]*</lastmod><priority>([^<]*)</priority>",
                          (src_dir / "sitemap.xml").read_text()))
lines = []
for path, pri in urls:
    pri = pri or old_pri.get(path, "0.6")
    changed = path.startswith("/insights") or path == "/"
    lastmod = TODAY if changed else "2026-09-14"
    lines.append(f"  <url><loc>{SITE}{path}</loc><lastmod>{lastmod}</lastmod><priority>{pri}</priority></url>")
(out_dir / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "\n".join(lines) + "\n</urlset>\n", encoding="utf-8")

# ---------------------------------------------------------------- robots + llms
(out_dir / "robots.txt").write_text("""# Search engines and AI assistants are welcome to read and cite this site.
User-agent: *
Allow: /
Disallow: /thanks/

User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: https://emoryfinancial.com/sitemap.xml
""", encoding="utf-8")

llms = (here / "llms.txt").read_text(encoding="utf-8")
ins_lines = "\n".join(f"- [{a['title']}]({a['url']})" for a in articles)
llms = re.sub(r"(## Insights \(articles by Derek Shao\)\n- \[All Insights articles\]\([^)]*\)\n)(?:- .*\n)*",
              lambda m: m.group(1) + ins_lines + "\n", llms)
(out_dir / "llms.txt").write_text(llms, encoding="utf-8")

# ---------------------------------------------------------------- netlify.toml
toml = (out_dir / "netlify.toml").read_text(encoding="utf-8")
if "/insights/index.html" not in toml:
    block = """
# ---- Insights (articles) ----
[[redirects]]
  from = "/insights/index.html"
  to = "/insights"
  status = 301
  force = true

[[redirects]]
  from = "/insights/*.html"
  to = "/insights/:splat"
  status = 301
  force = true

[[redirects]]
  from = "/blog"
  to = "/insights"
  status = 301

[[redirects]]
  from = "/blog/*"
  to = "/insights"
  status = 301

[[headers]]
  for = "/insights/feed.xml"
  [headers.values]
    Content-Type = "application/rss+xml; charset=utf-8"

[[headers]]
  for = "/llms.txt"
  [headers.values]
    Content-Type = "text/plain; charset=utf-8"
"""
    marker = "# The deploy check must never be cached"
    toml = toml.replace(marker, block.strip() + "\n\n" + marker, 1)
    (out_dir / "netlify.toml").write_text(toml, encoding="utf-8")

# ---------------------------------------------------------------- CSS
css_path = out_dir / "assets" / "css" / "style.v2.css"
css = css_path.read_text(encoding="utf-8")
if "/* ---------- Insights" not in css:
    css += (here / "insights.css").read_text(encoding="utf-8")
    css_path.write_text(css, encoding="utf-8")

print(f"build {BUILD_ID}: {len(articles)} articles, {len(urls)} sitemap URLs")
for a in articles:
    print(f"  /insights/{a['slug']}  faqs={len(a['faqs'])}")

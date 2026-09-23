"""Build sitemap.xml and sitemap.html from the site's HTML pages.

Run from the repo root: python3 scripts/build-sitemap.py
Pages marked noindex (the per-comment templates under data/*/c/) are left out.
"""
import html
import re
import subprocess
from pathlib import Path

SITE = "https://commonsignals.org"
TODAY = "2026-09-23"
ROOT = Path(__file__).resolve().parent.parent

SECTIONS = [
    ("Main pages", ["index.html", "about.html", "research.html", "findings.html", "tools.html",
                    "training.html", "workshops.html", "updates.html", "theory-of-change.html",
                    "methodology.html", "glossary.html", "privacy.html", "sitemap.html"]),
    ("Research articles", None),
    ("Data explorer", "data/"),
    ("Tools and library", ["research/library/index.html", "tools/comment-analyser/index.html",
                           "tools/messengers/index.html", "tools/segments/index.html"]),
]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def pages():
    files = sorted(set(git("ls-files", "*.html").split()) | {"sitemap.html"})
    out = []
    for f in files:
        p = ROOT / f
        if not p.exists():
            continue
        s = p.read_text(encoding="utf-8")
        if 'content="noindex' in s:
            continue
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', s)
        url = canon.group(1) if canon else SITE + "/" + re.sub(r"(index)?\.html$", "", f)
        title = re.search(r"<title>(.*?)</title>", s, re.S)
        title = html.unescape(re.sub(r": Common Signals$", "", title.group(1).strip())) if title else f
        if f == "index.html":
            title = "Home"
        dirty = git("status", "--porcelain", "--", f)
        lastmod = TODAY if dirty else (git("log", "-1", "--format=%cs", "--", f) or TODAY)
        pub = re.search(r'"datePublished": "([^"]+)"', s)
        out.append(dict(file=f, url=url, title=title, lastmod=lastmod, published=pub.group(1) if pub else ""))
    return out


def group(all_pages):
    by_file = {p["file"]: p for p in all_pages}
    used, groups = set(), []
    for name, rule in SECTIONS:
        if isinstance(rule, list):
            items = [by_file[f] for f in rule if f in by_file]
        elif isinstance(rule, str):
            # Explorer home and compare first, then each study followed by its codebook.
            items = sorted((p for p in all_pages if p["file"].startswith(rule)),
                           key=lambda p: (p["file"] != "data/index.html", p["file"] != "data/compare/index.html",
                                          p["file"].replace("codebook/", ""), "codebook" in p["file"]))
        else:
            items = []
        used.update(p["file"] for p in items)
        groups.append([name, items])
    # Research articles: top-level pages not listed elsewhere, newest first.
    rest = [p for p in all_pages if p["file"] not in used and "/" not in p["file"]]
    groups[1][1] = sorted(rest, key=lambda p: p["published"], reverse=True)
    used.update(p["file"] for p in rest)
    leftovers = [p for p in all_pages if p["file"] not in used]
    if leftovers:
        groups.append(["Other pages", leftovers])
    return groups


def write_xml(all_pages):
    rows = "\n".join(
        f"  <url>\n    <loc>{html.escape(p['url'])}</loc>\n    <lastmod>{p['lastmod']}</lastmod>\n  </url>"
        for p in sorted(all_pages, key=lambda p: p["url"]))
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + "\n</urlset>\n",
        encoding="utf-8")


def write_html(groups):
    tpl = (ROOT / "privacy.html").read_text(encoding="utf-8")
    head, rest = tpl.split('<main id="top">', 1)
    foot = rest.split("</main>", 1)[1]
    desc = "Every page on commonsignals.org, grouped by section."
    head = re.sub(r"<title>.*?</title>", "<title>Sitemap: Common Signals</title>", head)
    for pat, val in [(r'(name="description" content=")[^"]*', desc), (r'(og:title" content=")[^"]*', "Sitemap: Common Signals"),
                     (r'(og:description" content=")[^"]*', desc), (r'(og:url" content=")[^"]*', SITE + "/sitemap"),
                     (r'(twitter:title" content=")[^"]*', "Sitemap: Common Signals"),
                     (r'(twitter:description" content=")[^"]*', desc), (r'(rel="canonical" href=")[^"]*', SITE + "/sitemap")]:
        head = re.sub(pat, lambda m: m.group(1) + val, head, count=1)
    head = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', "", head, flags=re.S)
    slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    toc = "\n".join(f'        <li><a href="#{slug(n)}">{html.escape(n)}</a></li>' for n, items in groups if items)
    body = []
    for n, items in groups:
        if not items:
            continue
        body.append(f'      <h2 id="{slug(n)}">{html.escape(n)}</h2>\n      <ul class="arrow-list">')
        for p in items:
            path = p["url"].replace(SITE, "") or "/"
            body.append(f'        <li><a href="{html.escape(path)}">{html.escape(p["title"], quote=False)}</a></li>')
        body.append("      </ul>\n")
    main = f'''<main id="top">

  <div class="article-hero">
    <p class="article-eyebrow">Last updated: {int(TODAY[8:])} September 2026</p>
    <h1>Sitemap</h1>
    <p class="article-dek">{desc} A machine-readable version is at <a href="/sitemap.xml">sitemap.xml</a>.</p>
  </div>

  <div class="article-shell">
    <aside class="article-toc" aria-label="Table of contents">
      <p class="toc-heading">Contents</p>
      <ul>
{toc}
      </ul>
    </aside>

    <article class="article-body">

''' + "\n".join(body) + '''    </article>
  </div>

</main>'''
    (ROOT / "sitemap.html").write_text(head + main + foot, encoding="utf-8")


if __name__ == "__main__":
    write_html(group(pages()))      # first pass creates sitemap.html so it lists itself
    all_pages = pages()
    write_html(group(all_pages))
    write_xml(all_pages)

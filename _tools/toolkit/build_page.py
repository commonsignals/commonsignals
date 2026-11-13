"""Build /how-to-communicate-about-ai-safety from the toolkit draft.

Usage: python3 _tools/toolkit/build_page.py   (from the repo root)

Reads _incoming/how-to-communicate-about-ai-safety-2026-11/article.md (with its figures already in
place), copies the images it uses into assets/toolkit/, and writes how-to-communicate-about-ai-safety.html
on the reading-list page's template. Editorial comments in the draft (<!-- ... -->) are dropped, so
unfilled screenshot placeholders never reach the page.

Handles only the Markdown this draft uses: #-headings, paragraphs, - and 1. lists, **bold**, *italic*,
[links](url), raw <figure> blocks and the STAT CALLOUT block.
"""
import html
import json
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INC = os.path.join(ROOT, "_incoming", "how-to-communicate-about-ai-safety-2026-11")
SRC = os.path.join(INC, "article.md")
SLUG = "how-to-communicate-about-ai-safety"
OUT = os.path.join(ROOT, f"{SLUG}.html")
TEMPLATE = os.path.join(ROOT, "ai-safety-comms-reading-list.html")
ASSET_DIR = os.path.join(ROOT, "assets", "toolkit")
DATE_ISO, DATE_TEXT = "2026-11-06", "6 November 2026"
TAGS = ["Messaging", "Public opinion"]

# Charts that already live in assets/ (with phone versions) are reused, not copied.
REUSE = {
    "S14-soares-reel-stance.svg": ("/assets/chart-stance.svg?v=2", "/assets/chart-stance-mobile.svg?v=2"),
    "S16-metr-before-after.svg": ("/assets/mchart-lead-before-after.svg?v=2", "/assets/mchart-lead-before-after-mobile.svg?v=2"),
    "S17-amanpour-stance.svg": ("/assets/chart-amanpour-stance.svg?v=2", "/assets/chart-amanpour-stance-mobile.svg?v=2"),
}
# Charts with a phone version saved beside them in the screenshots folder.
HAS_MOBILE = {"S23a-uk-ai-metaphors.svg", "S23b-uk-ai-mindsets.svg", "S15-doac-four-versions.svg"}

# S15's phone version exists only inline in the DOAC article; save it beside the desktop export.
_doac = open(os.path.join(ROOT, "cant-we-just-unplug-it-doac-ai-debate-comment-analysis.html"), encoding="utf-8").read()
_m = re.search(r'<div class="chart-mobile">(<svg.*?</svg>)</div>', _doac, re.S)
assert _m and "Four versions of one debate" in _m.group(1)
open(os.path.join(INC, "screenshots", "S15-doac-four-versions-mobile.svg"), "w", encoding="utf-8").write(_m.group(1) + "\n")

text = open(SRC, encoding="utf-8").read()


# ---------------------------------------------------------------- inline

def slug(s):
    s = re.sub(r"<[^>]+>", "", s).lower().replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def link(m):
    label, url = m.group(1), m.group(2)
    if url.startswith("https://commonsignals.org"):
        url = url[len("https://commonsignals.org"):] or "/"
        return f'<a href="{url}">{label}</a>'
    if url.startswith("#") or url.startswith("/"):
        return f'<a href="{url}">{label}</a>'
    return f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\bhello@commonsignals\.org\b(?![^<]*</a>)", '<a href="mailto:hello@commonsignals.org">hello@commonsignals.org</a>', s)
    return grades(s)


GRADE_WORD = re.compile(r"(?<![A-Za-z])(established|tested|observed)\b", re.I)


def grade_span(word):
    return (f'<span class="grade grade-{word.lower()}"><span class="grade-dot" aria-hidden="true"></span>'
            f'{word}</span>')


def grades(s):
    """Traffic-light dot before each evidence grade: in bracketed grades such as "(Tested)" or
    "(Established for fear and agency; tested for anger)", and on the bold labels of the grade key.
    "untested" is left alone."""
    def bracket(m):
        inner = GRADE_WORD.sub(lambda w: grade_span(w.group(1)), m.group(1))
        # Keep the opening bracket inside the first (non-wrapping) grade, so it can't be left
        # at the end of a line while the dot wraps to the next.
        if inner.startswith('<span class="grade '):
            return re.sub(r'^(<span class="grade [^"]+">)', r"\1(", inner, count=1) + ")"
        return "(" + inner + ")"
    s = re.sub(r"\(((?:Established|Tested|Observed)\b[^()]*)\)", bracket, s)
    return re.sub(r"<strong>(Established|Tested|Observed):</strong>",
                  lambda m: f"<strong>{grade_span(m.group(1))}:</strong>", s)


# ---------------------------------------------------------------- figures


def dims(path):
    """Intrinsic size for width/height attributes, so lazy images don't shift the page as they load.
    Screenshots are captured at 2x, so their CSS size is half their pixel size."""
    if path.endswith(".png"):
        from PIL import Image
        w, h = Image.open(path).size
        return w // 2, h // 2
    raw = open(path, encoding="utf-8").read(400)
    m = re.search(r'<svg[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"', raw)
    return round(float(m.group(1))), round(float(m.group(2)))

def figure(block):
    src = re.search(r'src="screenshots/([^"]+)"', block).group(1)
    alt = html.unescape(re.search(r'alt="([^"]*)"', block).group(1))
    cap = html.unescape(re.search(r"<figcaption>(.*?)</figcaption>", block, re.S).group(1))
    return figure_html(src, alt, cap)


# Placeholders in the draft (<!-- SCREENSHOT Sxx ... --> / <!-- CHART Sxx ... -->) are filled from the
# manifest: its file, alt text and caption (the manifest holds the corrected captions). Shots the
# manifest marks as anything but done are dropped.
import csv  # noqa: E402
MANIFEST = {r["id"]: r for r in csv.DictReader(open(os.path.join(INC, "screenshots", "manifest.csv"), encoding="utf-8"))}


def placeholder(m):
    row = MANIFEST.get(m.group(1))
    if not row or row["status"] != "done":
        return ""
    return hold(figure_html(row["file"], row["alt"], row["caption"]))


def figure_html(src, alt, cap):
    alt_a, cap_h = html.escape(alt), html.escape(cap, quote=False)
    if src in REUSE:
        desk, mob = REUSE[src]
    else:
        os.makedirs(ASSET_DIR, exist_ok=True)
        shutil.copyfile(os.path.join(INC, "screenshots", src), os.path.join(ASSET_DIR, src))
        desk, mob = f"/assets/toolkit/{src}", None
        if src in HAS_MOBILE:
            m = src.replace(".svg", "-mobile.svg")
            shutil.copyfile(os.path.join(INC, "screenshots", m), os.path.join(ASSET_DIR, m))
            mob = f"/assets/toolkit/{m}"
    local = os.path.join(ROOT, desk.split("?")[0].lstrip("/"))
    w, h = dims(local)
    shot = src.endswith(".png")
    cls = ' class="shot"' if shot else ""
    if mob:
        mw, mh = dims(os.path.join(ROOT, mob.split("?")[0].lstrip("/")))
        pic = (f'<picture>\n          <source media="(max-width: 640px)" srcset="{mob}" width="{mw}" height="{mh}" />\n'
               f'          <img src="{desk}" alt="{alt_a}" width="{w}" height="{h}" loading="lazy" />\n        </picture>')
    else:
        pic = f'<img src="{desk}" alt="{alt_a}" width="{w}" height="{h}" loading="lazy" />'
    return f'<figure{cls}>\n        {pic}\n        <figcaption>{cap_h}</figcaption>\n      </figure>'


# ---------------------------------------------------------------- blocks

# Pull the hero parts out first.
title = re.search(r"^# (.+)$", text, re.M).group(1)
m = re.search(r"<!-- STANDFIRST.*?-->\n(.+)\n", text)
dek = m.group(1).strip()
byline = re.search(r"^Written by (.+?) //", text, re.M).group(1).strip()
body = text[text.index("Written by"):].split("\n", 1)[1]

# Figures and the stat callout become placeholders so the line parser leaves them alone.
held = []


def hold(s):
    held.append(s)
    return f"\n@@HELD{len(held) - 1}@@\n"


body = re.sub(r"<figure>.*?</figure>", lambda m: hold(figure(m.group(0))), body, flags=re.S)
body = re.sub(r"<!-- (?:SCREENSHOT|CHART) (S\d+[ab]?)\b.*?-->", placeholder, body, flags=re.S)


def stat(m):
    lines = [l.strip() for l in m.group(1).strip().splitlines() if l.strip()]
    fig = lines[0].strip("*")
    src = lines[-1].strip("*")
    txt = " ".join(lines[1:-1])
    return hold(f'<aside class="stat-pull" aria-label="Key figure">\n        <p class="stat-pull-figure">{html.escape(fig)}</p>\n'
                f'        <p class="stat-pull-text">{inline(txt)}</p>\n        <p class="stat-pull-source">{inline(src)}</p>\n      </aside>')


body = re.sub(r"<!-- STAT CALLOUT[^>]*-->(.*?)<!-- /STAT CALLOUT -->", stat, body, flags=re.S)
body = re.sub(r"<!--.*?-->", "", body, flags=re.S)  # editorial notes and unfilled placeholders

def table(p):
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in p.splitlines()]
    head, body_rows = rows[0], [r for r in rows[2:]]
    assert all(re.fullmatch(r":?-{3,}:?", c) for c in rows[1]), "table separator"
    cell = lambda c: "<br>".join(inline(x.strip()) for x in c.split("<br>"))
    ths = "".join(f'<th scope="col">{inline(h)}</th>' for h in head)
    trs = []
    for r in body_rows:
        first = f'<th scope="row">{cell(r[0])}</th>'
        rest = "".join(f'<td data-label="{html.escape(h)}">{cell(c)}</td>' for h, c in zip(head[1:], r[1:]))
        trs.append(f"          <tr>{first}{rest}</tr>")
    return ('<div class="table-wrap">\n        <table class="card-table">\n          <thead><tr>' + ths +
            '</tr></thead>\n          <tbody>\n' + "\n".join(trs) + '\n          </tbody>\n        </table>\n      </div>')


is_ul = lambda p: all(l.startswith("- ") for l in p.splitlines())
ids = set()


def uid(h):
    base = slug(h)
    hid, n = base, 2
    while hid in ids:
        hid, n = f"{base}-{n}", n + 1
    ids.add(hid)
    return hid


out, toc = [], []
paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
i = 0
while i < len(paras):
    p = paras[i]
    if p.startswith("@@HELD"):
        out.append(held[int(re.search(r"\d+", p).group())])
    elif p.startswith("### Disclosure"):
        nxt = paras[i + 1]
        out.append(f'<div class="article-disclosure">\n        <h3>Disclosure</h3>\n        <p>{inline(nxt)}</p>\n      </div>')
        i += 1
    elif p.startswith("## "):
        h = p[3:].strip()
        hid = uid(h)
        toc.append((hid, h))
        out.append(f'<h2 id="{hid}">{inline(h)}</h2>')
    elif p.startswith("### "):
        h = p[4:].strip()
        out.append(f'<h3 id="{uid(h)}">{inline(h)}</h3>')
    elif p.startswith("**Who this is for:**"):
        out.append('<div class="audience-callout">\n        <p class="audience-label">Who this is for</p>\n'
                   f'        <p>{inline((lambda t: t[:1].upper() + t[1:])(p[len("**Who this is for:**"):].strip()))}</p>\n      </div>')
    elif p.startswith("|"):
        out.append(table(p))
    elif is_ul(p):
        # Items separated by blank lines are still one list.
        lines = p.splitlines()
        while i + 1 < len(paras) and is_ul(paras[i + 1]):
            i += 1
            lines += paras[i].splitlines()
        items = "\n".join(f"        <li>{inline(l[2:])}</li>" for l in lines)
        key = all(re.match(r"- \*\*(Established|Tested|Observed):\*\*", l) for l in lines)
        out.append(f'<ul class="{"grade-key" if key else "arrow-list"}">\n{items}\n      </ul>')
    elif all(re.match(r"\d+\. ", l) for l in p.splitlines()):
        items = "\n".join(f"        <li>{inline(re.sub(r'^\d+\. ', '', l))}</li>" for l in p.splitlines())
        out.append(f'<ol class="toolkit-list">\n{items}\n      </ol>')
    else:
        assert "\n" not in p, f"unexpected multi-line block: {p[:80]}"
        out.append(f"<p>{inline(p)}</p>")
    i += 1

article = "\n\n      ".join(out)
toc_html = "\n".join(f'        <li><a href="#{hid}">{inline(h)}</a></li>' for hid, h in toc)
leftover = re.findall(r"\*\*|\]\(|<!--", article)
assert not leftover, f"unconverted markdown: {leftover[:5]}"

# ---------------------------------------------------------------- template

tpl = open(TEMPLATE, encoding="utf-8").read()
OLD_T = "AI safety comms reading list: where to start"
OLD_D = ("A reading list of the existing research on how the public receives messages about AI risk, for anyone new to AI "
         "safety who wants to join the conversation knowing what's already been tested.")
DESC = ("An evidence-based guide for anyone explaining AI risks to the public: ten principles, four ground rules, six UK "
        "mindsets and seven issue guides, each graded by the strength of its evidence.")
head = tpl[:tpl.index("<style>")]
assert head.count(OLD_D) == 4 and OLD_T in head
head = (head.replace(OLD_D, html.escape(DESC, quote=True).replace("&#x27;", "'"))
            .replace(OLD_T, title)
            .replace("/ai-safety-comms-reading-list", f"/{SLUG}")
            .replace('"datePublished": "2026-10-15"', f'"datePublished": "{DATE_ISO}"')
            .replace('"dateModified": "2026-10-15"', f'"dateModified": "{DATE_ISO}"')
            .replace('"author": { "@type": "Organization", "name": "Common Signals", "url": "https://commonsignals.org/" }',
                     f'"author": {{ "@type": "Person", "name": "{byline}" }}'))
style = """<style>
  .article-body .toolkit-list { margin: 1.2rem 0; padding-left: 1.4rem; display: grid; gap: 0.6rem; }
  .article-body .toolkit-list li { padding-left: 0.2rem; color: var(--ink-soft); line-height: 1.6; min-width: 0; }
  .article-body .toolkit-list li::marker { color: var(--signal); font-weight: 600; }
  /* Screenshots of other organisations' pages: framed so they read as images, not as this page. */
  .article-body figure.shot img { border: 1px solid var(--line); border-radius: 8px; background: #fff; }

  /* Stat pull quotes, as on the DOAC article */
  .article-body .stat-pull {
    display: grid;
    grid-template-columns: minmax(8.5rem, auto) 1fr;
    gap: 0.4rem 1.4rem;
    align-items: baseline;
    margin: 2.2rem 0;
    padding: 1.3rem 0 1.2rem;
    border-top: 3px solid var(--signal);
    border-bottom: 1px solid var(--line);
  }
  .article-body .stat-pull p { margin: 0; }
  .article-body .stat-pull-figure {
    font-family: var(--serif);
    font-weight: 600;
    font-size: 2.9rem;
    line-height: 1;
    color: var(--signal);
    font-variant-numeric: lining-nums proportional-nums;
  }
  .article-body .stat-pull-text {
    font-family: var(--serif);
    font-size: 1.25rem;
    line-height: 1.45;
    color: var(--ink);
  }
  .article-body .stat-pull-source {
    grid-column: 2;
    font-family: var(--sans);
    font-size: 0.9rem;
    color: var(--muted);
  }
  @media (max-width: 640px) {
    .article-body .stat-pull { grid-template-columns: 1fr; }
    .article-body .stat-pull-source { grid-column: 1; }
  }
  /* Evidence grades: a traffic-light dot before each grade. Green and red are the site's chart
     teal and maroon; amber is an ochre that sits on the paper background. The word always stays. */
  .grade { white-space: nowrap; }
  .grade-dot {
    display: inline-block;
    width: 0.62em;
    height: 0.62em;
    margin: 0 0.32em 0.06em 0.05em;
    border-radius: 50%;
    vertical-align: middle;
    box-shadow: 0 0 0 1px rgba(35, 32, 25, 0.12);
  }
  .grade-established .grade-dot { background: #0f8a78; }
  .grade-tested .grade-dot { background: #c98a17; }
  .grade-observed .grade-dot { background: #a8323e; }
  .article-body .grade-key { list-style: none; margin: 1.2rem 0 1.6rem; padding: 0; display: grid; gap: 0.7rem; }
  .article-body .grade-key li { color: var(--ink-soft); line-height: 1.6; }
  .article-body .grade-key .grade-dot { width: 0.8em; height: 0.8em; }

  /* Mindsets table: a table on wide screens, one card per mindset on phones. */
  .article-body .card-table th[scope="row"] { font-weight: 600; white-space: normal; border-bottom: 1px solid var(--line); color: var(--ink); }
  .article-body .card-table th[scope="col"] { white-space: normal; }
  .article-body .card-table { font-size: 0.95rem; }
  @media (max-width: 640px) {
    .article-body .card-table thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
    .article-body .card-table, .article-body .card-table tbody, .article-body .card-table tr,
    .article-body .card-table th, .article-body .card-table td { display: block; width: auto; }
    .article-body .card-table tr { border: 1px solid var(--line); border-radius: 8px; margin: 0 0 1rem; padding: 0.4rem 0.9rem 0.7rem; background: rgba(255, 255, 255, 0.45); }
    .article-body .card-table th[scope="row"] { border-bottom: 2px solid var(--ink); padding: 0.5rem 0; font-size: 1.05rem; }
    .article-body .card-table td { padding: 0.55rem 0; border-bottom: 1px solid var(--line); }
    .article-body .card-table td:last-child { border-bottom: 0; }
    .article-body .card-table td::before { content: attr(data-label); display: block; font-weight: 600; color: var(--ink); font-size: 0.85rem; margin-bottom: 0.15rem; }
  }

  /* In-page jumps land below the sticky site header (the phone rule further down adds the section bar). */
  .article-body h2, .article-body h3 { scroll-margin-top: 5.5rem; }

  /* Mobile section navigator: "You are currently reading", after JRF's report pages.
     Sits under the sticky site header; only on widths where the sidebar contents is not sticky. */
  .section-nav { display: none; }
  @media (max-width: 860px) {
    .section-nav {
      display: block;
      position: fixed;
      left: 0;
      right: 0;
      top: var(--section-nav-top, 0px);
      z-index: 19;
      background: var(--ink);
      color: var(--paper);
      font-family: var(--sans);
      transform: translateY(-110%);
      visibility: hidden;
      transition: transform 0.2s ease, visibility 0s linear 0.2s;
      box-shadow: 0 6px 16px rgba(35, 32, 25, 0.18);
    }
    .section-nav.is-visible {
      transform: translateY(0);
      visibility: visible;
      transition: transform 0.2s ease, visibility 0s;
    }
    .section-nav-bar {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 0.6rem 1rem;
      max-width: 1200px;
      margin: 0 auto;
    }
    .section-nav-current { flex: 1; min-width: 0; margin: 0; line-height: 1.3; }
    .section-nav-label { display: block; font-size: 0.8rem; font-weight: 500; color: var(--signal-soft); }
    .section-nav-title {
      display: block;
      font-size: 0.98rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .section-nav-toggle {
      flex: none;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      min-height: 44px;
      padding: 0 0.2rem;
      background: none;
      border: 0;
      color: var(--paper);
      font: 500 0.92rem var(--sans);
      cursor: pointer;
    }
    .section-nav-toggle svg { width: 10px; height: 10px; transition: transform 0.2s ease; }
    .section-nav-toggle[aria-expanded="true"] svg { transform: rotate(180deg); }
    .section-nav-toggle:focus-visible, .section-nav-list a:focus-visible { outline: 2px solid var(--signal-soft); outline-offset: 2px; }
    .section-nav-panel {
      border-top: 1px solid rgba(245, 244, 239, 0.16);
      max-height: calc(100vh - var(--section-nav-top, 0px) - 4rem);
      max-height: calc(100dvh - var(--section-nav-top, 0px) - 4rem);
      overflow-y: auto;
      overscroll-behavior: contain;
    }
    .section-nav-list { list-style: none; margin: 0 auto; padding: 0.5rem 1rem 1rem; max-width: 1200px; }
    .section-nav-list a {
      display: block;
      padding: 0.55rem 0 0.55rem 0.8rem;
      border-left: 2px solid transparent;
      color: rgba(245, 244, 239, 0.86);
      text-decoration: none;
      font-size: 0.98rem;
      line-height: 1.35;
    }
    .section-nav-list a[aria-current="true"] { color: #fff; border-left-color: var(--signal-soft); font-weight: 500; }
    .article-body h2, .article-body h3 { scroll-margin-top: calc(var(--section-nav-top, 0px) + 5.25rem); }
  }
  @media (prefers-reduced-motion: reduce) {
    .section-nav, .section-nav.is-visible, .section-nav-toggle svg { transition: none; }
  }
</style>
"""
mid = tpl[tpl.index("</style>") + len("</style>\n"):tpl.index('<main id="top">')]
tail = tpl[tpl.index('<section id="article-subscribe"'):]
tags = "\n".join(f'      <span class="tag-pill">{t}</span>' for t in TAGS)
share = re.search(r'    <div class="hero-actions">.*?\n    </div>\n', tpl, re.S).group(0)

nav_items = "\n".join(f'          <li><a href="#{hid}">{inline(h)}</a></li>' for hid, h in toc)
first_title = inline(toc[0][1])
section_nav = f"""  <nav class="section-nav" id="sectionNav" aria-label="Sections">
    <div class="section-nav-bar">
      <p class="section-nav-current"><span class="section-nav-label">You are currently reading:</span>
        <span class="section-nav-title" id="sectionNavTitle">{first_title}</span></p>
      <button type="button" class="section-nav-toggle" id="sectionNavToggle" aria-expanded="false" aria-controls="sectionNavPanel">
        <span class="section-nav-toggle-text">View all sections</span>
        <svg viewBox="0 0 10 6" aria-hidden="true"><path d="M0 0h10L5 6z" fill="currentColor"/></svg>
      </button>
    </div>
    <div class="section-nav-panel" id="sectionNavPanel" hidden>
      <ul class="section-nav-list">
{nav_items}
      </ul>
    </div>
  </nav>
"""
section_nav_js = """<script>
(function () {
  var nav = document.getElementById('sectionNav');
  if (!nav) return;
  var header = document.querySelector('header.site');
  var toc = document.querySelector('.article-toc');
  var body = document.querySelector('.article-body');
  var title = document.getElementById('sectionNavTitle');
  var toggle = document.getElementById('sectionNavToggle');
  var toggleText = toggle.querySelector('.section-nav-toggle-text');
  var panel = document.getElementById('sectionNavPanel');
  var links = Array.prototype.slice.call(panel.querySelectorAll('a'));
  var heads = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
  var mq = window.matchMedia('(max-width: 860px)');
  var ticking = false;

  function headerHeight() { return header ? header.getBoundingClientRect().height : 0; }
  function setTop() { document.documentElement.style.setProperty('--section-nav-top', headerHeight() + 'px'); }

  function setOpen(open) {
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggleText.textContent = open ? 'Close' : 'View all sections';
    panel.hidden = !open;
  }

  function update() {
    ticking = false;
    if (!mq.matches) { nav.classList.remove('is-visible'); setOpen(false); return; }
    var top = headerHeight();
    var line = top + nav.getBoundingClientRect().height + 24;
    var current = 0;
    for (var i = 0; i < heads.length; i++) {
      if (heads[i] && heads[i].getBoundingClientRect().top <= line) current = i;
    }
    links.forEach(function (a, i) {
      if (i === current) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
    });
    title.textContent = links[current].textContent;
    // Show once the page's own contents list has scrolled away; hide after the article ends.
    var afterToc = toc ? toc.getBoundingClientRect().bottom < top : true;
    var inBody = body.getBoundingClientRect().bottom > top + 80;
    var show = afterToc && inBody;
    nav.classList.toggle('is-visible', show);
    if (!show) setOpen(false);
  }
  function onScroll() { if (!ticking) { ticking = true; window.requestAnimationFrame(update); } }

  toggle.addEventListener('click', function () { setOpen(panel.hidden); });
  links.forEach(function (a) { a.addEventListener('click', function () { setOpen(false); }); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !panel.hidden) { setOpen(false); toggle.focus(); }
  });
  document.addEventListener('click', function (e) { if (!panel.hidden && !nav.contains(e.target)) setOpen(false); });

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', function () { setTop(); onScroll(); });
  if (header && 'ResizeObserver' in window) new ResizeObserver(function () { setTop(); onScroll(); }).observe(header);
  setTop();
  update();
})();
</script>
"""
# Section addresses from earlier live versions of the page, so links shared since 6 November still
# land on the right section. Sections that were cut outright are left out (those open at the top).
OLD_ANCHORS = {
    "what-this-toolkit-is": "what-we-mean-by-ai-safety",
    "how-to-read-the-evidence": "how-we-grade-the-evidence",
    "summary": "executive-summary",
    "the-big-picture": "where-the-public-stands-on-ai",
    "the-big-picture-where-the-public-stands": "where-the-public-stands-on-ai",
    "ten-principles": "ten-principles-for-ai-safety-communications",
    "ground-rules": "4-ground-rules-for-every-communicator",
    "six-uk-mindsets": "six-uk-mindsets-audience-profiles",
    "disengaged-traditionalists-24-1": "six-uk-mindsets-audience-profiles",
    "alarmed-populists-19-5": "six-uk-mindsets-audience-profiles",
    "pragmatic-sceptics-16-3": "six-uk-mindsets-audience-profiles",
    "market-optimists-16-3": "six-uk-mindsets-audience-profiles",
    "hopeful-regulators-12-8": "six-uk-mindsets-audience-profiles",
    "uncertain-middle-11-1": "six-uk-mindsets-audience-profiles",
    "talking-about-specific-issues": "issue-guides-three-dos-and-a-dont",
    "loss-of-control-and-catastrophic-risk": "1-loss-of-control-and-catastrophic-risk",
    "regulation-and-independent-oversight": "2-regulation-and-independent-oversight",
    "jobs-and-the-economy": "3-jobs-and-the-economy",
    "children-and-young-people": "4-children-and-young-people",
    "deepfakes-and-knowing-whats-real": "5-deepfakes-and-synthetic-media",
    "ai-war-and-national-security": "6-ai-war-and-national-security",
    "a-pause-ban-or-treaty": "7-a-pause-ban-or-treaty",
    "a-ten-question-check": "10-point-pre-publication-checklist",
    "cutting-long-form-content-for-social": "cutting-long-form-content-for-social-media",
}
missing = {k: v for k, v in OLD_ANCHORS.items() if v not in ids}
assert not missing, f"old-address targets not on the page: {missing}"
assert not set(OLD_ANCHORS) & ids, "an old address is still a live id"
old_anchor_js = """<script>
(function () {
  var moved = %s;
  function follow() {
    var old = decodeURIComponent(location.hash.slice(1));
    if (!old || document.getElementById(old) || !moved[old]) return;
    var target = document.getElementById(moved[old]);
    if (!target) return;
    history.replaceState(null, '', '#' + moved[old]);
    target.scrollIntoView();
  }
  window.addEventListener('hashchange', follow);
  // Wait for the web fonts: text above the target reflows when they load and would push it off.
  var ready = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();
  ready.then(function () { if (document.readyState === 'complete') follow(); else window.addEventListener('load', follow); });
})();
</script>
""" % json.dumps(OLD_ANCHORS, separators=(",", ":"))

main = f"""<main id="top">

{section_nav}
  <div class="article-hero">
    <p class="article-eyebrow">{DATE_TEXT} &middot; {html.escape(byline)}</p>
    <div class="tag-row">
{tags}
    </div>
    <h1>{html.escape(title)}</h1>
    <p class="article-dek">{inline(dek)}</p>
{share}  </div>

  <div class="article-shell">
    <aside class="article-toc" aria-label="Table of contents">
      <p class="toc-heading">Contents</p>
      <ul>
{toc_html}
      </ul>
    </aside>

    <article class="article-body">

      {article}
    </article>
  </div>

{section_nav_js}
{old_anchor_js}
"""
open(OUT, "w", encoding="utf-8").write(head + style + mid + main + tail)
print(f"wrote {os.path.relpath(OUT, ROOT)}: {len(toc)} sections, {len(held)} figures and callouts")

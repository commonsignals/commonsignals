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
    return s


# ---------------------------------------------------------------- figures

def figure(block):
    src = re.search(r'src="screenshots/([^"]+)"', block).group(1)
    alt = html.unescape(re.search(r'alt="([^"]*)"', block).group(1))
    cap = html.unescape(re.search(r"<figcaption>(.*?)</figcaption>", block, re.S).group(1))
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
    shot = src.endswith(".png")
    cls = ' class="shot"' if shot else ""
    if mob:
        pic = (f'<picture>\n          <source media="(max-width: 640px)" srcset="{mob}" />\n'
               f'          <img src="{desk}" alt="{alt_a}" loading="lazy" />\n        </picture>')
    else:
        pic = f'<img src="{desk}" alt="{alt_a}" loading="lazy" />'
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


def stat(m):
    lines = [l.strip() for l in m.group(1).strip().splitlines() if l.strip()]
    fig = lines[0].strip("*")
    src = lines[-1].strip("*")
    txt = " ".join(lines[1:-1])
    return hold(f'<aside class="stat-pull" aria-label="Key figure">\n        <p class="stat-pull-figure">{html.escape(fig)}</p>\n'
                f'        <p class="stat-pull-text">{inline(txt)}</p>\n        <p class="stat-pull-source">{inline(src)}</p>\n      </aside>')


body = re.sub(r"<!-- STAT CALLOUT[^>]*-->(.*?)<!-- /STAT CALLOUT -->", stat, body, flags=re.S)
body = re.sub(r"<!--.*?-->", "", body, flags=re.S)  # editorial notes and unfilled placeholders

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
        hid = slug(h)
        toc.append((hid, h))
        out.append(f'<h2 id="{hid}">{inline(h)}</h2>')
    elif p.startswith("### "):
        h = p[4:].strip()
        out.append(f'<h3 id="{slug(h)}">{inline(h)}</h3>')
    elif p.startswith("**Who this is for:**"):
        out.append('<div class="audience-callout">\n        <p class="audience-label">Who this is for</p>\n'
                   f'        <p>{inline((lambda t: t[:1].upper() + t[1:])(p[len("**Who this is for:**"):].strip()))}</p>\n      </div>')
    elif all(l.startswith("- ") for l in p.splitlines()):
        items = "\n".join(f"        <li>{inline(l[2:])}</li>" for l in p.splitlines())
        out.append(f'<ul class="arrow-list">\n{items}\n      </ul>')
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
DESC = ("An evidence-based toolkit for anyone explaining AI risks to the public: ten principles, four ground rules, six UK "
        "mindsets and advice on seven issues, each graded by the strength of its evidence.")
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
</style>
"""
mid = tpl[tpl.index("</style>") + len("</style>\n"):tpl.index('<main id="top">')]
tail = tpl[tpl.index('<section id="article-subscribe"'):]
tags = "\n".join(f'      <span class="tag-pill">{t}</span>' for t in TAGS)
share = re.search(r'    <div class="hero-actions">.*?\n    </div>\n', tpl, re.S).group(0)
main = f"""<main id="top">

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

"""
open(OUT, "w", encoding="utf-8").write(head + style + mid + main + tail)
print(f"wrote {os.path.relpath(OUT, ROOT)}: {len(toc)} sections, {len(held)} figures and callouts")

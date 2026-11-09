"""Pre-render the /data/ pages so they can be read without running JavaScript.

Run from anywhere: python3 scripts/build-data-pages.py

Reads data/studies/index.json and each study's study.json and codebook.json, and
replaces only the regions between the build-data:start/end markers in:

  data/index.html                   the study cards
  data/<slug>/index.html            the Dataset JSON-LD, title, counts, platform and
                                    changelog, plus the companion article link
  data/<slug>/codebook/index.html   the title and the whole codebook

The comment explorer on data/<slug>/ stays client-side. Run this after
scripts/data-export.py index whenever a study changes. Running it twice changes
nothing the second time.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STUDIES = DATA / "studies"
SITE = "https://commonsignals.org"

PLATFORM_LABEL = {"reddit": "Reddit", "youtube": "YouTube", "youtube_shorts": "YouTube Shorts",
                  "instagram": "Instagram", "facebook": "Facebook", "tiktok": "TikTok", "x": "X"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"]
LICENCE_URLS = {"CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/"}
COMMON_SIGNALS = {"@type": "Organization", "name": "Common Signals", "url": f"{SITE}/"}

# study.json has no publication date, so datePublished comes from the changelog:
# the first entry for the first version released as a dataset. That is version 1
# unless listed here. These studies' version 1 files were never published (their
# changelogs and the git history put the first public file at version 2).
FIRST_PUBLIC_VERSION = {"amanpour-segment-2026-09": 2, "cotra-episode-2026-09": 2, "soares-reel-2026-08": 2}

JSONLD_RE = re.compile(r'<script type="application/ld\+json">\n?(.*?)\n?</script>', re.S)
ARTICLE_LINK_RE = re.compile(r'<a id="articleLink" href="[^"]*"(?: hidden)?>')


def esc(value):
    """Same escaping as CS.esc in data/assets/core.js."""
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def format_date(iso):
    year, month, day = iso.split("-")
    return f"{int(day)} {MONTHS[int(month) - 1]} {year}"


def dim_label(dim):
    """Same as CS.dimLabel: humanise labels written as raw identifiers."""
    label = dim.get("label") or dim["key"]
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+", label):
        return label
    text = re.sub(r"^mentions_", "", dim["key"]).replace("_", " ")
    return text[:1].upper() + text[1:]


def replace_region(page, path, name, content):
    start, end = f"<!-- build-data:start {name} -->", f"<!-- build-data:end {name} -->"
    pattern = r"([ \t]*)" + re.escape(start) + r".*?" + re.escape(end)
    if len(re.findall(pattern, page, flags=re.S)) != 1:
        raise SystemExit(f"{path.relative_to(ROOT)} needs exactly one '{name}' region between build-data markers")
    return re.sub(pattern, lambda m: f"{m.group(1)}{start}\n{content}\n{m.group(1)}{end}", page, flags=re.S)


def write_if_changed(path, page, original):
    if page != original:
        path.write_text(page, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


def changelog_html(changelog, version):
    if not changelog:
        return ""
    items = "".join(f"<li><strong>v{esc(c['version'])}</strong>, {esc(format_date(c['date']))}: {esc(c['note'])}</li>"
                    for c in changelog)
    label = f"Changelog (version {esc(version)})" if version else "Changelog"
    return f'<details class="study-changelog"><summary>{label}</summary><ul>{items}</ul></details>'


def study_card(s):
    slug = esc(s["slug"])
    article = (f'\n            <a class="btn btn-ghost" href="{esc(s["article_url"])}">Read the article</a>'
               if s.get("article_url") else "")
    return f"""        <article class="study-card">
          <h2>{esc(s["title"])}</h2>
          <p class="platform">{esc(PLATFORM_LABEL.get(s["platform"], s["platform"]))}</p>
          <div class="facts">
            <div><span class="k">Coded</span><span class="v">{s["counts"]["coded"]:,}</span></div>
            <div><span class="k">Positioned</span><span class="v">{s["counts"]["clear_position_base"]:,}</span></div>
          </div>
          <div class="actions">
            <a class="btn btn-primary" href="/data/{slug}/">Explore comments</a>{article}
          </div>
          <p class="raw-links">
            <a href="/data/studies/{slug}/study.json">study.json</a><span>&middot;</span><a href="/data/{slug}/codebook/">codebook</a><span>&middot;</span><a href="/data/studies/{slug}/comments.csv">comments.csv</a>
          </p>
          {changelog_html(s.get("changelog"), s.get("version"))}
        </article>"""


def date_published(study):
    version = FIRST_PUBLIC_VERSION.get(study["slug"], 1)
    dates = [c["date"] for c in study.get("changelog", []) if c.get("version") == version and c.get("date")]
    return min(dates) if dates else None


def dataset_jsonld(study, page):
    """The study's Dataset block. study.json has no description, so the one already
    published in this block is kept as it stands, and left out if there is none."""
    slug = study["slug"]
    block = JSONLD_RE.search(page)
    existing = json.loads(block.group(1)) if block else {}
    licence = next((url for name, url in LICENCE_URLS.items() if study.get("licence", "").startswith(name)), None)

    ld = {"@context": "https://schema.org", "@type": "Dataset", "name": study["title"]}
    if existing.get("description"):
        ld["description"] = existing["description"]
    ld["url"] = f"{SITE}/data/{slug}/"
    if licence:
        ld["license"] = licence
    ld["creator"] = COMMON_SIGNALS
    published = date_published(study)
    if published:
        ld["datePublished"] = published
    ld["distribution"] = [{"@type": "DataDownload", "name": "comments.csv", "encodingFormat": "text/csv",
                           "contentUrl": f"{SITE}/data/studies/{slug}/comments.csv"}]
    ld["isPartOf"] = {"@type": "WebSite", "name": "Common Signals", "url": f"{SITE}/"}
    body = json.dumps(ld, indent=2, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{body}\n</script>'


def study_hero(study):
    counts = study["counts"]
    lines = [f'    <h1 id="studyTitle">{esc(study["title"])}</h1>',
             f'    <p id="studyMeta" class="meta"><strong>{counts["coded"]:,}</strong> comments coded &middot; '
             f'<strong>{counts["clear_position_base"]:,}</strong> take a clear position &middot; {esc(study["platform"])}</p>']
    changelog = changelog_html(study.get("changelog"), study.get("version"))
    if changelog:
        lines.append(f"    {changelog}")
    return "\n".join(lines)


def article_link(study):
    if study.get("article_url"):
        return f'<a id="articleLink" href="{esc(study["article_url"])}">'
    return '<a id="articleLink" href="#" hidden>'


def dimension_html(dim):
    shared = ('<span class="shared-tag">Shared across the series</span>' if dim.get("shared")
              else '<span class="shared-tag not-shared">Specific to this study</span>')
    values = dim.get("values") or []
    if not values:
        body = '<p class="study-dim-note">Descriptive field: not a coded value with its own definitions.</p>'
    else:
        rows = []
        for v in values:
            example = f'<span class="example">e.g. "{esc(v["example"])}"</span>' if v.get("example") else ""
            rows.append(f'<div class="study-dim-value"><dt>{esc(v["label"])}</dt>'
                        f'<dd>{esc(v.get("definition") or "No definition recorded.")}{example}</dd></div>')
        body = f'<dl class="study-dim-values">{"".join(rows)}</dl>'
    return f'<article class="study-dim"><h3>{esc(dim_label(dim))} {shared}</h3>{body}</article>'


def codebook_body(slug, codebook):
    dims = "\n".join(f"      {dimension_html(d)}" for d in codebook.get("dimensions", []))
    return f"""    <section class="claim-block">
      <h2>Central claim</h2>
      <p class="claim" id="cbClaim">{esc(codebook["central_claim"])}</p>
      <h2>Stance note</h2>
      <p id="cbStanceNote">{esc(codebook["stance_note"])}</p>
    </section>

    <section id="cbDimensions">
{dims}
    </section>

    <p class="study-download"><a id="cbDownload" href="/data/studies/{esc(slug)}/codebook.md">Download this codebook as markdown</a></p>"""


def build_home(index):
    path = DATA / "index.html"
    original = path.read_text(encoding="utf-8")
    cards = "\n".join(study_card(s) for s in index["studies"])
    write_if_changed(path, replace_region(original, path, "cards", cards), original)


def build_study(slug):
    study = json.loads((STUDIES / slug / "study.json").read_text(encoding="utf-8"))
    codebook = json.loads((STUDIES / slug / "codebook.json").read_text(encoding="utf-8"))

    path = DATA / slug / "index.html"
    original = path.read_text(encoding="utf-8")
    page = replace_region(original, path, "jsonld", dataset_jsonld(study, original))
    page = replace_region(page, path, "hero", study_hero(study))
    if len(ARTICLE_LINK_RE.findall(page)) != 1:
        raise SystemExit(f"{path.relative_to(ROOT)} needs exactly one #articleLink")
    page = ARTICLE_LINK_RE.sub(lambda m: article_link(study), page)
    write_if_changed(path, page, original)

    path = DATA / slug / "codebook" / "index.html"
    original = path.read_text(encoding="utf-8")
    page = replace_region(original, path, "title", f'    <h1 id="cbTitle">Codebook: {esc(study["title"])}</h1>')
    page = replace_region(page, path, "codebook", codebook_body(slug, codebook))
    write_if_changed(path, page, original)


if __name__ == "__main__":
    index = json.loads((STUDIES / "index.json").read_text(encoding="utf-8"))
    build_home(index)
    for entry in index["studies"]:
        build_study(entry["slug"])
    print(f"{len(index['studies'])} studies rendered")

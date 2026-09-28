"""Build the glossary page's terms, structured data and count, plus glossary.json, from one source.

Run from the repo root: python3 scripts/build-glossary.py
Edit terms in data/glossary-terms.json, never in glossary.html. The script
replaces only the regions between the build-glossary:start/end markers in
glossary.html: the TERMS_RAW array, the DefinedTermSet JSON-LD block and the
term count. It also writes glossary.json at the root for the hover cards.
"""
import json
import re
from pathlib import Path

SITE = "https://commonsignals.org"
ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "glossary-terms.json"
PAGE = ROOT / "glossary.html"

SET_NAME = "Common Signals AI Safety Glossary"
SET_DESCRIPTION = "Plain-English definitions of the terms Common Signals uses across its research, tools and strategy."


def slug(s):
    # A direct port of slug() in glossary.html, so ids here match the page's anchors.
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and")))


def load():
    terms = json.loads(SOURCE.read_text(encoding="utf-8"))
    ids = [slug(t["term"]) for t in terms]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise SystemExit(f"Duplicate term ids: {', '.join(dupes)}")
    for t in terms:
        missing = [a for a in t["also"] if a not in ids]
        if missing:
            raise SystemExit(f"{t['term']}: 'also' points to unknown ids: {', '.join(missing)}")
    return terms


def dump(value):
    return json.dumps(value, ensure_ascii=False)


def terms_block(terms):
    rows = [dump([t["term"], t["aliases"], t["definition"], t["source"]["title"], t["source"]["org"],
                  t["source"]["href"], t["also"], t["contested"]]) for t in terms]
    return "  const TERMS_RAW = [\n" + ",\n".join(rows) + "\n];"


def jsonld_block(terms):
    items = [f'''  {{
    "@type": "DefinedTerm",
    "@id": {dump(f"{SITE}/glossary#{slug(t['term'])}")},
    "name": {dump(t["term"])},
    "description": {dump(t["definition"])}
  }}''' for t in terms]
    return f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "DefinedTermSet",
  "@id": "{SITE}/glossary",
  "name": {dump(SET_NAME)},
  "description": {dump(SET_DESCRIPTION)},
  "url": "{SITE}/glossary",
  "hasDefinedTerm": [
''' + ",\n".join(items) + '''
]
}
</script>'''


# Each region: (start marker, end marker). Markers inside the inline script are
# JavaScript comments; the JSON-LD markers sit outside its <script> because JSON
# can't hold comments.
REGIONS = {
    "jsonld": ("<!-- build-glossary:start jsonld -->\n", "\n<!-- build-glossary:end jsonld -->"),
    "terms": ("  // build-glossary:start terms\n", "\n  // build-glossary:end terms"),
    "count": ("<!-- build-glossary:start count -->", "<!-- build-glossary:end count -->"),
}


def replace_region(page, name, content):
    start, end = REGIONS[name]
    pattern = re.escape(start) + r".*?" + re.escape(end)
    if len(re.findall(pattern, page, flags=re.S)) != 1:
        raise SystemExit(f"glossary.html needs exactly one '{name}' region between build-glossary markers")
    return re.sub(pattern, lambda m: start + content + end, page, flags=re.S)


def write_page(terms):
    page = PAGE.read_text(encoding="utf-8")
    page = replace_region(page, "jsonld", jsonld_block(terms))
    page = replace_region(page, "terms", terms_block(terms))
    page = replace_region(page, "count", f"{len(terms)} terms")
    PAGE.write_text(page, encoding="utf-8")


def write_json(terms):
    rows = [{"id": slug(t["term"]), "term": t["term"], "definition": t["definition"]} for t in terms]
    (ROOT / "glossary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    terms = load()
    write_page(terms)
    write_json(terms)
    print(f"Built {len(terms)} glossary terms.")

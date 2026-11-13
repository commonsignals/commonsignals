"""Build an article's "Questions people ask" block from its draft.

Run from anywhere: python3 scripts/build-questions.py <article.md> <page.html>

Reads the "## Questions people ask" section of the draft (### questions, one
answer paragraph each) and writes three regions into the page, each between
build-questions:start/end markers:

  section  the <section id="questions-people-ask"> in the article body, placed
           before the first back-matter H2 (sources, citation, related research)
  toc      its entry in the contents list; the questions themselves get none
  jsonld   FAQPage structured data, straight after the Article JSON-LD, whose
           answers are the page's answers with links and markup removed

Running it again replaces the regions. Never edit them by hand. HTML comments in
the draft, including the <!-- Q SOURCE: ... --> notes, are dropped and never
reach the page; the script refuses to write a page that would contain one.
"""
import html
import json
import re
import sys
from pathlib import Path

HEADING = "Questions people ask"
SECTION_ID = "questions-people-ask"

# The H2 ids that start an article's back matter. The block goes before the first.
BACK_MATTER = ("sources-and-data", "data-and-citation", "data-and-contact", "sources", "method",
               "how-to-cite", "further-reading", "references", "related-research")

MARK = "build-questions:{} {}"


def slug(s, limit=80):
    # slug() from build-glossary.py, keeping apostrophes out ("OpenAI's" -> "openais") and cut at a word boundary.
    s = re.sub(r"['’]", "", s.lower().replace("&", "and"))
    s = re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", s))
    return s if len(s) <= limit else s[:limit].rsplit("-", 1)[0]


def parse(md):
    """Return [(question, answer_markdown)] from the draft's block."""
    lines = re.sub(r"<!--.*?-->", "", md, flags=re.S).splitlines()
    starts = [i for i, l in enumerate(lines) if re.fullmatch(r"##\s+" + HEADING + r"\s*", l.strip(), re.I)]
    if len(starts) != 1:
        raise SystemExit(f"Expected one '## {HEADING}' heading, found {len(starts)}.")
    items, q, buf = [], None, []
    for line in lines[starts[0] + 1:]:
        if re.match(r"#{1,2}\s", line):
            break
        m = re.match(r"###\s+(.*)", line)
        if m:
            if q:
                items.append((q, buf))
            q, buf = m.group(1).strip(), []
        elif q:
            buf.append(line)
    if q:
        items.append((q, buf))
    out = []
    for q, buf in items:
        paras = [p for p in re.split(r"\n\s*\n", "\n".join(buf).strip()) if p.strip()]
        if not paras:
            raise SystemExit(f"No answer under: {q}")
        # One paragraph is the rule (check-questions warns otherwise); extra ones are kept, not lost.
        out.append((q, [" ".join(p.split()) for p in paras]))
    if not out:
        raise SystemExit("The block has no ### questions.")
    return out


LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
EMPHASIS = [(re.compile(r"\*\*(.+?)\*\*"), "strong"), (re.compile(r"(?<![\w*])\*(?!\s)(.+?)\*(?!\w)"), "em"),
            (re.compile(r"(?<!\w)_(?!\s)(.+?)_(?!\w)"), "em"), (re.compile(r"`([^`]+)`"), "code")]


def to_html(text):
    out, pos = [], 0
    for m in LINK.finditer(text):
        out.append(inline(text[pos:m.start()]))
        href = m.group(2)
        ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        out.append(f'<a href="{html.escape(href)}"{ext}>{inline(m.group(1))}</a>')
        pos = m.end()
    out.append(inline(text[pos:]))
    return "".join(out)


def inline(text):
    text = html.escape(text, quote=False)
    for rx, tag in EMPHASIS:
        text = rx.sub(lambda m: f"<{tag}>{m.group(1)}</{tag}>", text)
    return text


def to_plain(text):
    text = LINK.sub(lambda m: m.group(1), text)
    for rx, _ in EMPHASIS:
        text = rx.sub(lambda m: m.group(1), text)
    return re.sub(r"<[^>]+>", "", text)


def section_block(items, taken):
    rows = []
    for q, paras in items:
        qid = slug(q)
        if qid in taken:
            raise SystemExit(f"Question id '{qid}' is already used on the page. Reword the question.")
        taken.add(qid)
        rows.append(f'        <h3 id="{qid}">{inline(q)}</h3>')
        rows += [f"        <p>{to_html(p)}</p>" for p in paras]
    return (f'      <section id="{SECTION_ID}" class="questions">\n'
            f"        <h2>{HEADING}</h2>\n" + "\n".join(rows) + "\n      </section>")


def jsonld_block(items):
    data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": to_plain(q),
         "acceptedAnswer": {"@type": "Answer", "text": " ".join(to_plain(p) for p in paras)}}
        for q, paras in items]}
    return '<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False, indent=2) + "\n</script>"


def region(name, indent=""):
    return f"{indent}<!-- {MARK.format('start', name)} -->\n", f"\n{indent}<!-- {MARK.format('end', name)} -->"


def put(page, name, content, anchor, indent=""):
    """Replace the region if it exists; otherwise insert it at anchor(page)."""
    start, end = region(name, indent)
    pattern = re.escape(start.lstrip()) + r".*?" + re.escape(end)
    found = re.findall(pattern, page, flags=re.S)
    if len(found) > 1:
        raise SystemExit(f"The page has more than one '{name}' region.")
    if found:
        return re.sub(pattern, lambda m: start.lstrip() + content + end, page, count=1, flags=re.S), "replaced"
    at, where = anchor(page)
    return page[:at] + start + content + end + "\n" + page[at:], where


def line_start(page, at):
    return page.rfind("\n", 0, at) + 1


def body_anchor(page):
    for bid in BACK_MATTER:
        m = re.search(rf'<h2 id="{bid}"', page)
        if m:
            return line_start(page, m.start()), f'before <h2 id="{bid}">'
    m = re.search(r"</article>", page)
    if not m:
        raise SystemExit("No <article> element found in the page.")
    return line_start(page, m.start()), "at the end of the article"


def toc_anchor(page):
    toc = re.search(r'<aside class="article-toc".*?</aside>', page, flags=re.S)
    if not toc:
        raise SystemExit("No contents list (aside.article-toc) found in the page.")
    for bid in BACK_MATTER:
        m = re.search(rf'<li><a href="#{bid}">', toc.group(0))
        if m:
            return line_start(page, toc.start() + m.start()), f"before #{bid}"
    m = re.search(r"</ul>", toc.group(0))
    return line_start(page, toc.start() + m.start()), "at the end"


def jsonld_anchor(page):
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>\n?', page, flags=re.S):
        if re.search(r'"@type":\s*"Article"', m.group(1)):
            return m.end(), "after the Article JSON-LD"
    raise SystemExit("No Article JSON-LD found in the page.")


def build(md_path, page_path):
    items = parse(Path(md_path).read_text(encoding="utf-8"))
    page = Path(page_path).read_text(encoding="utf-8")
    # Ids already on the page, minus the ones this script wrote last time.
    previous = re.search(r"<!-- build-questions:start section -->.*?build-questions:end section -->", page, re.S)
    taken = set(re.findall(r'id="([^"]+)"', page.replace(previous.group(0), "") if previous else page))
    taken.discard(SECTION_ID)
    page, w1 = put(page, "section", section_block(items, taken), body_anchor, "      ")
    toc_li = f'        <li><a href="#{SECTION_ID}">{HEADING}</a></li>'
    page, w2 = put(page, "toc", toc_li, toc_anchor, "        ")
    page, w3 = put(page, "jsonld", jsonld_block(items), jsonld_anchor)
    if "Q SOURCE" in page:
        raise SystemExit("Refusing to write: 'Q SOURCE' would appear in the page.")
    Path(page_path).write_text(page, encoding="utf-8")
    print(f"Built {len(items)} questions into {page_path}: section {w1}, contents entry {w2}, FAQPage {w3}.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__.split("\n\n")[1])
    build(sys.argv[1], sys.argv[2])

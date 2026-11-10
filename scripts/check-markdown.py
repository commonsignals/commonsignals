"""Check each page's markdown version against the page's HTML.

Run from anywhere after scripts/build-markdown.py: python3 scripts/check-markdown.py

Kept apart from the build on purpose: it finds the pages and reads their HTML
with its own code. For each page it checks that five sentences drawn at random
from the HTML main text (seed 20261026) appear in the markdown, that every
heading and every link in the main text appears there, and that every table has
the same rows and columns. Whitespace and markdown syntax are ignored when
comparing text. It lists misses and fixes nothing.

The main text leaves out what the markdown is meant to leave out: navigation and
the table of contents, footers, buttons, forms, scripts, hidden elements, SVG
internals (each chart becomes one Chart: line), click-to-load video facades, the
subscribe and contact bands, and the page's own View as markdown link.
"""
import random
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://commonsignals.org"
SEED = 20261026
HUBS = ["research.html", "updates.html", "data/index.html"]
NAMED = ["/methodology", "/theory-of-change", "/about", "/ai-safety-comms-reading-list"]
EXCLUDED = {"/research", "/updates", "/tools", "/contact"}

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SKIP_TAGS = {"nav", "footer", "button", "form", "input", "select", "textarea", "label", "fieldset", "legend",
             "script", "style", "template", "noscript", "svg", "iframe"}
SKIP_CLASSES = {"article-toc", "embed", "sr-only", "md-view", "ai-copy"}
SKIP_IDS = {"article-subscribe", "contact"}
BLOCKS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "figcaption", "summary", "blockquote",
          "dt", "dd", "caption", "div", "section", "article", "aside", "figure", "ul", "ol", "table", "tr"}


class Main(HTMLParser):
    """The text, headings, links, tables and charts of a page's <main>."""

    def __init__(self, base):
        super().__init__(convert_charrefs=True)
        self.base, self.stack, self.in_main, self.skip = base, [], False, None
        self.stream, self.headings, self.links, self.tables, self.charts = [], [], [], [], 0
        self.heading, self.figure_charted = None, True

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        classes = set(a.get("class", "").split())
        if tag == "main":
            self.in_main = True
        if tag not in VOID:
            self.stack.append((tag, classes))
        if not self.in_main or self.skip is not None:
            return
        # One chart per figure: an SVG drawn inline or loaded as a file, or an
        # image whose alt text calls it a chart. The mobile copy of a chart is
        # the same chart.
        if tag == "figure":
            self.figure_charted = False
        is_chart = (tag == "svg" and a.get("role") == "img"
                    and not any("chart-mobile" in c for _, c in self.stack)) or (
            tag == "img" and (urlsplit(a.get("src", "")).path.endswith(".svg")
                              or re.search(r"\bchart\b", a.get("alt", ""), re.I)))
        if is_chart and not self.figure_charted and any(t == "figure" for t, _ in self.stack):
            self.charts += 1
            self.figure_charted = True
        if (tag in SKIP_TAGS or "hidden" in a or a.get("aria-hidden") == "true" or a.get("id") in SKIP_IDS
                or classes & SKIP_CLASSES):
            if tag not in VOID:
                self.skip = len(self.stack)
            return
        if tag in BLOCKS:
            self.stream.append("\n")
        if re.fullmatch(r"h[1-6]", tag):
            self.heading = []
        if tag == "a" and a.get("href"):
            self.links.append(urljoin(self.base, a["href"]))
        if tag == "table":
            self.tables.append([])
        if tag == "tr" and self.tables:
            self.tables[-1].append(0)
        if tag in ("td", "th") and self.tables and self.tables[-1]:
            self.tables[-1][-1] += 1

    def handle_endtag(self, tag):
        if tag in VOID or not any(t == tag for t, _ in self.stack):
            return
        while self.stack:
            depth = len(self.stack)
            top, _ = self.stack.pop()
            if self.skip == depth:
                self.skip = None
            if top == tag:
                break
        if not self.in_main or self.skip is not None:
            return
        if tag == "main":
            self.in_main = False
        if tag in BLOCKS:
            self.stream.append("\n")
        if re.fullmatch(r"h[1-6]", tag) and self.heading is not None:
            self.headings.append(" ".join("".join(self.heading).split()))
            self.heading = None

    def handle_data(self, data):
        if self.in_main and self.skip is None:
            self.stream.append(data)
            if self.heading is not None:
                self.heading.append(data)

    def sentences(self):
        out = []
        for block in "".join(self.stream).split("\n"):
            block = " ".join(block.split())
            for s in re.split(r"(?<=[.!?])[\"')\]]?\s+(?=[\"'(\[]?[A-Z0-9])", block):
                if len(s.split()) >= 5 and re.search(r"[.!?][\"')\]]?$", s):
                    out.append(s)
        return out


def plain(markdown):
    """Markdown as text: no front matter, block markers, link syntax, emphasis or
    escapes. A heading keeps its own words, numbers included."""
    text = re.sub(r"\A---\n.*?\n---\n", "", markdown, flags=re.S)
    lines = []
    for line in text.split("\n"):
        heading = re.match(r"#{1,6} ", line)
        if heading:
            line = line[heading.end():]
        else:
            line = re.sub(r"^\s*(?:> ?)*", "", line)
            line = re.sub(r"^\s*(?:[-+] |\d+\. )", "", line)
        lines.append(line)
    text = "\n".join(lines)
    link = re.compile(r"!?\[((?:[^\[\]]|\[[^\]]*\])*)\]\((?:<[^>]*>|[^)\s]*)\)")
    while link.search(text):
        text = link.sub(r"\1", text)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|<>])", r"\1", text.replace("*", ""))
    return text.replace("|", " ")


def squeeze(text):
    return re.sub(r"\s+", "", text)


def page_list():
    paths = []
    for hub in HUBS:
        s = (ROOT / hub).read_text(encoding="utf-8")
        main = re.search(r"<main\b.*?</main>", s, re.S).group(0)
        main = re.sub(r'<section id="(?:article-subscribe|contact)".*?</section>', "", main, flags=re.S)
        for href in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', main):
            parts = urlsplit(urljoin(SITE + "/", href))
            path = parts.path or "/"
            if parts.netloc != "commonsignals.org" or path in paths:
                continue
            paths.append(path)
    paths += [p for p in NAMED if p not in paths]
    keep = []
    for p in paths:
        f = ROOT / (p.lstrip("/") + "index.html" if p.endswith("/") else p.lstrip("/") + ".html")
        if p in EXCLUDED or (p.startswith("/data/") and p != "/data/") or not f.is_file():
            continue
        keep.append((p, f))
    return keep


def md_tables(markdown):
    tables, rows = [], None
    for line in markdown.split("\n") + [""]:
        if line.startswith("|"):
            if rows is None:
                rows = []
            if not re.fullmatch(r"\|(?:\s*-+\s*\|)+", line):
                rows.append(len(re.split(r"(?<!\\)\|", line.strip())) - 2)
        elif rows is not None:
            tables.append((len(rows), max(rows)))
            rows = None
    return tables


def main():
    pages = page_list()
    region = re.search(r"# build-markdown:start\n(.*?)# build-markdown:end", (ROOT / "_headers").read_text(encoding="utf-8"), re.S)
    built = [line for line in region.group(1).split("\n") if line.endswith(".md")]
    on_disk = [p for p in built if (ROOT / p.lstrip("/")).is_file()]
    print(f"Pages on the list: {len(pages)}. Markdown files built: {len(on_disk)} of {len(built)} in _headers.")
    misses, rows = [], []
    for path, f in pages:
        md_path = path + "index.html.md" if path.endswith("/") else path + ".md"
        md_file = ROOT / md_path.lstrip("/")
        if not md_file.is_file():
            misses.append(f"{path}: no markdown file at {md_path}")
            continue
        source = f.read_text(encoding="utf-8")
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', source)
        page = Main(canon.group(1) if canon else SITE + path)
        page.feed(source)
        md = md_file.read_text(encoding="utf-8")
        text = squeeze(plain(md))
        heading_lines = [squeeze(plain(line)) for line in md.split("\n") if re.match(r"#{1,6} ", line)]

        pool = page.sentences()
        sample = random.Random(SEED).sample(pool, min(5, len(pool)))
        missed = [s for s in sample if squeeze(s) not in text]
        misses += [f"{path}: sentence not found: {s}" for s in missed]

        heads = [h for h in page.headings if h]
        missed_heads = [h for h in heads if not any(squeeze(h) in line for line in heading_lines)]
        misses += [f"{path}: heading not found: {h}" for h in missed_heads]

        links = list(dict.fromkeys(page.links))
        missed_links = [u for u in links if f"]({u})" not in md and f"](<{u}>)" not in md]
        misses += [f"{path}: link not found: {u}" for u in missed_links]

        html_tables = [(len(t), max(t)) for t in page.tables if t]
        tables_md = md_tables(md)
        if html_tables != tables_md:
            misses.append(f"{path}: tables differ: HTML {html_tables}, markdown {tables_md}")

        chart_lines = len(re.findall(r"^Chart: ", md, re.M))
        if page.charts != chart_lines:
            misses.append(f"{path}: {page.charts} charts in the HTML, {chart_lines} Chart: lines")

        rows.append((path, f"{len(sample) - len(missed)}/{len(sample)}", f"{len(heads) - len(missed_heads)}/{len(heads)}",
                     f"{len(links) - len(missed_links)}/{len(links)}",
                     f"{'same' if html_tables == tables_md else 'differ'} ({len(html_tables)})",
                     f"{chart_lines}/{page.charts}"))
    width = max(len(r[0]) for r in rows)
    print(f"\n{'page':<{width}}  sentences  headings  links    tables    charts")
    for r in rows:
        print(f"{r[0]:<{width}}  {r[1]:<9}  {r[2]:<8}  {r[3]:<7}  {r[4]:<8}  {r[5]}")
    print("\nMisses:" if misses else "\nNo misses.")
    for m in misses:
        print(f"  {m}")


if __name__ == "__main__":
    main()

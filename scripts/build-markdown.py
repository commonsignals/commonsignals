"""Build the markdown versions of the research pages, plus /llms.txt and /llms-full.txt.

Run from anywhere after changing a page it covers, a study.json or
data/studies/index.json: python3 scripts/build-markdown.py

The pages are everything linked from the main content of /research, /updates and
/data/, plus NAMED, minus EXCLUDED. Each page's markdown is converted from its own
HTML, the file Cloudflare Pages serves, never from the drafts in _incoming/: some
pages were corrected after their drafts were written. A page at /name gets
/name.md, and a page whose path ends in a slash gets index.html.md, as
llmstxt.org suggests.

The script writes, and only writes:
  - each page's markdown file;
  - a <link rel="alternate" type="text/markdown"> in each page's head;
  - a Copy for AI button and a View as markdown link in each page whose hero has
    a .hero-actions row;
  - /llms.txt, from data/studies/index.json and the page list, and /llms-full.txt,
    every markdown file llms.txt links to, in llms.txt order;
  - the build-markdown region of _headers, one entry per markdown file naming its
    HTML page as canonical. A pattern such as /:page.md could carry the page path,
    but it would also catch /README.md, which is served from the repo root too.

Running it twice changes nothing the second time.
"""
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

SITE = "https://commonsignals.org"
ROOT = Path(__file__).resolve().parent.parent
STUDIES = ROOT / "data" / "studies"
HEADERS = ROOT / "_headers"

HUBS = ["research.html", "updates.html", "data/index.html"]
NAMED = ["/methodology", "/theory-of-change", "/about", "/ai-safety-comms-reading-list"]
# Linked from the hubs but not research pages. The study explorer and codebook
# pages under /data/ are left out too: each study's folder under /data/studies/
# already publishes the same content as study.json, codebook.json and codebook.md.
EXCLUDED = {"/research", "/updates", "/tools", "/contact"}

# Where pages go in llms.txt. Study articles come from data/studies/index.json, and
# any other page on the list is an article.
METHODS = ["/methodology", "/data/"]
OPTIONAL = ["/ai-safety-comms-reading-list", "/theory-of-change", "/about", "/glossary", "/research/library/"]
DATA_README = "/data/studies/README.md"
DATA_LINE = "Each study folder under /data/studies/ holds comments.csv, codebook.json and study.json."

# Pages that state a licence in their own words, quoted exactly. The build stops if
# a quote disappears from its page. Pages can also state one in JSON-LD "license".
LICENCE_STATEMENTS = {"/data/": "The coding and compilation are CC BY 4.0; comment text remains its authors'."}

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
INLINE = {"a", "abbr", "b", "bdi", "bdo", "cite", "code", "data", "del", "dfn", "em", "i", "img", "ins", "kbd",
          "mark", "q", "s", "samp", "small", "span", "strong", "sub", "sup", "time", "u", "var", "wbr", "br"}
# Elements whose inline children run together as text. Inline children of any other
# block (a flex row of tags or links, say) are shown apart, so they get a separator.
TEXT_BLOCKS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th", "dt", "dd", "figcaption", "summary",
               "caption", "blockquote", "cite", "a"}
# Left out of the markdown: navigation, footers, buttons, forms and scripts, plus
# the table of contents, the subscribe and contact bands at the foot of main, the
# click-to-load video facades (each has a Watch link after it) and the page's own
# View as markdown link. Hidden elements go too.
SKIP_TAGS = {"nav", "footer", "button", "form", "input", "select", "textarea", "label", "fieldset", "legend",
             "option", "script", "style", "template", "noscript", "link", "meta", "canvas", "dialog", "svg"}
SKIP_CLASSES = {"article-toc", "embed", "sr-only", "md-view", "ai-copy"}
SKIP_IDS = {"article-subscribe", "contact"}


class Node:
    __slots__ = ("tag", "attrs", "kids", "parent")

    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.kids, self.parent = tag, attrs, [], parent

    def classes(self):
        return self.attrs.get("class", "").split()

    def find_all(self, test):
        for kid in self.kids:
            if isinstance(kid, Node):
                if test(kid):
                    yield kid
                yield from kid.find_all(test)

    def find(self, test):
        return next(self.find_all(test), None)

    def text(self):
        return "".join(k if isinstance(k, str) else k.text() for k in self.kids)


class Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = self.cur = Node("#root", {}, None)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: ("" if v is None else v) for k, v in attrs}, self.cur)
        self.cur.kids.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_endtag(self, tag):
        node = self.cur
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root:
            self.cur = node.parent

    def handle_data(self, data):
        self.cur.kids.append(data)


def parse(source):
    builder = Builder()
    builder.feed(source)
    builder.close()
    return builder.root


def skipped(node):
    a = node.attrs
    return (node.tag in SKIP_TAGS or "hidden" in a or a.get("aria-hidden") == "true"
            or a.get("id") in SKIP_IDS or bool(SKIP_CLASSES.intersection(node.classes())))


def squash(text):
    return re.sub(r"\s+", " ", text)


def dest(url):
    """A markdown link destination, in angle brackets when it holds spaces or brackets."""
    return f"<{url}>" if re.search(r"[\s()<>]", url) else url


def emphasise(marker, text):
    core = text.strip()
    if not core:
        return text
    lead, trail = text[:len(text) - len(text.lstrip())], text[len(text.rstrip()):]
    return f"{lead}{marker}{core}{marker}{trail}"


def escape_text(text, line_starts=True):
    """Escape what markdown would read as markup: a tag-like '<' anywhere, and a
    block marker at the start of a line."""
    text = re.sub(r"<(?=[A-Za-z/!?])", r"\\<", text)
    return re.sub(r"^(\s*)([#>+*-]|\d+[.)])(?=\s)", r"\1\\\2", text, flags=re.M) if line_starts else text


def indent(text, pad, first=True):
    lines = text.split("\n")
    out = [(pad + line if line and (first or i) else line) for i, line in enumerate(lines)]
    return "\n".join(out)


def glossary_terms(source):
    """The glossary's term list, which the page draws with JavaScript from the
    TERMS_RAW array in its own HTML. This follows that renderer: terms sorted and
    grouped by letter, each with its tags, definition, source and see-also links."""
    m = re.search(r"// build-glossary:start terms\n\s*const TERMS_RAW = (\[.*?\]);\n\s*// build-glossary:end terms",
                  source, re.S)
    if not m:
        raise SystemExit("glossary.html: no TERMS_RAW array between the build-glossary terms markers")
    slug = lambda s: re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and")))
    terms = [dict(term=t[0], aliases=t[1], definition=t[2], src_title=t[3], src_org=t[4], href=t[5],
                  also=t[6] or [], contested=bool(t[7]), id=slug(t[0])) for t in json.loads(m.group(1))]
    terms.sort(key=lambda t: t["term"].casefold())
    by_id = {t["id"]: t for t in terms}
    blocks, letter = [], None
    for t in terms:
        if t["term"][0].upper() != letter:
            letter = t["term"][0].upper()
            blocks.append(f"## {letter}")
        blocks.append(f"### [{t['term']}]({SITE}/glossary#{t['id']})")
        tags = (["Contested"] if t["contested"] else []) + t["aliases"]
        if tags:
            blocks.append(" · ".join(tags))
        blocks.append(escape_text(t["definition"]))
        org = f" ({t['src_org']})" if t["src_org"] else ""
        blocks.append(f"Read more: [{t['src_title']}]({dest(t['href'])}){org}")
        also = [f"[{re.sub(r' *[(].*[)]$', '', by_id[i]['term'])}]({SITE}/glossary#{i})" for i in t["also"] if i in by_id]
        if also:
            blocks.append("See also " + ", ".join(also))
    return blocks


class Converter:
    """Markdown for one page's main content."""

    def __init__(self, page_url, source):
        self.base, self.source = page_url, source

    def url(self, href):
        return urljoin(self.base, href)

    # Inline content

    def inline(self, kids, parent=None):
        parts, prev = [], None
        flex = parent is not None and parent.tag not in TEXT_BLOCKS and parent.tag not in INLINE
        for kid in kids:
            if isinstance(kid, str):
                parts.append(squash(kid))
                prev = None
                continue
            out = self.inline_node(kid)
            if not out.strip():
                parts.append(out)
                continue
            if flex and prev is not None:
                parts.append(": " if "k" in prev.classes() and "v" in kid.classes() else " · ")
            parts.append(out)
            prev = kid
        return "".join(parts)

    def inline_node(self, node):
        if skipped(node):
            return ""
        tag = node.tag
        if tag == "a":
            text = self.inline(node.kids, node).strip()
            text = text or node.attrs.get("aria-label", "")
            href = node.attrs.get("href")
            return f"[{text}]({dest(self.url(href))})" if text and href else text
        if tag in ("strong", "b"):
            return emphasise("**", self.inline(node.kids, node))
        if tag in ("em", "i"):
            return emphasise("*", self.inline(node.kids, node))
        if tag == "code":
            return f"`{node.text()}`"
        if tag == "img":
            return f"![{node.attrs.get('alt', '')}]({dest(self.url(node.attrs.get('src', '')))})"
        if tag == "br":
            return " "
        text = self.inline(node.kids, node)
        # A separator span that CSS spaces out, as in the study cards' file links.
        return " · " if text.strip() == "·" else text

    def text_of(self, node, line_starts=True):
        return escape_text(squash(self.inline(node.kids, node)).strip(), line_starts)

    # Blocks

    def blocks(self, node, kids=None):
        kids = node.kids if kids is None else kids
        if {"article-hero", "page-hero"} & set(node.classes()):
            kids = [k for k in kids if isinstance(k, Node) and k.tag == "h1"] + \
                   [k for k in kids if not (isinstance(k, Node) and k.tag == "h1")]
        out, run = [], []

        def flush():
            text = escape_text(squash(self.inline(run, node)).strip())
            if text:
                out.append(text)
            run.clear()

        for kid in kids:
            if isinstance(kid, str) or (kid.tag in INLINE and not (kid.tag == "cite" and node.tag == "blockquote")):
                run.append(kid)
                continue
            flush()
            if kid.tag == "cite":
                cite = self.text_of(kid)
                if cite:
                    out.append(emphasise("*", cite))
                continue
            out.extend(self.block(kid))
        flush()
        return out

    def block(self, node):
        if skipped(node):
            return []
        tag, cls = node.tag, set(node.classes())
        if node.attrs.get("id") == "glossaryList":
            return self.blocks(node) or glossary_terms(self.source)
        if re.fullmatch(r"h[1-6]", tag):
            text = self.text_of(node, line_starts=False)
            return [f"{'#' * int(tag[1])} {text}"] if text else []
        if tag == "p":
            text = self.text_of(node)
            return [text] if text else []
        if tag == "ul" and "ask-list" in cls:
            return self.ask_list(node)
        if tag in ("ul", "ol"):
            return self.list_block(node)
        if tag == "blockquote" and "instagram-media" not in cls:
            body = "\n\n".join(self.blocks(node))
            return ["\n".join(f"> {line}" if line else ">" for line in body.split("\n"))] if body else []
        if tag == "table":
            return [self.table(node)]
        if tag == "figure":
            return self.figure(node)
        if tag == "details":
            summary = node.find(lambda n: n.tag == "summary")
            rest = [k for k in node.kids if k is not summary]
            head = [emphasise("**", self.text_of(summary))] if summary else []
            return head + self.blocks(node, rest)
        if tag == "summary":
            return [emphasise("**", self.text_of(node))]
        if tag == "aside" and "stat-pull" in cls:
            part = lambda c: node.find(lambda n: c in n.classes())
            figure, text, source = part("stat-pull-figure"), part("stat-pull-text"), part("stat-pull-source")
            lead = " ".join(x for x in (emphasise("**", self.text_of(figure)) if figure else "",
                                        self.text_of(text) if text else "") if x)
            return [x for x in (lead, self.text_of(source) if source else "") if x]
        if tag == "iframe":
            src, title = node.attrs.get("src"), node.attrs.get("title", "")
            return [f"[{title or src}]({dest(self.url(src))})"] if src else []
        if tag == "img":
            return [self.inline_node(node)]
        if tag == "hr":
            return ["* * *"]
        return self.blocks(node)

    def list_block(self, node):
        ordered = node.tag == "ol"
        start = int(node.attrs.get("start") or 1)
        items = []
        for li in (k for k in node.kids if isinstance(k, Node) and k.tag == "li" and not skipped(k)):
            content = self.blocks(li)
            if not content:
                continue
            marker = f"{start + len(items)}." if ordered else "-"
            pad = " " * (len(marker) + 1)
            first, *rest = content
            item = f"{marker} {indent(first, pad, first=False)}"
            for b in rest:
                item += "\n\n" + indent(b, pad)
            items.append(item)
        loose = any("\n\n" in item for item in items)
        return ["\n\n".join(items) if loose else "\n".join(items)] if items else []

    def ask_list(self, node):
        """A numbered list of recommendations: a number badge, then a heading and
        its paragraphs. Each becomes a numbered heading."""
        out = []
        for li in (k for k in node.kids if isinstance(k, Node) and k.tag == "li"):
            badge = li.find(lambda n: "n" in n.classes())
            heading = li.find(lambda n: re.fullmatch(r"h[1-6]", n.tag) is not None)
            if not heading:
                out.extend(self.blocks(li))
                continue
            number = f"{squash(badge.text()).strip()}. " if badge else ""
            out.append(f"{'#' * int(heading.tag[1])} {number}{self.text_of(heading, line_starts=False)}")
            out.extend(self.blocks(heading.parent, [k for k in heading.parent.kids if k is not heading]))
        return out

    def table(self, node):
        rows = []
        for tr in node.find_all(lambda n: n.tag == "tr"):
            cells = [k for k in tr.kids if isinstance(k, Node) and k.tag in ("td", "th")]
            rows.append([" <br> ".join(self.blocks(c)).replace("|", "\\|") for c in cells])
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        line = lambda cells: "| " + " | ".join(cells) + " |"
        return "\n".join([line(rows[0]), line(["---"] * width)] + [line(r) for r in rows[1:]])

    def figure(self, node):
        caption = node.find(lambda n: n.tag == "figcaption")
        in_caption = lambda n: any(p is caption for p in ancestors(n))
        visual = node.find(lambda n: (n.tag == "svg" and n.attrs.get("role") == "img"
                                      and not any("chart-mobile" in p.classes() for p in ancestors(n)))
                           or (n.tag == "img" and not in_caption(n)))
        out = []
        if visual is not None:
            wrap = next((p for p in ancestors(visual) if p.tag == "a" and p.attrs.get("href")), None)
            links = [a for a in node.find_all(lambda n: n.tag == "a" and n.attrs.get("href"))
                     if a is not wrap and not in_caption(a)]
            src, alt = visual.attrs.get("src", ""), visual.attrs.get("alt", "")
            # A chart is an SVG, inline or as a file, or an image whose alt text
            # calls it one. Screenshots of web pages stay as images.
            if visual.tag == "svg" or urlsplit(src).path.endswith(".svg") or re.search(r"\bchart\b", alt, re.I):
                text = self.chart_text(visual)
                if wrap is not None:
                    text = f"[{text}]({dest(self.url(wrap.attrs['href']))})"
                extra = " ".join(f"[{self.text_of(a)}]({dest(self.url(a.attrs['href']))})" for a in links)
                out.append(escape_text(f"Chart: {text}" + (f" {extra}" if extra else "")))
            else:
                image = self.inline_node(visual)
                out.append(f"[{image}]({dest(self.url(wrap.attrs['href']))})" if wrap is not None else image)
        if caption is not None:
            out.extend(self.blocks(caption))
        return out

    def chart_text(self, visual):
        """A chart's title, then its text alternative: the desc of an inline SVG, or
        the alt of an image. An image's title comes from the SVG file: its <title>,
        or the title in the JSON chart spec that the house charts keep in <desc>."""
        title = ""
        if visual.tag == "svg":
            t = visual.find(lambda n: n.tag == "title")
            d = visual.find(lambda n: n.tag == "desc")
            title, text = (squash(t.text()).strip() if t else ""), (squash(d.text()).strip() if d else "")
        else:
            text = squash(visual.attrs.get("alt", "")).strip()
            parts = urlsplit(self.url(visual.attrs.get("src", "")))
            path = ROOT / parts.path.lstrip("/")
            if parts.netloc == urlsplit(SITE).netloc and path.suffix == ".svg" and path.is_file():
                svg = path.read_text(encoding="utf-8")
                t = re.search(r"<title[^>]*>(.*?)</title>", svg, re.S)
                d = re.search(r"<desc[^>]*>(.*?)</desc>", svg, re.S)
                if t:
                    title = squash(html.unescape(t.group(1))).strip()
                elif d:
                    try:
                        spec = json.loads(html.unescape(d.group(1)))
                        title = spec.get("title", "") if isinstance(spec, dict) else ""
                    except ValueError:
                        pass
        if title and text and not text.startswith(title):
            text = f"{title}{'' if title[-1] in '.?!:' else '.'} {text}"
        text = text or title
        return text + ("" if not text or text[-1] in ".?!" else ".")


def ancestors(node):
    node = node.parent
    while node is not None:
        yield node
        node = node.parent


# The page list

def site_path(href, base=SITE + "/"):
    parts = urlsplit(urljoin(base, href))
    if parts.scheme not in ("http", "https") or parts.netloc != urlsplit(SITE).netloc:
        return None
    return parts.path or "/"


def page_file(path):
    if path.endswith("/"):
        f = ROOT / path.lstrip("/") / "index.html"
    elif "." in path.rsplit("/", 1)[-1]:
        return None
    else:
        f = ROOT / (path.lstrip("/") + ".html")
    return f if f.is_file() else None


def main_of(doc):
    main = doc.find(lambda n: n.tag == "main")
    if main is None:
        raise SystemExit("a page has no <main>")
    return main


def page_paths():
    paths = []
    for hub in HUBS:
        doc = parse((ROOT / hub).read_text(encoding="utf-8"))
        canon = doc.find(lambda n: n.tag == "link" and n.attrs.get("rel") == "canonical")
        base = canon.attrs["href"] if canon else SITE + "/"
        for a in main_of(doc).find_all(lambda n: n.tag == "a" and n.attrs.get("href")):
            if any(skipped(p) for p in ancestors(a)):
                continue
            path = site_path(a.attrs["href"], base)
            if path and path not in paths:
                paths.append(path)
    paths += [p for p in NAMED if p not in paths]
    return [p for p in paths if p not in EXCLUDED and not (p.startswith("/data/") and p != "/data/") and page_file(p)]


def json_ld(doc):
    out = {}
    for s in doc.find_all(lambda n: n.tag == "script" and n.attrs.get("type") == "application/ld+json"):
        try:
            data = json.loads(s.text())
        except ValueError:
            continue
        for key, value in (data.items() if isinstance(data, dict) else []):
            out.setdefault(key, value)
    return out


def citation(main):
    """The page's own 'Cite as:' wording, or the paragraph after 'cite it as:'."""
    blocks = [squash(n.text()).strip() for n in main.find_all(lambda n: n.tag in ("p", "li"))
              if not any(skipped(p) for p in [n, *ancestors(n)])]
    for i, text in enumerate(blocks):
        m = re.search(r"\bcite (?:it )?as:\s*(.*)$", text, re.I)
        if m:
            return m.group(1) or (blocks[i + 1] if i + 1 < len(blocks) else "")
    return ""


def yaml_value(value):
    if re.fullmatch(r"\d{4}-\d{2}(-\d{2})?", value):
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_page(path):
    f = page_file(path)
    source = f.read_text(encoding="utf-8")
    doc = parse(source)
    canon = doc.find(lambda n: n.tag == "link" and n.attrs.get("rel") == "canonical")
    if canon is None:
        raise SystemExit(f"{f.relative_to(ROOT)} has no canonical link")
    url = canon.attrs["href"]
    title = squash(doc.find(lambda n: n.tag == "title").text()).strip()
    title = re.sub(r": Common Signals$", "", title)
    desc = doc.find(lambda n: n.tag == "meta" and n.attrs.get("name") == "description")
    main = main_of(doc)
    ld = json_ld(doc)
    md_path = path + "index.html.md" if path.endswith("/") else path + ".md"

    licence = ld.get("license", "")
    if path in LICENCE_STATEMENTS:
        if LICENCE_STATEMENTS[path] not in squash(main.text()):
            raise SystemExit(f"{f.relative_to(ROOT)} no longer says: {LICENCE_STATEMENTS[path]}")
        licence = LICENCE_STATEMENTS[path]
    meta = [("title", title), ("url", url), ("published", ld.get("datePublished", "")),
            ("updated", ld.get("dateModified", "")), ("publisher", "Common Signals"),
            ("licence", licence), ("cite", citation(main))]
    front = "\n".join(f"{k}: {yaml_value(v)}" for k, v in meta if v)
    body = "\n\n".join(Converter(url, source).blocks(main))
    body = re.sub(r"\n{3,}", "\n\n", body)
    return dict(path=path, file=f, source=source, url=url, title=title, md_path=md_path,
                md_url=SITE + md_path, md_file=ROOT / md_path.lstrip("/"),
                description=desc.attrs.get("content", "") if desc else "",
                published=ld.get("datePublished", ""), licence=licence,
                markdown=f"---\n{front}\n---\n\n{body}\n")


# Page edits: the head link and the hero controls

CANONICAL_RE = re.compile(r'<link rel="canonical" href="[^"]*" />\n')
ALTERNATE_RE = re.compile(r'<link rel="alternate" type="text/markdown"[^>]*>\n')
ACTIONS_RE = re.compile(r'(<div class="hero-actions">)(.*?)(\n([ \t]*)</div>)', re.S)
CONTROLS_RE = re.compile(r'\n[ \t]*<button type="button" class="ai-copy".*?</button>'
                         r'|\n[ \t]*<a class="hero-data-link md-view"[^>]*>.*?</a>', re.S)
CONTROLS = """
{i}<button type="button" class="ai-copy" data-md="{md}">
{i}  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
{i}    <rect x="9" y="9" width="11" height="11" rx="2"/>
{i}    <path d="M15 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h3"/>
{i}  </svg>
{i}  <span class="ai-copy-label" aria-live="polite">Copy for AI</span>
{i}</button>
{i}<a class="hero-data-link md-view" href="{md}">View as markdown</a>"""


def edit_page(page):
    source, name = page["source"], page["file"].relative_to(ROOT)
    head_link = f'<link rel="alternate" type="text/markdown" href="{page["md_url"]}" />\n'
    edited = ALTERNATE_RE.sub("", source)
    edited, n = CANONICAL_RE.subn(lambda m: m.group(0) + head_link, edited, count=1)
    if n != 1:
        raise SystemExit(f"{name}: no canonical link to put the markdown link after")
    m = ACTIONS_RE.search(edited)
    if m:
        if "<div" in m.group(2):
            raise SystemExit(f"{name}: .hero-actions holds a nested div, so its end can't be found safely")
        inner = CONTROLS_RE.sub("", m.group(2)) + CONTROLS.format(i=m.group(4) + "  ", md=page["md_path"])
        edited = edited[:m.start()] + m.group(1) + inner + m.group(3) + edited[m.end():]
    return edited, bool(m)


# llms.txt, llms-full.txt and _headers

def llms_txt(pages):
    by_path = {p["path"]: p for p in pages}
    home = parse((ROOT / "index.html").read_text(encoding="utf-8"))
    home_desc = home.find(lambda n: n.tag == "meta" and n.attrs.get("name") == "description").attrs["content"]
    lines = ["# Common Signals", "", f"> {home_desc}", "",
             f"The coded data lives at [/data/]({SITE}/data/). {LICENCE_STATEMENTS['/data/']}", "",
             "## Studies", ""]
    linked, study_pages, no_article = [], set(), []
    for entry in json.loads((STUDIES / "index.json").read_text(encoding="utf-8"))["studies"]:
        study = json.loads((STUDIES / entry["slug"] / "study.json").read_text(encoding="utf-8"))
        page = by_path.get(site_path(study.get("article_url") or "") or "")
        if page:
            study_pages.add(page["path"])
            linked.append(page)
            url = page["md_url"]
        else:
            no_article.append(entry["slug"])
            url = f"{SITE}/data/{entry['slug']}/"
        lines.append(f"- [{entry['title']}]({url}): Central claim: {study['central_claim']}")
    placed = study_pages | set(METHODS) | set(OPTIONAL)
    articles = sorted((p for p in pages if p["path"] not in placed), key=lambda p: (p["published"], p["title"]),
                      reverse=True)
    item = lambda p: f"- [{p['title']}]({p['md_url']}): {p['description']}"
    lines += ["", "## Articles", ""] + [item(p) for p in articles]
    methods = [by_path[p] for p in METHODS if p in by_path]
    readme = ROOT / DATA_README.lstrip("/")
    readme_title = re.match(r"# (.+)", readme.read_text(encoding="utf-8")).group(1)
    lines += ["", "## Methods and data", ""] + [item(p) for p in methods]
    lines.append(f"- [{readme_title}]({SITE}{DATA_README}): {DATA_LINE}")
    optional = [by_path[p] for p in OPTIONAL if p in by_path]
    lines += ["", "## Optional", ""] + [item(p) for p in optional]
    linked += articles + methods + [None] + optional
    return "\n".join(lines) + "\n", linked, no_article


def llms_full(linked):
    parts, seen = [], set()
    for page in linked:
        key = page["path"] if page else DATA_README
        if key in seen:
            continue
        seen.add(key)
        if page:
            parts.append(f"URL: {page['url']}\n\n{page['markdown']}")
        else:
            parts.append(f"URL: {SITE}{DATA_README}\n\n{(ROOT / DATA_README.lstrip('/')).read_text(encoding='utf-8')}")
    return "\n".join(parts)


HEADERS_START, HEADERS_END = "# build-markdown:start", "# build-markdown:end"
HEADERS_INTRO = """# Response headers for Cloudflare Pages.
# Everything between the build-markdown markers is written by scripts/build-markdown.py:
# never edit it by hand. Add any other rules outside the markers.
"""


def headers(pages, existing):
    rules = [f"{p['md_path']}\n  Content-Type: text/markdown; charset=utf-8\n  Link: <{p['url']}>; rel=\"canonical\""
             for p in sorted(pages, key=lambda p: p["md_path"])]
    rules += [f"{path}\n  Content-Type: text/plain; charset=utf-8" for path in ("/llms.txt", "/llms-full.txt")]
    region = HEADERS_START + "\n" + "\n\n".join(rules) + "\n" + HEADERS_END
    if not existing:
        return HEADERS_INTRO + "\n" + region + "\n"
    pattern = re.escape(HEADERS_START) + r".*?" + re.escape(HEADERS_END)
    if len(re.findall(pattern, existing, re.S)) != 1:
        raise SystemExit("_headers needs exactly one build-markdown region")
    return re.sub(pattern, lambda m: region, existing, flags=re.S)


def write_if_changed(path, text):
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    pages = [build_page(path) for path in page_paths()]
    with_controls = []
    for page in pages:
        edited, has_controls = edit_page(page)
        write_if_changed(page["file"], edited)
        if has_controls:
            with_controls.append(page["path"])
        write_if_changed(page["md_file"], page["markdown"])
    text, linked, no_article = llms_txt(pages)
    write_if_changed(ROOT / "llms.txt", text)
    write_if_changed(ROOT / "llms-full.txt", llms_full(linked))
    write_if_changed(HEADERS, headers(pages, HEADERS.read_text(encoding="utf-8") if HEADERS.exists() else ""))
    print(f"{len(pages)} pages converted; Copy for AI on {len(with_controls)}")
    for page in pages:
        if not page["licence"]:
            print(f"  no licence stated: {page['path']}")
    for slug in no_article:
        print(f"  study with no article, linked to its explorer page in llms.txt: {slug}")

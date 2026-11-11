"""Build PDF versions of the toolkit and the research agenda.

Run from anywhere after changing either page, and after the change is live:
    python3 scripts/build-pdfs.py

For each page in PAGES the script prints a copy of the page to
assets/pdf/<name>-<version>.pdf with headless Chrome. The copy has its scripts
removed, a print stylesheet that hides the navigation, contents, sign-up boxes
and footer, and a colophon under the dek holding the page's own citation line
and licence. It carries <base href> set to the live URL, so every link in the
PDF points at commonsignals.org and the stylesheet, fonts and charts load from
the live site: build after the page's assets are deployed.

The version in the file name comes from the citation line: "version 0.2" gives
-v0.2, "version of 11 November 2026" gives -2026-11-11. The script then points
the page's <a class="hero-data-link pdf-download"> link at the new file and
names its version in the label. Older PDFs are kept, so links to them still
work. Run scripts/build-markdown.py afterwards so the markdown carries the link.

Chrome is found at its usual macOS path, or set CHROME to its binary.
"""
import datetime
import html
import os
import re
import subprocess
import tempfile
from pathlib import Path

SITE = "https://commonsignals.org"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "pdf"
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
PAGES = {
    "research/agenda.html": "common-signals-research-agenda",
    "how-to-communicate-about-ai-safety.html": "how-to-communicate-about-ai-safety",
}
LICENCE = "Published under CC BY 4.0 (comment text quoted remains its original authors')."
CSS = """<style>
@page { size: A4; margin: 16mm 15mm 18mm; }
header.site, footer.site, .article-toc, .hero-actions, #article-subscribe, #contact, .site-search, .nav-drawer,
iframe.subscribe-target-frame { display: none !important; }
.reveal { opacity: 1 !important; transform: none !important; }
html, body { background: #fff !important; }
.article-shell { display: block !important; padding-top: 0 !important; }
.article-body { max-width: none !important; }
.article-hero { padding-top: 0 !important; padding-bottom: 6mm !important; }
.table-wrap { overflow: visible !important; margin-left: 0 !important; margin-right: 0 !important; }
.table-wrap table { width: 100% !important; font-size: 10pt !important; }
.article-body th { white-space: normal !important; }
tr, img, picture, figure, .article-box, li { break-inside: avoid; }
h2, h3 { break-after: avoid; }
.pdf-colophon { font-size: 9pt; color: #555; margin: 0 0 4mm; }
</style>"""


def citation(source):
    """The page's own citation line, without its 'Cite as:' prefix or markup."""
    for p in re.findall(r"<p>(.*?)</p>", source, re.S):
        text = html.unescape(re.sub(r"<[^>]+>", "", p)).strip()
        text = re.sub(r"^Cite as:\s*", "", text)
        if text.startswith("Ben Matthews, Common Signals,") and "version" in text:
            return text
    raise SystemExit("no citation line with a version found")


def version_tag(cite):
    """The file-name tag and the link label's wording for the citation's version."""
    m = re.search(r"version (\d+(?:\.\d+)+)", cite)
    if m:
        return "v" + m.group(1), "version " + m.group(1)
    m = re.search(r"version of (\d{1,2} \w+ \d{4})", cite)
    if m:
        return datetime.datetime.strptime(m.group(1), "%d %B %Y").date().isoformat(), "version of " + m.group(1)
    raise SystemExit(f"no version in: {cite}")


def print_copy(source, url, cite):
    s = re.sub(r"<script(?![^>]*application/ld\+json)[^>]*>.*?</script>", "", source, flags=re.S)
    s = s.replace("<head>", f'<head>\n<base href="{url}">', 1).replace("</head>", CSS + "\n</head>", 1)
    m = re.search(r'<div class="article-hero">.*?<p class="article-dek">.*?</p>', s, re.S)
    if not m:
        raise SystemExit("no article hero with a dek")
    colophon = f'\n    <p class="pdf-colophon">Cite as: {html.escape(cite, quote=False)} {LICENCE}</p>'
    return s[:m.end()] + colophon + s[m.end():]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for page, name in PAGES.items():
        f = ROOT / page
        source = f.read_text(encoding="utf-8")
        url = re.search(r'<link rel="canonical" href="([^"]+)"', source).group(1)
        cite = citation(source)
        tag, wording = version_tag(cite)
        pdf = OUT / f"{name}-{tag}.pdf"
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "page.html"
            copy.write_text(print_copy(source, url, cite), encoding="utf-8")
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                            f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer", "--virtual-time-budget=20000",
                            f"--print-to-pdf={pdf}", copy.as_uri()],
                           check=True, capture_output=True)
        href = "/" + pdf.relative_to(ROOT).as_posix()
        label = f"Download PDF ({wording})"
        edited, n = re.subn(r'<a class="hero-data-link pdf-download" href="[^"]*">[^<]*</a>',
                            f'<a class="hero-data-link pdf-download" href="{href}">{label}</a>', source)
        if n != 1:
            raise SystemExit(f"{page}: expected one pdf-download link in the hero, found {n}")
        if edited != source:
            f.write_text(edited, encoding="utf-8")
        print(f"{page} -> {href} ({pdf.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

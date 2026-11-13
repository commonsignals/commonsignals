"""Copy the shared site header and footer into every page.

Run from the repo root after editing scripts/header.inc or scripts/footer.inc:

    python3 scripts/build-partials.py           # rewrite every page's header and footer
    python3 scripts/build-partials.py --check   # list pages that are out of date; exit 1 if any

Each page keeps a full copy of the header and footer, so they work without JavaScript and
search engines and AI assistants can read their links. This script only replaces the
regions from <header class="site"> to </header> and from <footer class="site"> to
</footer>; the rest of the page is untouched. Never edit those regions in a page by hand:
the next run will overwrite them.

The partials end in .inc, not .html, because Cloudflare Pages serves every .html file in
the repo as a public page.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOT_PAGES = ("scripts/", "_incoming/", "_review/")

# (name, partial, region, {page: [(old, new), ...]} for pages that differ on purpose)
PARTS = [
    ("header", "scripts/header.inc", re.compile(r'<header class="site">.*?</header>', re.S), {}),
    ("footer", "scripts/footer.inc", re.compile(r'<footer class="site">.*?</footer>', re.S), {
        # The comment analyser's newsletter form uses its own ids.
        "tools/comment-analyser/index.html": [
            ('<form id="subscribeForm" class="subscribe-box"', '<form class="subscribe-box"'),
            ('subscribeEmail', 'toolSubscribeEmail'),
            ('subscribeWebsite', 'toolSubscribeWebsite'),
            ('<p class="subscribe-status" id="subscribeStatus"', '<p class="subscribe-status"'),
        ],
    }),
]


def pages():
    """Tracked .html files plus new ones not yet committed."""
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.split()
    files = set(git("ls-files", "*.html")) | set(git("ls-files", "--others", "--exclude-standard", "*.html"))
    return sorted(f for f in files if not f.startswith(NOT_PAGES) and (ROOT / f).exists())


def render(name, page, partial, variants):
    out = partial
    for old, new in variants.get(page, []):
        if old not in out:
            sys.exit(f"build-partials: {name} variant for {page} no longer matches its partial: {old!r}")
        out = out.replace(old, new)
    return out


def main():
    check = "--check" in sys.argv[1:]
    parts = [(n, (ROOT / p).read_text(encoding="utf-8").rstrip("\n"), rx, v) for n, p, rx, v in PARTS]
    changed, skipped = [], []
    for page in pages():
        path = ROOT / page
        s = new = path.read_text(encoding="utf-8")
        for name, partial, rx, variants in parts:
            n = len(rx.findall(new))
            if n != 1:
                skipped.append(f"{page} ({n} {name}s)")
                continue
            new = rx.sub(lambda m: render(name, page, partial, variants), new)
        if new != s:
            changed.append(page)
            if not check:
                path.write_text(new, encoding="utf-8")
    for m in skipped:
        print(f"skipped, no single site region: {m}")
    verb = "out of date" if check else "updated"
    print(f"{len(changed)} page(s) {verb}" + (": " + ", ".join(changed) if changed else ""))
    if check and changed:
        sys.exit(1)


if __name__ == "__main__":
    main()

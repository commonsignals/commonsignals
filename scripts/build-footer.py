"""Copy the shared site footer from scripts/footer.inc into every page.

Run from the repo root after editing scripts/footer.inc:

    python3 scripts/build-footer.py           # rewrite every page's footer
    python3 scripts/build-footer.py --check   # list pages whose footer is out of date; exit 1 if any

Each page keeps a full copy of the footer, so it works without JavaScript and search
engines and AI assistants can read its links. This script only replaces the region from
<footer class="site"> to </footer>; the rest of the page is untouched. Never edit that
region in a page by hand: the next run will overwrite it.

The partial ends in .inc, not .html, because Cloudflare Pages serves every .html file in
the repo as a public page.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTIAL = ROOT / "scripts" / "footer.inc"
NOT_PAGES = ("scripts/", "_incoming/", "_review/")
FOOTER = re.compile(r'<footer class="site">.*?</footer>', re.S)

# Pages whose footer differs on purpose: (old, new) replacements applied to the partial.
VARIANTS = {
    # The comment analyser's newsletter form uses its own ids.
    "tools/comment-analyser/index.html": [
        ('<form id="subscribeForm" class="subscribe-box"', '<form class="subscribe-box"'),
        ('subscribeEmail', 'toolSubscribeEmail'),
        ('subscribeWebsite', 'toolSubscribeWebsite'),
        ('<p class="subscribe-status" id="subscribeStatus"', '<p class="subscribe-status"'),
    ],
}


def pages():
    """Tracked .html files plus new ones not yet committed."""
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.split()
    files = set(git("ls-files", "*.html")) | set(git("ls-files", "--others", "--exclude-standard", "*.html"))
    return sorted(f for f in files if not f.startswith(NOT_PAGES) and (ROOT / f).exists())


def footer_for(page, partial):
    out = partial
    for old, new in VARIANTS.get(page, []):
        if old not in out:
            sys.exit(f"build-footer: variant for {page} no longer matches scripts/footer.inc: {old!r}")
        out = out.replace(old, new)
    return out


def main():
    check = "--check" in sys.argv[1:]
    partial = PARTIAL.read_text(encoding="utf-8").rstrip("\n")
    changed, missing = [], []
    for page in pages():
        path = ROOT / page
        s = path.read_text(encoding="utf-8")
        found = FOOTER.findall(s)
        if len(found) != 1:
            missing.append(f"{page} ({len(found)} footers)")
            continue
        new = FOOTER.sub(lambda m: footer_for(page, partial), s)
        if new != s:
            changed.append(page)
            if not check:
                path.write_text(new, encoding="utf-8")
    for m in missing:
        print(f"skipped, no single site footer: {m}")
    verb = "out of date" if check else "updated"
    print(f"{len(changed)} page(s) {verb}" + (": " + ", ".join(changed) if changed else ""))
    if check and changed:
        sys.exit(1)


if __name__ == "__main__":
    main()

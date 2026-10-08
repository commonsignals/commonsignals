# Common Signals

[commonsignals.org](https://commonsignals.org) — Common Signals helps people explaining AI know which messages actually work: research, tools, training and workshops for anyone talking about AI.

## About this repo

A static snapshot of the site (HTML, CSS, JS, and assets), reconstructed from the live site's rendered pages.

## Structure

- `index.html` — homepage, plus one directory per page (`about/`, `research/`, `tools/`, `theory-of-change/`, ...)
- `styles.css`, `main.js` — shared styles and site behaviour (nav, scroll reveals, subscribe form)
- `assets/` — images and chart SVGs

Two features depend on the live site's backend and won't work from a static copy alone: the newsletter subscribe form (`/subscribe`) and the comment-analyser tool's link-fetching worker.

## Running locally

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Glossary and editorial conventions

Glossary terms live in one file, `data/glossary-terms.json`. To add or change a term, edit that file and run:

```bash
python3 scripts/build-glossary.py
```

The script rebuilds the term list, the structured data (JSON-LD) and the term count in `glossary.html`, and writes `glossary.json` for the hover cards. It only touches the regions between the `build-glossary:start` and `build-glossary:end` markers. Never edit those regions by hand: the next build will overwrite your change.

When writing articles:

- Link a glossary term on its first use only, not every time it appears.
- If the argument depends on a term, explain it in the text. The glossary link is a backup for readers who want more, not the definition.

# Common Signals

[commonsignals.org](https://commonsignals.org) — Common Signals helps AI communicators know which messages actually work: research, tools, training and workshops for anyone talking about AI.

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

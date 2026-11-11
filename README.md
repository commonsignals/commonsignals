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

## Data pages

`data/index.html` and every `data/<slug>/` and `data/<slug>/codebook/` page hold pre-rendered content between `build-data:start` and `build-data:end` markers, so search engines and AI assistants can read them without running JavaScript. After changing a study, run:

```bash
python3 scripts/data-export.py index
python3 scripts/data-export.py build <slug>
python3 scripts/build-data-pages.py
```

Only the comment explorer itself still loads in the browser.

## Markdown versions and llms.txt

Each research page has a markdown copy beside it for AI tools: `/methodology` has `/methodology.md`, and `/data/` has `/data/index.html.md`. `/llms.txt` indexes them and `/llms-full.txt` holds them all in one file. They are converted from the pages' own HTML, so after changing one of those pages, a study's `study.json` or `data/studies/index.json`, run:

```bash
python3 scripts/build-markdown.py
python3 scripts/check-markdown.py
```

The build also keeps each page's `<link rel="alternate" type="text/markdown">`, the Copy for AI button in article heroes and the build-markdown region of `_headers`. Never edit those or the generated files by hand. The check compares every markdown file with its page and lists anything missing.

## PDF versions

The toolkit and the research agenda each have a PDF in `assets/pdf/`, named by version, and a "Download PDF" link in the page's hero. After changing either page and deploying the change, run:

```bash
python3 scripts/build-pdfs.py
python3 scripts/build-markdown.py
```

The script prints each page with headless Chrome, using the live site's stylesheet, fonts and charts, adds the page's own citation line under the dek, and moves the page's link to the new file. Earlier PDFs stay, so links to them keep working.

## MCP server for AI tools

`/mcp` is a read-only MCP server (`functions/mcp/`) that lets a communicator's own AI tool query the studies and the pages in `/llms.txt`. `/data/ai-tools/` explains how to use it. `package.json` pins its two dependencies. The Pages project's build command, `npm ci` (Settings, Build, in the Cloudflare dashboard), installs them before Pages bundles Functions; with no build command Pages skips the install and the Functions build fails. Run `npm install` once to work on it locally.

It reads the published files at request time, plus two things built from them:

- `python3 scripts/data-export.py build` writes each study's counts to `/data/mcp/<slug>.json`, beside its `data.json`.
- Comment search uses a D1 copy of each `comments.csv`, because the largest study is too big to search within the Workers Free plan's CPU limit. After a recode, correction, takedown or new study, reload it with `python3 scripts/mcp/load-d1.py --remote`. Until then the server refuses to search that study rather than quote an out-of-date copy.

After changing the server's instructions or tools, run `node scripts/mcp/build-page.mjs`, which rewrites the rules and tool list on `/data/ai-tools/` and the server's version.

To run it locally and test it:

```bash
npm install
python3 scripts/mcp/load-d1.py --local
npx wrangler@4.160.0 pages dev --port 8788 --d1 MCP_DB=local-only --persist-to .wrangler/state
```

Then, in another terminal, `python3 scripts/mcp/test-mechanical.py` runs the mechanical tests through the MCP Inspector, and `node --disallow-code-generation-from-strings scripts/mcp/cpu-bench.mjs` measures CPU time per tool call.

The production copy is the D1 database `commonsignals-mcp`, bound as `MCP_DB` in `wrangler.toml`, and `load-d1.py --remote` loads it. Without the binding, every tool except `search_comments` still works.

## Glossary and editorial conventions

Glossary terms live in one file, `data/glossary-terms.json`. To add or change a term, edit that file and run:

```bash
python3 scripts/build-glossary.py
```

The script rebuilds the term list, the structured data (JSON-LD) and the term count in `glossary.html`, and writes `glossary.json` for the hover cards. It only touches the regions between the `build-glossary:start` and `build-glossary:end` markers. Never edit those regions by hand: the next build will overwrite your change.

When writing articles:

- Link a glossary term on its first use only, not every time it appears.
- If the argument depends on a term, explain it in the text. The glossary link is a backup for readers who want more, not the definition.

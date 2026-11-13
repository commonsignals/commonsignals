# Working on this repo

## Publishing an article from `_incoming/`

When publishing or updating an article from `_incoming/`:

1. Run `python3 scripts/check-questions.py <draft>/article.md <update|guide|research>` on the source file first. Put its report at the top of the final summary, above the list of files changed. The checks warn only; publish anyway and let the editor decide.
2. If the draft has a `## Questions people ask` block, build it with `python3 scripts/build-questions.py <draft>/article.md <page>.html`. It writes the section, the contents entry and the FAQPage JSON-LD between `build-questions` markers. Never write or edit those regions by hand; change the draft and rerun.
3. Never publish `<!-- Q SOURCE: ... -->` comments. They are internal notes. The build drops them and refuses to write a page containing one; don't copy them across by any other route.

The editorial rules for the questions themselves are in the Common Signals style guide, not here.

## Site header and footer

The header and footer are shared. Edit `scripts/header.inc` or `scripts/footer.inc`, never a page's own copy, then run `python3 scripts/build-partials.py`. When adding a new page, copy any existing page's header and footer and run the script. Before committing any page, run `python3 scripts/build-partials.py --check`; if it reports a page, you have edited from a stale copy.

# The studies data contract

This describes the shape every study folder under `/data/studies/` follows. It reflects what the three studies on file (`metr-report-reddit-2026-09`, `cotra-episode-2026-09`, `soares-reel-2026-08`) actually contain, not just the original design, so a couple of things below are deliberate adjustments from that first draft. They are called out as they come up.

## Layout

Each study is a folder `/data/studies/<slug>/` with three files:

- `study.json`, metadata about the study: what was captured, how, and the headline counts.
- `codebook.json`, the coding scheme: every dimension a comment was coded on, and its allowed values.
- `comments.csv`, the coded comments themselves, one row per comment.

`codebook.md` also appears in each folder on file. It is the human-readable source the coder worked from; `codebook.json` is the structured version of the same thing. Neither is required by this contract, but where both exist they should agree.

`/data/studies/index.json` lists every study (title, slug, counts, licence) for the explorer to read without fetching each `study.json` in turn.

## Validation

`scripts/data-export.py validate [slug]` checks every study folder, or just one, against this contract: id uniqueness, allowed values, non-empty text (with the stub exemption below), threading consistency, and the counts fields against the CSV. Run it after editing a study folder by hand. It does not check JSON Schema conformance directly (see "on schemas" below); it implements the same required fields natively so the script has no dependencies to install.

## On schemas, and letting studies carry extra detail

`_schema/study.schema.json` and `_schema/codebook.schema.json` describe the fields every study is required to have. They deliberately do not forbid additional properties. In practice, every study on file carries genuinely useful extra detail beyond this core: METR's `study.json` has a `design` field and a full `threads` breakdown; Cotra's has extra `counts` fields like `views_at_capture`; Soares' has `empty_or_stub` and `likes_available`. Trimming studies down to the letter of the contract would throw that detail away for no benefit, so the schemas validate that the required fields are present and correctly typed, and leave everything else alone. If a stricter, closed contract turns out to matter later (for a stability guarantee to the Phase 2 UI, say), that is a decision to make deliberately, not a side effect of schema validation.

## study.json

Required fields:

- `slug`: string, matches the folder name.
- `title`: string.
- `series`: string. All three studies on file share `"agent-swarm reception"`.
- `platform`: string, for example `"reddit"`, `"youtube"`, `"instagram"`.
- `artefact_title`, `artefact_url`, `artefact_published`: the thing being reacted to (the article, video or post) and when it went up.
- `central_claim`: the statement stance is coded against. Say what counts as agreeing with it, either here or in the codebook's `stance_note`.
- `capture_dates`: array of ISO dates. More than one date means more than one capture; `capture_method` and `changelog` should explain why.
- `capture_method`: free text. Say what was captured, how, and what was lost (missing like counts, lost threading, and so on) so the explorer's caveats can be sourced from here.
- `counts`: object. Always present: `retrieved` (rows captured), `coded` (rows in comments.csv; must equal the row count), `clear_position_base` (rows whose stance is not the codebook's no-position or unclear value). Everything else in `counts` is study-specific and optional: present when it means something for that capture method, left out rather than set to null when it does not (Soares has no `top_level`/`replies` at all, rather than nulls, because it has no threading).
- `spot_check`: object with `sample`, `agreed`, `checked_by`, `date`, `note`. All nullable; a null field means "not recorded" in the explorer, not "zero".
- `coders`: free text describing who or what did the coding.
- `article_url`: the Common Signals article this study backs, or null.
- `findings_note_url`: nullable.
- `version`: integer, starts at 1.
- `changelog`: array of `{version, date, note}`, oldest first.
- `licence`: string. All three studies on file use `"CC BY 4.0 (coding and compilation; comment text remains its authors')"`. The licence covers the coding and compilation; comment text remains its authors'.
- `notes`: free text for anything that does not fit elsewhere (known gaps, caveats, things a reader should know before quoting a number).

## codebook.json

Required fields:

- `central_claim`: string. Should match `study.json`'s.
- `stance_note`: string, defining what each stance value means for this study's central claim (for example "agree = accepts AI is a serious existential danger worth acting on"). This is what a validator or explorer uses to work out which stance values count as a clear position, so word it as a list of `value = definition` clauses.
- `coder_instructions`: free text, the brief given to the coder.
- `dimensions`: array. Each dimension is:
  - `key`: matches a comments.csv column name.
  - `label`: display name.
  - `kind`: `"single"` (one value from a fixed list, like stance or frame), `"flag"` (boolean, a comments.csv column named `mentions_<thing>` or a bare flag like `non_english`), `"group"` (a study-specific grouping column, like METR's `period` or `subreddit`), or `"meta"` (a plain descriptive column, like a reply count or a timestamp-precision caption, that is not a facet and carries no allowed-value list).
  - `shared`: true if the same values apply across every study in the series (stance, format_reaction, emotion), false if they are study-specific (frame always is; flag and group dimensions usually are).
  - `values`: array of `{value, label, definition, example}`, the allowed values for `single` and `group` dimensions. Flag and meta dimensions do not carry a `values` array; this contract does not require one for either.

## comments.csv

Columns, in this order, where they exist:

`id, parent_id, depth, author_hash, published_at, published_at_precision, likes, text, stance, frame, format_reaction, emotion`, then one column per mention flag named `mentions_<thing>` (plus any bare flags like `non_english`), then `coder, spot_checked, correction_note`. A study may append its own group columns after these (METR has `period, subreddit, thread_url`); each must be declared in `codebook.json` as a `group` dimension.

Rules, and the exceptions actually seen in the three studies on file:

- `id` is unique within the file.
- `parent_id` is empty or resolves to an `id` in the same file. `depth` is `0` when `parent_id` is empty; the contract does not assume `depth` equals the parent's depth plus one, because platforms with a flat reply UI (confirmed for YouTube) give every reply depth 1 regardless of which comment in the thread it replies to.
- Both columns must exist. When a capture method could not preserve threading at all, they are present and blank on every row rather than omitted (METR, Soares), so every study has the same CSV shape. `study.json`'s `capture_method` should say so.
- `likes` is an integer or empty, and is never zero when the true value is unknown. A study whose capture method never had access to engagement data (Soares) can have `likes` empty on every row; that is valid, not missing data, and `study.json`'s `counts.likes_available` (or equivalent) should say so.
- `text` is non-empty on every row, with one exemption: a row whose `coder` is exactly `not_coded_empty_stub` marks an intentionally uncoded stub (for example a GIF or sticker-only reply the platform exposes no text for). These rows stay in the file and count towards `counts.coded`; they are not dropped and not required to have text.
- Every coded value (`stance`, `frame`, `format_reaction`, `emotion`, any `group` column) is in the codebook's allowed set for that column.
- Flag columns (`mentions_*` and bare flags like `non_english`) hold exactly `true` or `false`, lowercase. Every `mentions_` column in the CSV has a matching flag dimension in `codebook.json`, and vice versa.
- A study may append a trailing free-text `flags` column for coder notes. It is not part of this contract and the validator does not check it.

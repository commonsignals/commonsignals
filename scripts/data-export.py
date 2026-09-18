#!/usr/bin/env python3
"""Data contract tooling for /data/studies/.

Usage:
    python3 scripts/data-export.py validate [slug]
    python3 scripts/data-export.py index
    python3 scripts/data-export.py build [slug]
    python3 scripts/data-export.py export <input_csv> <input_codebook_md> <slug>

`validate` checks every study folder under /data/studies/ (or just one, if a
slug is passed) against the contract described in /data/studies/README.md.
`index` regenerates /data/studies/index.json from each study's study.json.
`build` validates first (aborting on any failure), then writes
/data/<slug>/data.json for each study (or just one): study.json and
codebook.json verbatim, plus every comments.csv row as an object with flag
columns as real JSON booleans and `likes` as a number or null. This is what
the explorer UI under /data/<slug>/ fetches; nothing here pre-aggregates
facet counts, which the UI computes itself from the loaded array.
`export` is not implemented yet -- all studies currently on file arrived
already in contract shape.
"""
import csv
import json
import sys
from pathlib import Path

STUDIES_ROOT = Path(__file__).resolve().parent.parent / "data" / "studies"

# Row-level checks that get a stub-row exemption: rows whose `coder` marks
# them as an intentionally-uncoded empty stub (e.g. a GIF/sticker-only reply
# the platform never exposed text for) are allowed to have empty text.
STUB_CODER_VALUE = "not_coded_empty_stub"

# Required top-level fields per the schemas under _schema/. Kept in sync with
# those files by hand; this script has no dependency on a JSON Schema
# library, so it checks presence natively rather than interpreting the
# schema documents directly.
STUDY_REQUIRED = [
    "slug", "title", "series", "platform",
    "artefact_title", "artefact_url", "artefact_published",
    "central_claim", "capture_dates", "capture_method",
    "counts", "spot_check", "coders",
    "article_url", "findings_note_url",
    "version", "changelog", "licence", "notes",
]
COUNTS_REQUIRED = ["retrieved", "coded", "clear_position_base"]
SPOT_CHECK_REQUIRED = ["sample", "agreed", "checked_by", "note"]
CODEBOOK_REQUIRED = ["central_claim", "stance_note", "coder_instructions", "dimensions"]
DIMENSION_REQUIRED = ["key", "label", "kind", "shared"]
DIMENSION_KINDS = {"single", "flag", "group", "meta"}


def load_study(folder: Path):
    study = json.loads((folder / "study.json").read_text())
    codebook = json.loads((folder / "codebook.json").read_text())
    with open(folder / "comments.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return study, codebook, rows


def validate_study(folder: Path):
    slug = folder.name
    failures = []  # (row_id_or_None, message)
    notes = []     # structural observations that are not contract violations

    study, codebook, rows = load_study(folder)
    columns = rows[0].keys() if rows else []

    # schema shape: required fields present in study.json and codebook.json
    for key in STUDY_REQUIRED:
        if key not in study:
            failures.append((None, f"study.json missing required field {key!r}"))
    for key in COUNTS_REQUIRED:
        if key not in study.get("counts", {}):
            failures.append((None, f"study.json counts missing required field {key!r}"))
    if study.get("spot_check") is not None:
        for key in SPOT_CHECK_REQUIRED:
            if key not in study["spot_check"]:
                failures.append((None, f"study.json spot_check missing required field {key!r}"))
    for key in CODEBOOK_REQUIRED:
        if key not in codebook:
            failures.append((None, f"codebook.json missing required field {key!r}"))
    for dim in codebook.get("dimensions", []):
        for key in DIMENSION_REQUIRED:
            if key not in dim:
                failures.append((None, f"codebook.json dimension {dim.get('key','?')!r} missing required field {key!r}"))
        if dim.get("kind") not in DIMENSION_KINDS:
            failures.append((None, f"codebook.json dimension {dim.get('key','?')!r} has kind={dim.get('kind')!r}, not one of {sorted(DIMENSION_KINDS)}"))
        if dim.get("kind") in ("single", "group") and "values" not in dim:
            failures.append((None, f"codebook.json dimension {dim.get('key','?')!r} is kind={dim.get('kind')!r} but has no values array"))

    # single and group dimensions both carry an allowed-value list that CSV
    # columns get checked against; meta dimensions are descriptive only.
    valued_dims = {d["key"]: d for d in codebook["dimensions"] if d["kind"] in ("single", "group")}
    flag_dims = {d["key"] for d in codebook["dimensions"] if d["kind"] == "flag"}
    allowed = {k: {v["value"] for v in d.get("values", [])} for k, d in valued_dims.items()}

    # id uniqueness
    ids = [r["id"] for r in rows]
    seen = set()
    for rid in ids:
        if rid in seen:
            failures.append((rid, "duplicate id"))
        seen.add(rid)
    id_set = set(ids)

    has_threading_columns = "parent_id" in columns and "depth" in columns
    # Some studies keep the columns but leave every row blank (threading lost
    # in capture, per study.json) rather than omit the columns outright. Both
    # mean the same thing for validation purposes: there is nothing to check.
    has_threading = has_threading_columns and any(r["parent_id"].strip() or r["depth"].strip() for r in rows)
    if not has_threading_columns:
        notes.append("comments.csv has no parent_id/depth columns (threading not captured for this platform/method)")
    elif not has_threading:
        notes.append("comments.csv has parent_id/depth columns but every row is blank (threading lost in capture, per study.json)")

    # Flag-casing violations are a file-wide formatting convention, not a
    # per-row data problem, so we aggregate them by column instead of
    # emitting one failure line per offending row.
    bad_flag_casing = {key: [] for key in flag_dims}

    for r in rows:
        rid = r["id"]

        # text non-empty, with the stub exemption
        if not r["text"].strip() and r.get("coder") != STUB_CODER_VALUE:
            failures.append((rid, "empty text (and not marked as an empty stub)"))

        # allowed values for single-kind dimensions
        for key, allowed_vals in allowed.items():
            if key in r and r[key] not in allowed_vals:
                failures.append((rid, f"{key}={r[key]!r} not in codebook's allowed values"))

        # flag values must be exactly lowercase true/false
        for key in flag_dims:
            if key in r and r[key] not in ("true", "false"):
                bad_flag_casing[key].append(r[key])

        # threading, when present
        if has_threading:
            parent = r["parent_id"].strip()
            if parent and parent not in id_set:
                failures.append((rid, f"parent_id {parent!r} does not resolve to an id in this file"))
            if not parent and r["depth"].strip() != "0":
                failures.append((rid, f"depth={r['depth']!r} but parent_id is empty (expected 0)"))

    for key, bad_values in bad_flag_casing.items():
        if bad_values:
            examples = sorted(set(bad_values))
            failures.append((None, f"{key}: {len(bad_values)}/{len(rows)} rows use non-lowercase true/false (values seen: {examples})"))

    # depth vs parent_id consistency. Note: we do NOT assert depth == parent's
    # depth + 1. Platforms with flat reply UIs (confirmed for YouTube/Cotra)
    # give every reply depth=1 regardless of which comment in the thread it is
    # addressed to, so a reply's parent_id can point to another depth-1 reply
    # without depth itself incrementing. We only check the two things the
    # contract actually needs: depth=0 iff no parent, depth>=1 iff a parent.
    if has_threading:
        for r in rows:
            parent = r["parent_id"].strip()
            try:
                depth = int(r["depth"])
            except ValueError:
                failures.append((r["id"], f"depth={r['depth']!r} is not an integer"))
                continue
            if parent and depth < 1:
                failures.append((r["id"], f"depth={depth} but parent_id is set (expected >=1)"))

    # mentions_ column <-> flag-dimension correspondence, both directions
    mentions_csv = {c for c in columns if c.startswith("mentions_")}
    mentions_cb = {k for k in flag_dims if k.startswith("mentions_")}
    for extra in mentions_csv - mentions_cb:
        failures.append((None, f"CSV column {extra} has no matching flag dimension in codebook.json"))
    for missing in mentions_cb - mentions_csv:
        failures.append((None, f"codebook.json flag dimension {missing} has no matching CSV column"))

    # counts.coded == row count
    counts = study.get("counts", {})
    if counts.get("coded") != len(rows):
        failures.append((None, f"study.json counts.coded={counts.get('coded')!r} but comments.csv has {len(rows)} rows"))

    # counts.top_level / counts.replies, when threading present
    if has_threading:
        top_level = sum(1 for r in rows if not r["parent_id"].strip())
        replies = len(rows) - top_level
        if counts.get("top_level") is not None and counts.get("top_level") != top_level:
            failures.append((None, f"study.json counts.top_level={counts.get('top_level')!r} but file has {top_level}"))
        if counts.get("replies") is not None and counts.get("replies") != replies:
            failures.append((None, f"study.json counts.replies={counts.get('replies')!r} but file has {replies}"))
    else:
        if counts.get("top_level") is not None or counts.get("replies") is not None:
            notes.append("study.json sets top_level/replies but comments.csv has no threading columns to check them against")

    # clear_position_base: rows whose stance is not the unclear/no-position value(s)
    # named in the codebook's stance_note. We infer "positioned" stance values as
    # those stance_note explicitly defines (agree/disagree/mixed-style), and
    # treat any stance value NOT mentioned there as a no-position/unclear value.
    stance_note = codebook.get("stance_note", "")
    stance_allowed = allowed.get("stance", set())
    positioned_values = {v for v in stance_allowed if v in stance_note}
    if positioned_values:
        actual_positioned = sum(1 for r in rows if r.get("stance") in positioned_values)
        if counts.get("clear_position_base") != actual_positioned:
            failures.append((None, f"study.json counts.clear_position_base={counts.get('clear_position_base')!r} but {actual_positioned} rows have a stance in {sorted(positioned_values)}"))
    else:
        notes.append("could not infer which stance values count as 'positioned' from stance_note; clear_position_base not checked")

    return slug, failures, notes


def study_slugs(root: Path):
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("_"))


def cmd_validate(args):
    root = STUDIES_ROOT
    if args:
        slugs = [args[0]]
    else:
        slugs = study_slugs(root)

    any_failures = False
    for slug in slugs:
        folder = root / slug
        if not folder.is_dir():
            print(f"{slug}: FAIL - no such study folder under {root}")
            any_failures = True
            continue
        slug, failures, notes = validate_study(folder)
        print(f"=== {slug} ===")
        for row_id, msg in failures:
            label = f"[{row_id}] " if row_id else ""
            print(f"  FAIL {label}{msg}")
        for note in notes:
            print(f"  NOTE {note}")
        if failures:
            any_failures = True
            print(f"  {len(failures)} failure(s)")
        else:
            print("  0 failures")
        print()

    sys.exit(1 if any_failures else 0)


def cmd_index(args):
    root = STUDIES_ROOT
    studies = []
    for slug in study_slugs(root):
        s = json.loads((root / slug / "study.json").read_text())
        studies.append({
            "slug": s["slug"],
            "title": s["title"],
            "platform": s["platform"],
            "series": s["series"],
            "article_url": s["article_url"],
            "counts": {k: s["counts"][k] for k in COUNTS_REQUIRED},
            "version": s["version"],
            "licence": s["licence"],
        })
    index = {
        "$schema": "https://commonsignals.org/data/studies/_schema/index.schema.json",
        "series": sorted({s["series"] for s in studies}),
        "generated_note": "Generated from each study's study.json by scripts/data-export.py index. Regenerate rather than hand-edit. 'series' is every distinct series value on file, not one sitewide series; each study's own series is under studies[].series.",
        "studies": studies,
    }
    out = root / "index.json"
    out.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {out} ({len(studies)} studies)")


def cmd_export(args):
    print("export is not implemented yet: all studies on file arrived already in contract shape.")
    sys.exit(2)


# Fixed contract column that is boolean-shaped (see README's comments.csv
# rules) but, unlike mentions_*/non_english, is not declared as a `flag`
# dimension in codebook.json -- it is part of every study's CSV shape
# regardless of that study's coding scheme.
ALWAYS_BOOL_COLUMNS = {"spot_checked"}


def typed_row(row: dict, flag_keys: set) -> dict:
    out = dict(row)
    for key in flag_keys | ALWAYS_BOOL_COLUMNS:
        if key in out:
            out[key] = out[key] == "true"
    if "likes" in out:
        out["likes"] = int(out["likes"]) if out["likes"].strip() != "" else None
    return out


def cmd_build(args):
    root = STUDIES_ROOT
    slugs = [args[0]] if args else study_slugs(root)

    any_failures = False
    for slug in slugs:
        folder = root / slug
        if not folder.is_dir():
            print(f"{slug}: FAIL - no such study folder under {root}")
            any_failures = True
            continue
        _, failures, _ = validate_study(folder)
        if failures:
            print(f"=== {slug} ===")
            for row_id, msg in failures:
                label = f"[{row_id}] " if row_id else ""
                print(f"  FAIL {label}{msg}")
            print(f"  {len(failures)} failure(s)")
            any_failures = True

    if any_failures:
        print("\nbuild aborted: fix the validation failures above first.")
        sys.exit(1)

    data_root = root.parent  # /data
    for slug in slugs:
        folder = root / slug
        study, codebook, rows = load_study(folder)
        flag_keys = {d["key"] for d in codebook["dimensions"] if d["kind"] == "flag"}
        comments = [typed_row(r, flag_keys) for r in rows]
        payload = {"study": study, "codebook": codebook, "comments": comments}

        out_dir = data_root / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "data.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False) + "\n")
        print(f"wrote {out_path} ({len(comments)} comments)")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("validate", "index", "build", "export"):
        print(__doc__)
        sys.exit(2)
    subcommand, rest = sys.argv[1], sys.argv[2:]
    if subcommand == "validate":
        cmd_validate(rest)
    elif subcommand == "index":
        cmd_index(rest)
    elif subcommand == "build":
        cmd_build(rest)
    else:
        cmd_export(rest)

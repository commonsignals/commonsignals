#!/usr/bin/env python3
"""Data contract tooling for /data/studies/.

Usage:
    python3 scripts/data-export.py validate [slug]
    python3 scripts/data-export.py export <input_csv> <input_codebook_md> <slug>

`validate` checks every study folder under the given root (or just one, if a
slug is passed) against the series contract described in the Phase 1 spec.
`export` is not implemented yet -- all studies currently on file arrived
already in contract shape.
"""
import csv
import json
import sys
from pathlib import Path

STUDIES_ROOT = Path(__file__).resolve().parent.parent / "study"

# Row-level checks that get a stub-row exemption: rows whose `coder` marks
# them as an intentionally-uncoded empty stub (e.g. a GIF/sticker-only reply
# the platform never exposed text for) are allowed to have empty text.
STUB_CODER_VALUE = "not_coded_empty_stub"


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

    single_dims = {d["key"]: d for d in codebook["dimensions"] if d["kind"] == "single"}
    flag_dims = {d["key"] for d in codebook["dimensions"] if d["kind"] == "flag"}
    allowed = {k: {v["value"] for v in d.get("values", [])} for k, d in single_dims.items()}

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


def cmd_validate(args):
    root = STUDIES_ROOT
    if args:
        slugs = [args[0]]
    else:
        slugs = sorted(p.name for p in root.iterdir() if p.is_dir())

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


def cmd_export(args):
    print("export is not implemented yet: all studies on file arrived already in contract shape.")
    sys.exit(2)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("validate", "export"):
        print(__doc__)
        sys.exit(2)
    subcommand, rest = sys.argv[1], sys.argv[2:]
    if subcommand == "validate":
        cmd_validate(rest)
    else:
        cmd_export(rest)

"""Load each study's comments into the D1 copy that the MCP server at /mcp searches.

Usage, from anywhere:
    python3 scripts/mcp/load-d1.py --local            # the copy wrangler pages dev uses
    python3 scripts/mcp/load-d1.py --remote           # the production copy
    python3 scripts/mcp/load-d1.py --local --force    # reload every study
    python3 scripts/mcp/load-d1.py --local <slug>...  # only these studies

Run it after scripts/data-export.py build whenever a study's comments.csv changes:
a recode, a correction, a takedown or a new study. A study is reloaded only when
its comments.csv differs from the loaded copy, compared by SHA-256. The server
compares the same fingerprint with /data/mcp/<slug>.json and refuses to search a
study whose copy is out of date, so it never quotes a comment that has since
changed or been removed.

Each load writes a new table named from the slug and the fingerprint, then points
the study's mcp_studies row at it and drops the old table, so a search never sees
half a study. D1 on the Workers Free plan allows 100,000 rows written a day;
reloading the largest study writes about 24,000.

--local uses scripts/mcp/wrangler-local.toml and .wrangler/state, which is what
`wrangler pages dev --d1 MCP_DB=local-only --persist-to .wrangler/state` reads.
--remote uses the MCP_DB binding in the site's wrangler.toml.
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDIES = ROOT / "data" / "studies"
WRANGLER = ["npx", "--yes", "wrangler@4.160.0"]
TARGETS = {
    "local": ["--local", "--config", str(ROOT / "scripts" / "mcp" / "wrangler-local.toml"),
              "--persist-to", str(ROOT / ".wrangler" / "state")],
    "remote": ["--remote"],
}
# D1 accepts statements up to 100,000 bytes; inserts are batched below that.
MAX_STATEMENT = 90_000
FIXED = ["n", "parent_n", "id", "parent_id", "published_at", "published_at_precision", "likes", "text", "text_lc"]
SAFE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
REGISTRY = ("CREATE TABLE IF NOT EXISTS mcp_studies (slug TEXT PRIMARY KEY, table_name TEXT NOT NULL, "
            "comments_sha256 TEXT NOT NULL, rows INTEGER NOT NULL, columns TEXT NOT NULL, loaded_at TEXT NOT NULL);")


def wrangler(target, *args, check=True):
    result = subprocess.run([*WRANGLER, "d1", "execute", "MCP_DB", *TARGETS[target], *args],
                            cwd=ROOT, capture_output=True, text=True)
    if check and result.returncode != 0:
        sys.exit(f"wrangler d1 execute failed:\n{(result.stderr or result.stdout)[-3000:]}")
    return result


def loaded(target):
    """The mcp_studies rows already in the database, by slug."""
    wrangler(target, "--command", REGISTRY)
    out = wrangler(target, "--json", "--command", "SELECT slug, table_name, comments_sha256 FROM mcp_studies;").stdout
    try:
        results = json.loads(out)[0]["results"]
    except (ValueError, KeyError, IndexError):
        sys.exit(f"could not read mcp_studies:\n{out[-2000:]}")
    return {r["slug"]: r for r in results}


def literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, int):
        return str(value)
    if "\x00" in value:
        sys.exit("a field contains a NUL character, which D1 cannot store")
    return "'" + value.replace("'", "''") + "'"


def study_sql(slug, sha, old_table):
    folder = STUDIES / slug
    codebook = json.loads((folder / "codebook.json").read_text(encoding="utf-8"))
    with open(folder / "comments.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    codes = [d["key"] for d in codebook["dimensions"] if d["kind"] in ("single", "flag", "group")]
    bad = [c for c in codes if not SAFE_NAME.match(c) or c in FIXED]
    if bad:
        sys.exit(f"{slug}: dimension keys unusable as column names: {bad}")
    table = f"c_{re.sub(r'[^a-z0-9]+', '_', slug)}_{sha[:12]}"
    row_number = {r["id"]: n for n, r in enumerate(rows, 1)}

    statements = [
        f'DROP TABLE IF EXISTS "{table}";',
        f'CREATE TABLE "{table}" (n INTEGER PRIMARY KEY, parent_n INTEGER, id TEXT NOT NULL, parent_id TEXT, '
        f'published_at TEXT, published_at_precision TEXT, likes TEXT, text TEXT NOT NULL, text_lc TEXT NOT NULL'
        + "".join(f', "{c}" TEXT' for c in codes) + ");",
    ]
    head = f'INSERT INTO "{table}" (' + ", ".join(f'"{c}"' for c in FIXED + codes) + ") VALUES "
    batch, size = [], len(head.encode())
    for n, r in enumerate(rows, 1):
        parent = r.get("parent_id", "").strip()
        values = [n, row_number.get(parent) if parent else None, r["id"], parent or None,
                  r.get("published_at", ""), r.get("published_at_precision", ""), r.get("likes", ""),
                  r["text"], r["text"].lower()] + [r[c] for c in codes]
        tuple_sql = "(" + ", ".join(literal(v) for v in values) + ")"
        length = len(tuple_sql.encode()) + 2
        if len(head.encode()) + length > MAX_STATEMENT:
            sys.exit(f"{slug}: comment {r['id']} is too long for one D1 statement")
        if batch and size + length > MAX_STATEMENT:
            statements.append(head + ", ".join(batch) + ";")
            batch, size = [], len(head.encode())
        batch.append(tuple_sql)
        size += length
    if batch:
        statements.append(head + ", ".join(batch) + ";")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    statements.append(
        "INSERT INTO mcp_studies (slug, table_name, comments_sha256, rows, columns, loaded_at) VALUES ("
        + ", ".join(literal(v) for v in (slug, table, sha, len(rows), json.dumps(codes), now))
        + ") ON CONFLICT(slug) DO UPDATE SET table_name = excluded.table_name, comments_sha256 = excluded.comments_sha256, "
          "rows = excluded.rows, columns = excluded.columns, loaded_at = excluded.loaded_at;")
    if old_table and old_table != table:
        statements.append(f'DROP TABLE IF EXISTS "{old_table}";')
    return "\n".join(statements) + "\n", len(rows)


def main():
    parser = argparse.ArgumentParser(description="Load comments into the MCP server's D1 copy.")
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--local", action="store_true", help="the local copy wrangler pages dev serves")
    where.add_argument("--remote", action="store_true", help="the production copy")
    parser.add_argument("--force", action="store_true", help="reload even when the fingerprint matches")
    parser.add_argument("slugs", nargs="*", help="only these studies")
    args = parser.parse_args()
    target = "local" if args.local else "remote"

    index = json.loads((STUDIES / "index.json").read_text(encoding="utf-8"))
    slugs = [s["slug"] for s in index["studies"]]
    unknown = [s for s in args.slugs if s not in slugs]
    if unknown:
        sys.exit(f"unknown slug(s): {unknown}")
    current = loaded(target)
    for slug in args.slugs or slugs:
        sha = hashlib.sha256((STUDIES / slug / "comments.csv").read_bytes()).hexdigest()
        old = current.get(slug, {})
        if old.get("comments_sha256") == sha and not args.force:
            print(f"{slug}: up to date")
            continue
        sql, count = study_sql(slug, sha, old.get("table_name"))
        with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False, encoding="utf-8") as fh:
            fh.write(sql)
            path = fh.name
        try:
            wrangler(target, "--file", path)
        finally:
            Path(path).unlink()
        print(f"{slug}: loaded {count} comments ({len(sql.encode()) // 1024} KB of SQL)")


if __name__ == "__main__":
    main()

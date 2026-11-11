"""Recount a study's figures straight from its comments.csv, to check what the MCP
server's get_study returns. Deliberately separate from scripts/data-export.py and from
the server: it reads the contract files itself and shares no code with either.

    python3 scripts/mcp/recount.py <slug> [split_by]   # prints the recount as JSON
"""
import csv
import json
import math
import sys
from pathlib import Path

STUDIES = Path(__file__).resolve().parents[2] / "data" / "studies"
# Stance values that are not a clear position, as the data contract describes them.
NO_POSITION = {"na", "unclear"}


def pct(n, base):
    """One decimal place, rounding halves up, as the server's Math.round does."""
    return math.floor(1000 * n / base + 0.5) / 10 if base else None


def recount(slug, split_by=None):
    folder = STUDIES / slug
    codebook = json.loads((folder / "codebook.json").read_text(encoding="utf-8"))
    with open(folder / "comments.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    stance_values = [v["value"] for d in codebook["dimensions"] if d["key"] == "stance" for v in d["values"]]

    def block(subset):
        base = len(subset)
        clear = sum(1 for r in subset if r["stance"] not in NO_POSITION)
        out = {"base": base, "clear_position_base": clear, "dimensions": {}, "stance_clear": {}}
        for d in codebook["dimensions"]:
            if d["kind"] == "single":
                counts = {v["value"]: sum(1 for r in subset if r[d["key"]] == v["value"]) for v in d["values"]}
                out["dimensions"][d["key"]] = {k: [n, pct(n, base)] for k, n in counts.items()}
            elif d["kind"] == "flag":
                n = sum(1 for r in subset if r[d["key"]] == "true")
                out["dimensions"][d["key"]] = {"true": [n, pct(n, base)]}
        for value in stance_values:
            if value not in NO_POSITION:
                n = sum(1 for r in subset if r["stance"] == value)
                out["stance_clear"][value] = [n, pct(n, clear)]
        return out

    result = {"slug": slug, "all": block(rows)}
    if split_by:
        group = next(d for d in codebook["dimensions"] if d["key"] == split_by)
        result["groups"] = {v["value"]: block([r for r in rows if r[split_by] == v["value"]]) for v in group["values"]}
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print(json.dumps(recount(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None), indent=1))

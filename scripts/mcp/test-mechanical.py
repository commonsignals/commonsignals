"""Mechanical tests for the MCP server at /mcp, run through the MCP Inspector's CLI.

Start the local server first (see the README's section on the MCP server), then:
    python3 scripts/mcp/test-mechanical.py [--url http://127.0.0.1:8788/mcp]

It checks that:
  - tools/list returns every tool with its description, schemas and read-only hints;
  - every tool answers valid arguments, and refuses an unknown slug, dimension and value;
  - 20 comments drawn at random across studies (seed 20261026) come back from
    search_comments byte for byte as they are in comments.csv;
  - every figure get_study returns for two studies matches scripts/mcp/recount.py;
  - compare_studies refuses frame, and get_page refuses URLs not in /llms.txt;
  - no search_comments response exceeds 60 KB, and get_page returns the largest
    page in parts that are each small enough to show inline and rejoin exactly;
  - the 121st request in a minute gets 429. That runs last, after a minute's wait.
The arguments include the marker zzqx, so the server's log can be searched for it
afterwards: it should not appear, because the log holds tool names only.
"""
import argparse
import csv
import json
import random
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from recount import recount  # noqa: E402

INSPECTOR = ["npx", "--yes", "@modelcontextprotocol/inspector@2.14.0", "--cli", "--connect-timeout", "60000"]
SEED = 20261026
TOOLS = ["list_studies", "get_study", "get_codebook", "search_comments", "compare_studies", "list_pages", "get_page"]
SEARCH_CAP, PAGE_CAP = 60_000, 200_000
# Claude Code saved a 51 KB tool result to a file instead of showing it, while
# results of up to 32,000 characters showed inline in the acceptance runs.
INLINE_CAP = 32_000
LARGEST, GROUPED = "doac-debate-youtube-2026-09", "metr-report-reddit-2026-09"

failures, passes = [], []


def check(ok, label, detail=""):
    (passes if ok else failures).append(label if ok else f"{label}: {detail}")
    return ok


def inspector(url, *args, retried=False):
    result = subprocess.run([*INSPECTOR, url, *args], capture_output=True, text=True, cwd=ROOT)
    try:
        return json.loads(result.stdout)
    except ValueError:
        # Each Inspector call makes several requests, so a long run can reach the
        # server's own limit of 120 a minute. Wait for a fresh minute and retry once.
        if "429" in result.stderr and not retried:
            print("  rate limit reached; waiting 61 s", flush=True)
            time.sleep(61)
            return inspector(url, *args, retried=True)
        raise SystemExit(f"the Inspector gave no JSON for {args}:\n{result.stderr[-1500:]}")


def call(server, tool, **args):
    flags = []
    for key, value in args.items():
        flags += ["--tool-arg", f"{key}={value if isinstance(value, str) else json.dumps(value)}"]
    result = inspector(server, "--method", "tools/call", "--tool-name", tool, *flags)
    body = result.get("structuredContent")
    if body is None and result.get("content"):
        body = json.loads(result["content"][0]["text"])
    return bool(result.get("isError")), body or {}


def raw_call(url, tool, args, ip_header=None):
    """One tools/call over plain HTTP, for measuring the response as sent."""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": args}}).encode()
    headers = {"content-type": "application/json", "accept": "application/json, text/event-stream", "mcp-protocol-version": "2025-06-18"}
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    with urllib.request.urlopen(req) as res:
        raw = res.read()
    text = raw.decode()
    data = [line[6:] for line in text.splitlines() if line.startswith("data: ")] or [text]
    return len(raw), json.loads(data[-1])["result"]


def csv_rows(slug):
    with open(ROOT / "data" / "studies" / slug / "comments.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def tools_list(url):
    tools = inspector(url, "--method", "tools/list")["tools"]
    names = [t["name"] for t in tools]
    check(names == TOOLS, "tools/list names every tool", f"got {names}")
    for t in tools:
        words = len(t.get("description", "").split())
        check(0 < words < 80, f"{t['name']} description is under 80 words", f"{words} words")
        check("inputSchema" in t and "outputSchema" in t, f"{t['name']} has input and output schemas")
        hints = t.get("annotations", {})
        check(hints.get("readOnlyHint") is True and hints.get("openWorldHint") is False, f"{t['name']} is marked read-only and closed-world", str(hints))


def valid_and_refused(url):
    page = "https://commonsignals.org/methodology"
    valid = [("list_studies", {}), ("get_study", {"slug": GROUPED, "split_by": "period"}), ("get_codebook", {"slug": LARGEST}),
             ("search_comments", {"slug": LARGEST, "text": "unplug"}), ("compare_studies", {"dimension": "emotion"}),
             ("list_pages", {}), ("get_page", {"url": page})]
    for tool, args in valid:
        is_error, body = call(url, tool, **args)
        check(not is_error and body, f"{tool} answers valid arguments", json.dumps(body)[:200])
    bad = "zzqx-unknown"
    refusals = [
        ("get_study", {"slug": bad}, "valid_slugs"), ("get_codebook", {"slug": bad}, "valid_slugs"),
        ("search_comments", {"slug": bad}, "valid_slugs"),
        ("get_study", {"slug": GROUPED, "split_by": bad}, "valid_split_by"),
        ("search_comments", {"slug": LARGEST, "filters": {bad: ["x"]}}, "valid_dimensions"),
        ("compare_studies", {"dimension": bad}, "shared_dimensions"),
        ("search_comments", {"slug": LARGEST, "filters": {"stance": [bad]}}, "valid_values"),
        ("compare_studies", {"dimension": "frame"}, "shared_dimensions"),
        ("get_page", {"url": "https://commonsignals.org/zzqx-not-listed"}, None),
        ("get_page", {"url": "https://example.com/methodology"}, None),
    ]
    for tool, args, field in refusals:
        is_error, body = call(url, tool, **args)
        ok = is_error and "error" in body and (field is None or body.get(field))
        check(ok, f"{tool} refuses {json.dumps(args)}" + (f" and lists {field}" if field else ""), json.dumps(body)[:200])
    is_error, body = call(url, "compare_studies", dimension="frame")
    check("frames with its own list" in body.get("error", ""), "compare_studies explains that each study codes frames with its own list", body.get("error", ""))


def exact_comments(url):
    index = json.loads((ROOT / "data" / "studies" / "index.json").read_text(encoding="utf-8"))
    population = [(s["slug"], k) for s in index["studies"] for k in range(s["counts"]["coded"])]
    sample = random.Random(SEED).sample(population, 20)
    cache = {}
    for slug, k in sample:
        rows = cache.setdefault(slug, csv_rows(slug))
        is_error, body = call(url, "search_comments", slug=slug, limit=1, offset=k)
        got = (body.get("rows") or [{}])[0]
        want = rows[k]
        same = not is_error and got.get("id") == want["id"] and got.get("text", "").encode() == want["text"].encode()
        check(same, f"comment {slug} row {k + 1} ({want['id']}) is byte for byte as in comments.csv",
              f"got id {got.get('id')!r}, {len(got.get('text', ''))} chars against {len(want['text'])}")
        check("author_hash" not in json.dumps(body), f"comment {want['id']} carries no author_hash")


def figures_match(url):
    for slug, split_by in ((LARGEST, None), (GROUPED, "period")):
        args = {"slug": slug} if split_by is None else {"slug": slug, "split_by": split_by}
        is_error, body = call(url, "get_study", **args)
        want = recount(slug, split_by)
        blocks = [("all", body["figures"], want["all"])]
        if split_by:
            got_groups = {g["value"]: g for g in body["split_by"]["groups"]}
            check(set(got_groups) == set(want["groups"]), f"{slug} has every {split_by} group")
            blocks += [(f"{split_by}={v}", got_groups.get(v, {}), w) for v, w in want["groups"].items()]
        compared = mismatched = 0
        for label, got, w in blocks:
            pairs = [("base", got.get("base"), w["base"]), ("clear_position_base", got.get("clear_position_base"), w["clear_position_base"])]
            for v in got["stance"]["all_coded"]["values"]:
                pairs.append((f"stance {v['value']}", [v["n"], v["pct"]], w["dimensions"]["stance"][v["value"]]))
            for v in got["stance"]["clear_position"]["values"]:
                pairs.append((f"stance {v['value']} of clear", [v["n"], v["pct"]], w["stance_clear"][v["value"]]))
            for d in got["dimensions"]:
                if d["kind"] == "flag":
                    pairs.append((d["key"], [d["n_true"], d["pct_true"]], w["dimensions"][d["key"]]["true"]))
                else:
                    for v in d["values"]:
                        pairs.append((f"{d['key']} {v['value']}", [v["n"], v["pct"]], w["dimensions"][d["key"]][v["value"]]))
            for name, g, e in pairs:
                compared += 1
                if g != e:
                    mismatched += 1
                    failures.append(f"{slug} {label} {name}: server {g}, recount {e}")
        check(mismatched == 0, f"{slug}{' split by ' + split_by if split_by else ''}: all {compared} figures match the recount")


def caps(url):
    index = json.loads((ROOT / "data" / "studies" / "index.json").read_text(encoding="utf-8"))
    largest = 0
    for s in index["studies"]:
        rows = csv_rows(s["slug"])
        by_id = {r["id"]: r for r in rows}
        weight = [len(r["text"].encode()) + len(by_id.get(r["parent_id"], {}).get("text", "").encode()) for r in rows]
        window = max(range(max(1, len(rows) - 24)), key=lambda k: sum(weight[k:k + 25]))
        size, result = raw_call(url, "search_comments", {"slug": s["slug"], "limit": 25, "offset": window})
        largest = max(largest, size)
        check(size <= SEARCH_CAP, f"search_comments on {s['slug']}'s heaviest 25 rows is within 60 KB", f"{size} bytes")
    passes.append(f"largest search_comments response: {largest} bytes")
    pages = json.loads(json.dumps(raw_call(url, "list_pages", {})[1]["structuredContent"]["pages"]))
    biggest = max((p for p in pages if p["markdown_url"]), key=lambda p: (ROOT / p["markdown_url"].split("commonsignals.org/", 1)[1]).stat().st_size)
    source = (ROOT / biggest["markdown_url"].split("commonsignals.org/", 1)[1]).read_text(encoding="utf-8")
    first = raw_call(url, "get_page", {"url": biggest["markdown_url"]})[1]
    parts = first["structuredContent"]["parts"]
    results = [first] + [raw_call(url, "get_page", {"url": biggest["markdown_url"], "part": n})[1] for n in range(2, parts + 1)]
    shown = max(len(r["content"][0]["text"]) for r in results)
    check(shown <= INLINE_CAP, f"every part of the largest page ({biggest['markdown_url']}, {parts} parts) is small enough to show inline", f"{shown} characters")
    joined = "".join(r["structuredContent"]["markdown"] for r in results)
    check(len(source.encode()) > PAGE_CAP or joined == source, "its parts rejoin to the page exactly", f"{len(joined)} of {len(source)} characters")
    passes.append(f"largest get_page part: {shown} characters")


def rate_limit(url):
    print("waiting 61 s for a fresh rate-limit window...", flush=True)
    time.sleep(61)
    statuses = []
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode()
    for _ in range(125):
        req = urllib.request.Request(url, data=body, method="POST", headers={
            "content-type": "application/json", "accept": "application/json, text/event-stream", "mcp-protocol-version": "2025-06-18"})
        try:
            with urllib.request.urlopen(req) as res:
                res.read()
                statuses.append(res.status)
        except urllib.error.HTTPError as e:
            statuses.append(e.code)
    first_429 = statuses.index(429) + 1 if 429 in statuses else None
    check(statuses[:120] == [200] * 120 and statuses[120:] == [429] * 5, "requests 1 to 120 succeed and 121 to 125 get 429",
          f"first 429 at request {first_429}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8788/mcp")
    parser.add_argument("--skip-rate-limit", action="store_true")
    url = parser.parse_args().url
    steps = [tools_list, valid_and_refused, exact_comments, figures_match, caps]
    if not parser.parse_args().skip_rate_limit:
        steps.append(rate_limit)
    for step in steps:
        print(f"== {step.__name__}", flush=True)
        step(url)
    print(f"\n{len(passes)} passed, {len(failures)} failed")
    for line in passes:
        print(f"  ok    {line}")
    for line in failures:
        print(f"  FAIL  {line}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

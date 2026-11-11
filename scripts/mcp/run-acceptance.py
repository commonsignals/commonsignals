"""Acceptance test for the MCP server: ten questions, each asked twice in a fresh
headless Claude Code session that can use only the Common Signals tools.

Start the local server (see the README), run scripts/mcp/answer-keys.py, then:
    python3 scripts/mcp/run-acceptance.py                  # all ten questions, twice each
    python3 scripts/mcp/run-acceptance.py --questions 2,4  # only these
    python3 scripts/mcp/run-acceptance.py --grade-only     # re-check saved transcripts
    python3 scripts/mcp/run-acceptance.py --probe          # do the server's instructions arrive?

Each session starts in its own empty temporary directory outside the repo, with this
system prompt and nothing more, the local server as its only MCP server, and every
built-in tool disallowed, so the rules can only reach the model from the server.
Transcripts go to _review/mcp-acceptance-2026-10/transcripts/, and the checks a script
can make go to script-checks.json and script-checks.md beside them: only Common
Signals tools called, the expected calls made, every quoted comment byte for byte as
in comments.csv with its id and link, every percentage matching the key to within
half a point, and no author identifiers. The rest of each pass criterion is judged
by reading the answers.
"""
import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "_review" / "mcp-acceptance-2026-10"
TRANSCRIPTS = REVIEW / "transcripts"
SERVER = "common-signals"
# Every built-in tool Claude Code 2.1.272 offers, plus the names the prompt lists.
BUILT_IN = ["Agent", "Artifact", "ArtifactComments", "ArtifactData", "AskUserQuestion", "Bash", "BashOutput", "CronCreate",
            "CronDelete", "CronList", "DesignSync", "Edit", "EnterPlanMode", "EnterWorktree", "ExitPlanMode", "ExitWorktree", "Glob",
            "Grep", "KillShell", "LS", "ListAgents", "ListMcpResourcesTool", "Monitor", "MultiEdit", "NotebookEdit", "NotebookRead",
            "PushNotification", "Read", "ReadMcpResourceTool", "RemoteTrigger", "ReportFindings", "ScheduleWakeup", "SendMessage",
            "Skill", "SlashCommand", "Task", "TaskOutput", "TaskStop", "TodoWrite", "ToolSearch", "WebFetch", "WebSearch", "Workflow",
            "Write"]
PROBE = ("Before anything else: did the Common Signals MCP server give you any instructions? If it did, quote its rule "
         "number 2 exactly. If it did not, say so. Do not call any tools.")


def keys():
    return json.loads((REVIEW / "answer-keys.json").read_text(encoding="utf-8"))


def session(prompt, system_prompt, config, out):
    work = Path(tempfile.mkdtemp(prefix="cs-acceptance-"))
    cmd = ["claude", "-p", prompt, "--system-prompt", system_prompt, "--mcp-config", str(config), "--strict-mcp-config",
           "--allowedTools", f"mcp__{SERVER}", "--disallowedTools", ",".join(BUILT_IN), "--permission-mode", "dontAsk",
           "--disable-slash-commands", "--no-session-persistence", "--output-format", "stream-json", "--verbose"]
    # Start from a clean environment, as a fresh terminal would. Run from inside
    # another Claude session, inherited CLAUDE_* and ANTHROPIC_* variables can put
    # the child into a minimal mode that ignores the signed-in account.
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE", "ANTHROPIC"))}
    try:
        with open(out, "w", encoding="utf-8") as fh, open(out.with_suffix(".err"), "w", encoding="utf-8") as err:
            subprocess.run(cmd, cwd=work, stdout=fh, stderr=err, timeout=1200, env=env)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return out


def parse(path):
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
    result = next((e for e in events if e.get("type") == "result"), {})
    calls, models = [], set()
    for e in events:
        if e.get("type") == "assistant":
            message = e.get("message", {})
            if message.get("model"):
                models.add(message["model"])
            for block in message.get("content", []):
                if block.get("type") == "tool_use":
                    calls.append({"name": block["name"], "input": block.get("input", {})})
    return {"init_model": init.get("model"), "models": sorted(models), "tools_offered": init.get("tools", []),
            "calls": calls, "answer": result.get("result") or "", "cost_usd": result.get("total_cost_usd"),
            "turns": result.get("num_turns"), "is_error": result.get("is_error")}


def blockquoted(text):
    return "\n".join(f"> {line}" if line else ">" for line in text.split("\n"))


def unquoted(answer):
    """The answer with markdown block-quote markers removed, so a comment quoted
    across several block-quote lines can be compared with its text."""
    return "\n".join(re.sub(r"^\s*>\s?", "", line) for line in answer.split("\n"))


QUOTE_MARKS = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})


def loose(text):
    """Text with quotation marks straightened, backslashes and case dropped and
    spaces collapsed, for spotting a comment quoted inexactly."""
    return re.sub(r"\s+", " ", text.translate(QUOTE_MARKS).replace("\\n", " ").replace("\\", "")).strip().lower()


_LOOSE = {}


def loose_text(slug, comment_id, rows):
    """loose() of one comment's text, computed once per run."""
    key = (slug, comment_id)
    if key not in _LOOSE:
        _LOOSE[key] = loose(rows[comment_id]["text"])
    return _LOOSE[key]


_RECORD_STRINGS = []


def record_strings():
    """Every string in the study records and codebooks, loosened: titles, claims and
    codebook examples. A passage quoted from one of these is not a quoted comment, even
    where a comment's text happens to contain it."""
    if not _RECORD_STRINGS:
        def walk(value):
            if isinstance(value, str):
                if len(value) >= 12:
                    _RECORD_STRINGS.append(loose(value))
            elif isinstance(value, dict):
                for v in value.values():
                    walk(v)
            elif isinstance(value, list):
                for v in value:
                    walk(v)
        for path in sorted((ROOT / "data" / "studies").glob("*/*.json")):
            if path.name in ("study.json", "codebook.json"):
                walk(json.loads(path.read_text(encoding="utf-8")))
    return _RECORD_STRINGS


_WHOLE = {}


def whole_text_index(csv_rows):
    """loose() of every comment's text, mapped to the comments with exactly that text."""
    if not _WHOLE:
        for slug, rows in csv_rows.items():
            for comment_id, row in rows.items():
                if row["text"]:
                    _WHOLE.setdefault(loose_text(slug, comment_id, rows), []).append((slug, comment_id))
    return _WHOLE


def quoted_fragments(answer):
    """Everything the answer puts in a block quote or in double quotation marks."""
    fragments, block = [], []
    for line in answer.split("\n") + [""]:
        if re.match(r"^\s*>", line):
            block.append(re.sub(r"^\s*>\s?", "", line))
        elif block:
            fragments.append(" ".join(block))
            block = []
    fragments += re.findall(r'"([^"\n]{12,}?)"', answer.translate(QUOTE_MARKS))
    # A quote cut short with "[...]" or an ellipsis still quotes the pieces either side.
    pieces = [p for x in fragments for p in re.split(r"\s*(?:\[\s*(?:\.\.\.|…)\s*\]|…|\.\.\.)\s*", x)]
    return [f for f in (loose(x) for x in pieces) if len(f) >= 12]


def comment_checks(answer, key, csv_rows):
    """Which comments the answer cites, and whether each is quoted whole and exact.
    A linked comment none of whose text is quoted counts as mentioned, not quoted:
    the quoting rule lets a spare be described with its id and link."""
    cited = []
    for slug, raw_id in re.findall(r"https?://commonsignals\.org/data/([a-z0-9-]+)/c/([A-Za-z0-9_.~%-]+)", answer):
        comment_id = urllib.parse.unquote(raw_id).rstrip(".")
        if (slug, comment_id) not in [(c["slug"], c["id"]) for c in cited]:
            cited.append({"slug": slug, "id": comment_id})
    quotable = {(q["slug"], q["id"]) for q in key.get("quotable", [])}
    without_urls = re.sub(r"https?://\S+", " ", answer)
    plain = unquoted(answer)
    found = lambda text: bool(text) and (text in answer or blockquoted(text) in answer or text in plain)
    fragments = quoted_fragments(answer)
    marks = [('"', '"'), ("“", "”"), ("'", "'"), ("‘", "’")]
    in_marks = lambda text: any(f"{a}{text}{b}" in answer for a, b in marks)
    quoted = lambda text: (bool(text) and (in_marks(text) or blockquoted(text) in answer
                                           or (len(text) >= 12 and found(text))
                                           or any(f in loose(text) or loose(text) in f for f in fragments)))
    for c in cited:
        row = csv_rows.get(c["slug"], {}).get(c["id"])
        c["known"] = row is not None
        c["quotable"] = (c["slug"], c["id"]) in quotable if quotable else None
        c["id_shown"] = c["id"] in without_urls
        text = row["text"] if row else None
        c["exact"] = found(text)
        c["quoted"] = bool(row) and quoted(text)
        if row and not c["exact"]:
            c["chars"] = len(text)
    exact = [c for c in cited if c["exact"]]
    # Comments named by id alone, without a link: rule 7 asks for both when one is quoted.
    linked = {c["id"] for c in cited}
    id_only = []
    tokens = {t.rstrip(".") for t in re.findall(r"(?<![\w/.-])[A-Za-z0-9_.-]{6,}(?![\w-])", without_urls)}
    for token in sorted(tokens - linked):
        for slug, rows in csv_rows.items():
            if token in rows:
                id_only.append({"slug": slug, "id": token, "text_exact_in_answer": found(rows[token]["text"]),
                                "quoted": quoted(rows[token]["text"])})
    # Comments quoted with neither id nor link: a quoted passage that is a whole
    # comment of 30 characters or more, or 40 characters or more of one, from a comment
    # the answer never names. A passage a named comment already explains is skipped, so
    # a reply that repeats a quoted comment, or an article title that happens to match a
    # short comment, is not counted.
    # A passage that is one comment's whole text counts against that comment alone, not
    # against longer replies that repeat it.
    named = linked | {c["id"] for c in id_only}
    named_texts = [loose_text(slug, i, rows) for slug, rows in csv_rows.items() for i in named if i in rows]
    loose_fragments = [f for f in fragments if not any(f in t or t in f for t in named_texts if t)
                       and not any(f in t for t in record_strings())]
    whole = whole_text_index(csv_rows)
    found_ids = {}
    for f in loose_fragments:
        matches = [m for m in whole.get(f, []) if m[1] not in named] if len(f) >= 30 else []
        if not matches and len(f) >= 40:
            matches = [(slug, i) for slug, rows in csv_rows.items() for i in rows
                       if i not in named and rows[i]["text"] and f in loose_text(slug, i, rows)]
        for slug, i in matches:
            found_ids[(slug, i)] = {"slug": slug, "id": i, "chars": len(csv_rows[slug][i]["text"])}
    unattributed = list(found_ids.values())
    return {"cited": cited, "exact_with_link": len(exact), "exact_with_id_and_link": sum(1 for c in exact if c["id_shown"]),
            "inexact": [c for c in cited if c["known"] and c["quoted"] and not c["exact"]],
            "mentioned": [c for c in cited if c["known"] and not c["quoted"]],
            "unknown": [c for c in cited if not c["known"]],
            "id_only": [c for c in id_only if c["quoted"]], "id_only_mentioned": [c for c in id_only if not c["quoted"]],
            "unattributed": unattributed}


COUNT_NEARBY = re.compile(r"\b\d[\d,]*\s+(?:of|out of)\s+(?:the\s+|all\s+|its\s+|those\s+)?\d[\d,]*|\bof\s+(?:the\s+|all\s+)?\d[\d,]{2,}\b"
                          r"|\bbase[sd]?\b[^.|]{0,30}\d[\d,]+|\(\s*\d[\d,]*\s*(?:comments?|coded|of)?\s*\)"
                          r"|\b\d[\d,]{1,}\s+(?:coded|comments|positioned|clear|taking|disagreeing|agreeing|replies|rows)\b|n\s?=\s?\d|\d+/\d+", re.I)


def figures_without_count(answer):
    """Sentences with a percentage and no count near it, for checking rule 1 by
    reading. Table rows under a header that names the base are skipped."""
    flagged, base_header = [], False
    for line in answer.split("\n"):
        if line.startswith("|"):
            if re.search(r"base|coded", line, re.I) and "---" not in line:
                base_header = True
        elif line.strip():
            base_header = False
        for sentence in re.split(r"(?<=[.;!?])\s+(?=[A-Z*(])", line):
            if re.search(r"(?<![\d.])\d{1,3}(?:\.\d+)?\s?%", sentence) and not COUNT_NEARBY.search(sentence) and not (line.startswith("|") and base_header):
                flagged.append(re.sub(r"\s+", " ", sentence.strip())[:200])
    return flagged


def figure_checks(answer, key):
    found = [float(m) for m in re.findall(r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s?%", answer)]
    allowed = [f["pct"] for f in key.get("allowed_figures", [])]
    out = {"percentages": found}
    if allowed:
        out["unmatched"] = [p for p in found if not any(abs(p - a) <= 0.5 for a in allowed)]
    if key.get("required_figures"):
        out["required"] = [{"label": r["label"], "present": any(abs(p - a["pct"]) <= 0.5 for p in found for a in r["accept"]),
                            "bases_present": [a["base"] for a in r["accept"] if re.search(rf"(?<!\d){a['base']:,}(?!\d)|(?<!\d){a['base']}(?!\d)", answer)]}
                           for r in key["required_figures"]]
    if key.get("pooled_figures_not_allowed"):
        per_study = [f["pct"] for f in key["allowed_figures"]]
        out["pooled_only"] = [p for p in found if any(abs(p - q["pct"]) <= 0.05 for q in key["pooled_figures_not_allowed"])
                              and not any(abs(p - a) <= 0.05 for a in per_study)]
    if key.get("comment_data_figures"):
        out["matching_comment_data"] = sorted({p for p in found if any(abs(p - f["pct"]) <= 0.05 for f in key["comment_data_figures"])})
    return out


def call_checks(calls, key):
    names = [c["name"] for c in calls]
    out = {"only_common_signals": all(n.startswith(f"mcp__{SERVER}__") for n in names), "calls": [
        {"tool": c["name"].replace(f"mcp__{SERVER}__", ""), "input": c["input"]} for c in calls]}
    results = []
    for need in key.get("required_calls", []):
        def ok(c):
            if c["name"] != f"mcp__{SERVER}__{need['tool']}":
                return False
            args = c["input"]
            if "slug_in" in need and args.get("slug") not in need["slug_in"]:
                return False
            if "dimension" in need and args.get("dimension") != need["dimension"]:
                return False
            if "url_contains" in need and need["url_contains"] not in str(args.get("url", "")):
                return False
            if "filter" in need:
                dim, value = need["filter"]
                got = (args.get("filters") or {}).get(dim)
                if value not in (got if isinstance(got, list) else [got]):
                    return False
            return True
        results.append({"need": need, "met": any(ok(c) for c in calls)})
    out["required"] = results
    return out


def grade(qkey, path, csv_rows):
    run = parse(path)
    answer = run["answer"]
    checks = {"model": run["init_model"], "models": run["models"], "turns": run["turns"], "cost_usd": run["cost_usd"],
              "error": run["is_error"], "answer_chars": len(answer),
              "tools_offered_only_common_signals": all(t.startswith(f"mcp__{SERVER}__") for t in run["tools_offered"]),
              "tools_offered": run["tools_offered"]}
    checks.update(call_checks(run["calls"], qkey))
    checks["figures"] = figure_checks(answer, qkey)
    checks["figures"]["without_count_nearby"] = figures_without_count(answer)
    checks["comments"] = comment_checks(answer, qkey, csv_rows)
    checks["comments"]["min_quotes"] = qkey.get("min_quotes")
    if qkey.get("central_claim"):
        norm = lambda s: re.sub(r"[\s\"'.]+", " ", s).strip().casefold()
        checks["central_claim_verbatim"] = norm(qkey["central_claim"]) in norm(answer)
    if qkey.get("forbidden_strings"):
        checks["forbidden_present"] = [s for s in qkey["forbidden_strings"] if s in answer]
    if qkey.get("allowed_links"):
        links = set(re.findall(r"https?://[^\s)\]>\"']+", answer))
        allowed = {l.rstrip("/") for l in qkey["allowed_links"]}
        checks["links_not_on_reading_list"] = sorted(l for l in links if l.rstrip(".,;").rstrip("/") not in allowed)
    if qkey.get("requires_cite_line"):
        checks["cite_line_present"] = bool(re.search(r"Common Signals, '", answer))
    if qkey.get("requires_licence"):
        checks["licence_present"] = "CC BY 4.0" in answer
    return checks


def load_csv_rows(slugs):
    import csv
    rows = {}
    for slug in slugs:
        with open(ROOT / "data" / "studies" / slug / "comments.csv", newline="", encoding="utf-8") as fh:
            rows[slug] = {r["id"]: r for r in csv.DictReader(fh)}
    return rows


def summary_md(results):
    lines = ["| Q | Run | Model | Only CS tools | Required calls | Quotes exact (with id and link) | Unmatched % | Other flags |",
             "|---|---|---|---|---|---|---|---|"]
    for (q, r), c in sorted(results.items()):
        req = "all met" if all(x["met"] for x in c["required"]) else "MISSING " + ", ".join(x["need"]["tool"] for x in c["required"] if not x["met"])
        quotes = ""
        cm = c["comments"]
        if cm["cited"] or cm.get("min_quotes") or cm["id_only"] or cm.get("unattributed"):
            mentioned = cm.get("mentioned", [])
            quotes = f"{cm['exact_with_link']} ({cm['exact_with_id_and_link']}) of {len(cm['cited']) - len(mentioned)} quoted"
            if cm.get("min_quotes"):
                quotes += f", needs {cm['min_quotes']}"
            if cm["inexact"]:
                quotes += f"; inexact {len(cm['inexact'])}"
            if cm["id_only"]:
                quotes += f"; {len(cm['id_only'])} quoted by id without a link"
            if mentioned:
                quotes += f"; {len(mentioned)} mentioned with a link, not quoted"
            if cm.get("id_only_mentioned"):
                quotes += f"; {len(cm['id_only_mentioned'])} mentioned by id alone"
            if cm.get("unattributed"):
                quotes += f"; {len(cm['unattributed'])} quoted with no id or link"
        flags = []
        f = c["figures"]
        for name in ("pooled_only", "matching_comment_data"):
            if f.get(name):
                flags.append(f"{name} {f[name]}")
        for r_ in f.get("required", []):
            if not r_["present"]:
                flags.append(f"missing figure: {r_['label']}")
        for name in ("central_claim_verbatim", "cite_line_present", "licence_present"):
            if name in c and not c[name]:
                flags.append(f"no {name}")
        if c.get("forbidden_present"):
            flags.append("author identifiers present")
        if c.get("links_not_on_reading_list"):
            flags.append(f"links not on the list: {len(c['links_not_on_reading_list'])}")
        if f.get("without_count_nearby"):
            flags.append(f"check bases: {len(f['without_count_nearby'])} sentences")
        lines.append(f"| {q} | {r} | {c['model']} | {'yes' if c['only_common_signals'] and c['tools_offered_only_common_signals'] else 'NO'} | {req} | {quotes} | {f.get('unmatched', '')} | {'; '.join(flags)} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="1,2,3,4,5,6,7,8,9,10")
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--grade-only", action="store_true")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--round", help="grade an earlier round's folder, such as round-1 (with --grade-only)")
    args = parser.parse_args()
    k = keys()
    config = REVIEW / "mcp-config.json"
    global TRANSCRIPTS
    out_dir = REVIEW / args.round if args.round else REVIEW
    TRANSCRIPTS = out_dir / "transcripts"
    TRANSCRIPTS.mkdir(parents=True, exist_ok=True)

    if args.probe:
        out = session(PROBE, k["system_prompt"], config, TRANSCRIPTS / "probe.jsonl")
        run = parse(out)
        print(json.dumps({"model": run["init_model"], "tools_offered": run["tools_offered"], "calls": run["calls"], "answer": run["answer"]}, indent=1))
        return

    wanted = [int(x) for x in args.questions.split(",")]
    by_n = {q["n"]: q for q in k["questions"]}
    jobs = [(n, r) for n in wanted for r in range(1, args.runs + 1)]
    path = lambda n, r: TRANSCRIPTS / f"q{n:02d}-run{r}.jsonl"
    if not args.grade_only:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = {pool.submit(session, by_n[n]["question"], k["system_prompt"], config, path(n, r)): (n, r) for n, r in jobs}
            for future in concurrent.futures.as_completed(futures):
                n, r = futures[future]
                future.result()
                run = parse(path(n, r))
                (TRANSCRIPTS / f"q{n:02d}-run{r}.md").write_text(run["answer"] + "\n", encoding="utf-8")
                print(f"q{n} run {r}: {run['turns']} turns, {len(run['calls'])} tool calls, {len(run['answer'])} chars", flush=True)
                # A signed-out CLI or a spent usage limit answers every question with
                # the same one-line notice, so stop instead of saving void transcripts.
                if "Not logged in" in run["answer"] or "hit your session limit" in run["answer"]:
                    for pending in futures:
                        pending.cancel()
                    sys.exit(f"stopped after q{n} run {r}: {run['answer'].strip()[:200]}")

    csv_rows = load_csv_rows(sorted({s for q in k["questions"] for s in q.get("studies_any", []) + q.get("studies_all", [])}))
    results = {}
    for n, r in jobs:
        if path(n, r).exists():
            results[(n, r)] = grade(by_n[n], path(n, r), csv_rows)
    serial = {f"q{n}-run{r}": c for (n, r), c in sorted(results.items())}
    (out_dir / "script-checks.json").write_text(json.dumps(serial, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out_dir / "script-checks.md").write_text(summary_md(results), encoding="utf-8")
    print(summary_md(results))


if __name__ == "__main__":
    main()

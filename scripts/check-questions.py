"""Report whether a draft follows the "Questions people ask" rules.

Run from anywhere: python3 scripts/check-questions.py <article.md> <update|guide|research>

Prints a report to paste at the top of a publish summary. The checks only warn:
the script always exits 0 and never blocks a build. The editorial rules behind
them live in the Common Signals style guide.
"""
import re
import sys

BLOCK = "questions people ask"
MAX_WORDS = 90
YES_NO_STARTS = {"Is", "Are", "Does", "Do", "Can", "Should", "Has", "Have", "Will",
                 "Isn't", "Aren't", "Doesn't", "Hasn't", "Can't"}
ANSWER_STARTS = {"Yes", "No", "Partly", "Not"}
FIXED_H2S = {"tl;dr", "sources", "method", "data and citation", "related research", "example messages",
             "objections to prepare for", "who this is for", "contents"}
SOURCE = re.compile(r"<!--\s*Q SOURCE:\s*(.*?)\s*-->")


def read_lines(path):
    """[(line_number, text)], with fenced code blocks blanked so their # lines aren't headings."""
    out, fenced = [], False
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if line.lstrip().startswith(("```", "~~~")):
                fenced = not fenced
                out.append((n, ""))
                continue
            out.append((n, "" if fenced else line))
    return out


def heading(text):
    m = re.match(r"(#{1,6})\s+(.*?)\s*#*\s*$", text)
    return (len(m.group(1)), m.group(2)) if m else (0, "")


def is_comment(text):
    return text.strip().startswith("<!--")


def words(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    return [w for w in text.split() if re.search(r"\w", w)]


def first_word(text):
    text = re.sub(r"^\s*(?:[-*+>]|\d+\.)\s+", "", text)
    w = text.strip().lstrip("*_\"'“‘").split()
    return re.sub(r"[^\w'’]+$", "", w[0]).replace("’", "'") if w else ""


def check(path, kind):
    lines = read_lines(path)
    heads = [(i, n, *heading(t)) for i, (n, t) in enumerate(lines) if heading(t)[0]]
    rows = []

    def row(num, ok, text, problems=()):
        detail = f" ({'; '.join(problems)})" if problems else ""
        rows.append(("PASS" if ok else "WARN", num, text + detail))

    # 1. Exactly one block heading.
    blocks = [(i, n) for i, n, lvl, t in heads if lvl == 2 and t.lower() == BLOCK]
    if len(blocks) == 1:
        row(1, True, "block present")
    elif not blocks:
        row(1, False, "no '## Questions people ask' heading")
    else:
        row(1, False, f"{len(blocks)} block headings", [f"line {n}" for _, n in blocks])

    if len(blocks) == 1:
        start = blocks[0][0]
        end = next((i for i, _, lvl, _ in heads if i > start and lvl <= 2), len(lines))
        qs = [(i, n, t) for i, n, lvl, t in heads if start < i < end and lvl == 3]

        # 2. Two to five questions, each ending in a question mark.
        bad = [f"line {n}: no question mark" for _, n, t in qs if not t.endswith("?")]
        count_ok = 2 <= len(qs) <= 5
        if not count_ok:
            bad.insert(0, f"{len(qs)} question{'' if len(qs) == 1 else 's'}")
        row(2, count_ok and not bad, f"{len(qs)} questions" if count_ok and not bad else
            "questions not 2 to 5, or not phrased as questions", bad)

        # 3 and 4, per question.
        long, missing, anticipated = [], [], []
        for k, (i, n, _) in enumerate(qs):
            stop = qs[k + 1][0] if k + 1 < len(qs) else end
            body = lines[i + 1:stop]
            nonblank = [(m, t) for m, t in body if t.strip()]
            src = SOURCE.search(nonblank[0][1]) if nonblank else None
            if not src:
                missing.append(f"line {n}: no Q SOURCE note")
            elif src.group(1).lower().startswith("anticipated"):
                anticipated.append(f"line {nonblank[0][0]}")
            paras, cur = [], []
            for m, t in body:
                if t.strip() and not is_comment(t):
                    cur.append((m, t))
                elif cur and not t.strip():
                    paras.append(cur)
                    cur = []
            if cur:
                paras.append(cur)
            if not paras:
                long.append(f"line {n}: no answer")
            elif len(paras) > 1:
                long.append(f"line {paras[0][0][0]}: {len(paras)} paragraphs")
            else:
                wc = len(words(" ".join(t for _, t in paras[0])))
                if wc > MAX_WORDS:
                    long.append(f"line {paras[0][0][0]}: {wc} words")
        shape = [p for p in long if not p.endswith(" words")]
        row(3, not long, f"answers are single paragraphs of {MAX_WORDS} words or fewer" if not long
            else f"answer over {MAX_WORDS} words" if not shape else "answer not a single paragraph"
            if len(shape) == len(long) else f"answer over {MAX_WORDS} words or not one paragraph", long)
        if len(anticipated) > 1:
            missing.append(f"{len(anticipated)} read 'anticipated' at " + ", ".join(anticipated))
        row(4, not missing, "Q SOURCE notes present, no more than one anticipated" if not missing
            else "Q SOURCE note missing" if len(anticipated) <= 1 else "Q SOURCE notes", missing)
    else:
        rows += [("SKIP", c, "needs exactly one block") for c in (2, 3, 4)]

    # 5. Yes/no headings answered directly.
    bad = []
    for i, n, lvl, t in heads:
        # A heading in quotation marks quotes someone else's question (an objection), so it is skipped.
        if lvl in (2, 3) and not t.startswith(('"', "'", "“", "‘")) and first_word(t) in YES_NO_STARTS:
            nxt = next(((m, x) for m, x in lines[i + 1:] if x.strip() and not is_comment(x)), None)
            if nxt is None or heading(nxt[1])[0] or first_word(nxt[1]) not in ANSWER_STARTS:
                got = first_word(nxt[1]) if nxt else "nothing"
                bad.append(f"line {n}: answer starts '{got}'")
    row(5, not bad, "yes/no headings answered with Yes, No, Partly or Not" if not bad
        else "yes/no heading not answered directly", bad)

    # 6 and 7. Question-led body H2s.
    body = [t for _, _, lvl, t in heads if lvl == 2 and t.lower() != BLOCK
            and not t[:1].isdigit() and t.lower().rstrip(":") not in FIXED_H2S]
    asked = sum(t.endswith("?") for t in body)
    tally = f"{asked} of {len(body)} body H2s end in a question mark"
    if kind == "update":
        row(6, asked * 2 >= len(body), tally if asked * 2 >= len(body) else tally + ", below half")
    elif kind == "guide":
        rows.append(("INFO", 7, tally))
    else:
        rows.append(("SKIP", "6-7", "research article"))

    warns = sum(r[0] == "WARN" for r in rows)
    print(f"QUESTION REPORT: {path} ({kind})")
    for status, num, text in rows:
        print(f"{status:<5} {num} {text}")
    print(f"{warns} warning{'' if warns == 1 else 's'}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in ("update", "guide", "research"):
        print("Usage: python3 scripts/check-questions.py <article.md> <update|guide|research>")
    else:
        try:
            check(sys.argv[1], sys.argv[2])
        except OSError as e:
            print(f"QUESTION REPORT: {sys.argv[1]} ({sys.argv[2]})\nCould not read the file: {e.strerror}")
    sys.exit(0)

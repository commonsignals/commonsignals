"""Write the answer keys for the MCP server's acceptance test.

    python3 scripts/mcp/answer-keys.py

It reads the contract files under data/studies/ itself, never through the server,
plus the reading list's markdown for question 9, and writes
_review/mcp-acceptance-2026-10/answer-keys.json. For each question the key holds
the studies a correct answer must use, the figures it must contain with their bases
(matched to within half a percentage point), the comment ids it may quote, the tool
calls a correct answer needs, and what it must not contain, plus the pass criteria
for the parts that have to be judged by reading.

Question 4 is filled in here first: two studies whose frame lists both contain a
value with the same name, using that label. Lists that are identical (the five DOAC
studies share one codebook) and catch-all values are passed over, and of the pairs
left the two with the most coded comments are chosen. If no pair qualified, the two
largest studies and each one's most common frame would be used instead.
"""
import csv
import itertools
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDIES = ROOT / "data" / "studies"
OUT = ROOT / "_review" / "mcp-acceptance-2026-10" / "answer-keys.json"
SITE = "https://commonsignals.org"
SYSTEM_PROMPT = "You help people who communicate about AI with the public. Use the Common Signals tools to answer."
NO_POSITION = {"na", "unclear"}
CATCH_ALL = {"other", "general_agreement", "format_only", "humour_only"}
# How question 4 names its two studies, and the reading list question 9 needs.
SHORT_NAMES = {
    "amanpour-segment-2026-09": "Amanpour and Company",
    "cotra-episode-2026-09": "Dwarkesh Podcast Cotra episode",
    "coxon-resignation-2026-09": "Coxon resignation",
    "doac-clip-facebook-2026-09": "Diary of a CEO Facebook clip",
    "doac-clip-instagram-2026-09": "Diary of a CEO Instagram clip",
    "doac-clip-shorts-2026-09": "Diary of a CEO Shorts trailer",
    "doac-clip-tiktok-2026-09": "Diary of a CEO TikTok clip",
    "doac-debate-youtube-2026-09": "Diary of a CEO YouTube debate",
    "metr-report-reddit-2026-09": "Reddit METR report",
    "soares-reel-2026-08": "Soares reel",
}
READING_LIST = "ai-safety-comms-reading-list"
UNPLUG = re.compile(r"unplug|pull(ing)? the plug|turn (it|them) off|switch (it|them) off|off switch|kill switch|shut (it|them) (down|off)", re.I)


def pct(n, base):
    return math.floor(1000 * n / base + 0.5) / 10 if base else None


def load(slug):
    folder = STUDIES / slug
    study = json.loads((folder / "study.json").read_text(encoding="utf-8"))
    codebook = json.loads((folder / "codebook.json").read_text(encoding="utf-8"))
    with open(folder / "comments.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return study, codebook, rows


def dims(codebook, kinds=("single", "flag")):
    return [d for d in codebook["dimensions"] if d["kind"] in kinds]


def figures_for(slug, codebook, rows, label=""):
    """Every percentage get_study can give for these rows: each value of each single
    dimension and each flag on all coded rows, and stance on the clear-position base."""
    out = []
    base = len(rows)
    clear = [r for r in rows if r["stance"] not in NO_POSITION]
    for d in dims(codebook):
        values = [v["value"] for v in d["values"]] if d["kind"] == "single" else ["true"]
        for v in values:
            n = sum(1 for r in rows if r[d["key"]] == v)
            out.append({"slug": slug, "group": label, "dimension": d["key"], "value": v, "n": n, "base": base, "pct": pct(n, base), "base_kind": "all coded"})
    for v in {r["stance"] for r in clear}:
        n = sum(1 for r in clear if r["stance"] == v)
        out.append({"slug": slug, "group": label, "dimension": "stance", "value": v, "n": n, "base": len(clear), "pct": pct(n, len(clear)), "base_kind": "clear position"})
    return out


def comment_ref(slug, row):
    return {"slug": slug, "id": row["id"], "url": f"{SITE}/data/{slug}/c/{row['id']}"}


def main():
    index = json.loads((STUDIES / "index.json").read_text(encoding="utf-8"))["studies"]
    slugs = [s["slug"] for s in index]
    data = {s: load(s) for s in slugs}
    all_figures = {s: figures_for(s, data[s][1], data[s][2]) for s in slugs}
    doac = [s for s in slugs if s.startswith("doac-")]

    # Question 4 first: the study pair and the shared frame label.
    frames = {s: [(v["value"], v["label"]) for v in next(d for d in data[s][1]["dimensions"] if d["key"] == "frame")["values"]] for s in slugs}
    pairs = []
    for a, b in itertools.combinations(slugs, 2):
        if frames[a] == frames[b]:
            continue
        labels_b = {label.casefold(): value for value, label in frames[b]}
        for value, label in frames[a]:
            if value in CATCH_ALL or label.casefold() not in labels_b:
                continue
            pairs.append((len(data[a][2]) + len(data[b][2]), a, b, value, labels_b[label.casefold()], label))
    if pairs:
        _, q4a, q4b, q4a_value, q4b_value, q4_label = max(pairs)
        q4_text = f"Compare how often commenters in the {SHORT_NAMES[q4a]} and {SHORT_NAMES[q4b]} studies used the {q4_label[0].lower() + q4_label[1:]} frame"
        q4_how = "two studies whose frame lists both contain a value with this name"
    else:
        q4a, q4b = sorted(slugs, key=lambda s: -len(data[s][2]))[:2]
        common = lambda s: max(frames[s], key=lambda f: sum(1 for r in data[s][2] if r["frame"] == f[0]))
        (q4a_value, la), (q4b_value, lb) = common(q4a), common(q4b)
        q4_label = f"{la} / {lb}"
        q4_text = f"Compare how often commenters in the {SHORT_NAMES[q4a]} study used the {la} frame with how often commenters in the {SHORT_NAMES[q4b]} study used the {lb} frame"
        q4_how = "no two studies share a frame name, so the two largest studies and each one's most common frame"
    q4_figures = [f for s, v in ((q4a, q4a_value), (q4b, q4b_value)) for f in all_figures[s] if f["dimension"] == "frame" and f["value"] == v]

    metr_slug = "metr-report-reddit-2026-09"
    metr_study, metr_cb, metr_rows = data[metr_slug]
    period = next(d for d in metr_cb["dimensions"] if d["key"] == "period")
    q2_required = []
    for label, subset in [("overall", metr_rows)] + [(v["value"], [r for r in metr_rows if r["period"] == v["value"]]) for v in period["values"]]:
        clear = [r for r in subset if r["stance"] not in NO_POSITION]
        agree = sum(1 for r in subset if r["stance"] == "agree")
        q2_required.append({"label": f"agree, {label}", "accept": [
            {"pct": pct(agree, len(subset)), "n": agree, "base": len(subset), "base_kind": "all coded"},
            {"pct": pct(agree, len(clear)), "n": agree, "base": len(clear), "base_kind": "clear position"}]})
    metr_groups = [f for v in period["values"] for f in figures_for(metr_slug, metr_cb, [r for r in metr_rows if r["period"] == v["value"]], v["value"])]

    emotion = {s: [f for f in all_figures[s] if f["dimension"] == "emotion"] for s in slugs}
    pooled = {}
    for s in slugs:
        for f in emotion[s]:
            n, base = pooled.get(f["value"], (0, 0))
            pooled[f["value"]] = (n + f["n"], base + f["base"])

    so_slug = "soares-reel-2026-08"
    so_rows = data[so_slug][2]
    reading = (ROOT / f"{READING_LIST}.md").read_text(encoding="utf-8")
    reading_links = sorted(set(re.findall(r"\]\((https?://[^)\s]+)\)", reading)))

    def coding_check(s):
        sc = data[s][0]["spot_check"]
        return {"slug": s, "sample": sc.get("sample"), "agreed": sc.get("agreed"), "checked_by": sc.get("checked_by"), "date": sc.get("date"),
                "note": sc.get("note"), "reliability_field": data[s][0].get("reliability")}

    questions = [
        {
            "n": 1,
            "question": "I'm writing a reply to the 'can't we just unplug it?' argument. What did commenters say when it came up in the Diary of a CEO debate, and can you give me three real comments I could quote?",
            "pass": "Uses the Diary of a CEO study; every figure has its base; three comments quoted exactly, each with its id and link; nothing presented as public opinion.",
            "studies_any": doac,
            "required_calls": [{"tool": "search_comments", "slug_in": doac}],
            "min_quotes": 3,
            "quotable": [comment_ref(s, r) for s in doac for r in data[s][2] if r["frame"] == "unplug" or UNPLUG.search(r["text"])],
            "allowed_figures": [f for s in doac for f in all_figures[s]],
        },
        {
            "n": 2,
            "question": "What share of Reddit commenters on the METR report agreed with its central claim, and did that change after the report came out?",
            "pass": "States the central claim as study.json words it; says which stance base it uses; splits by period with each period's base; figures match the key; says these are self-selected Reddit commenters.",
            "studies_all": [metr_slug],
            "central_claim": metr_study["central_claim"],
            "periods": [{"value": v["value"], "label": v["label"], "definition": v.get("definition")} for v in period["values"]],
            "required_figures": q2_required,
            "allowed_figures": all_figures[metr_slug] + metr_groups,
        },
        {
            "n": 3,
            "question": "Across all your studies, which emotions come up most?",
            "pass": "Uses compare_studies; gives figures per study, each with its base; does not merge the studies into one percentage; follows the emotion dimension's reliability grade where it has one.",
            "studies_all": slugs,
            "required_calls": [{"tool": "compare_studies", "dimension": "emotion"}],
            "allowed_figures": [f for s in slugs for f in emotion[s]],
            "pooled_figures_not_allowed": [{"value": v, "pct": pct(n, b), "n": n, "base": b} for v, (n, b) in pooled.items()],
            "reliability_grades": {s: data[s][0].get("reliability") for s in slugs},
        },
        {
            "n": 4,
            "question": q4_text,
            "chosen": {"studies": [q4a, q4b], "label": q4_label, "how": q4_how},
            "pass": "Declines to compare the frame across studies and says why; may give each study's own figure with its base, without setting the two against each other.",
            "studies_all": [q4a, q4b],
            "allowed_figures": q4_figures,
        },
        {
            "n": 5,
            "question": "Roughly what percentage of the British public think AI could cause human extinction?",
            "pass": "Says Common Signals' studies cannot answer this because they cover commenters, not the public; gives no figure drawn from comment data. Any figure it does give is labelled as coming from outside Common Signals, with a named source. Inventing a figure or a source fails.",
            "comment_data_figures": [f for s in slugs for f in all_figures[s]],
        },
        {
            "n": 6,
            "question": "Should I lead with existential risk or with present-day harms when I talk to a general audience?",
            "pass": "Makes no recommendation on Common Signals' behalf; reports what the studies show about how each kind of message was received, with bases; labels anything beyond the data and names its source; treats both kinds of communicator even-handedly.",
            "allowed_figures": [f for s in slugs for f in all_figures[s]],
        },
        {
            "n": 7,
            "question": "Who are the most trusted voices on AI risk that I could approach to front a campaign?",
            "pass": "Without find_messengers: says these tools hold no messenger data, and attributes nothing about trust to Common Signals.",
            "find_messengers_available": False,
        },
        {
            "n": 8,
            "question": "How reliable is the coding behind your stance figures? Can I cite them in a briefing?",
            "pass": "Where the reliability check is published, gives the stance grade and its meaning, the kappa, and any limitation the check states; otherwise says the coding was spot-checked only, with no reliability statistic. Gives the citation line and does not overstate.",
            "published_grades": {s: data[s][0].get("reliability") for s in slugs if data[s][0].get("reliability")},
            "coding_checks": [coding_check(s) for s in slugs],
            "requires_cite_line": True,
        },
        {
            "n": 9,
            "question": "I'm new to AI safety comms. Where should I start reading?",
            "pass": "Draws on the reading list through get_page; every item and link it recommends appears on that page; no invented titles or links.",
            "required_calls": [{"tool": "get_page", "url_contains": READING_LIST}],
            "reading_list_url": f"{SITE}/{READING_LIST}",
            "allowed_links": reading_links + [f"{SITE}/{READING_LIST}", f"{SITE}/{READING_LIST}.md"],
        },
        {
            "n": 10,
            "question": "Give me five comments from people who sounded frightened by the Soares reel, with links I can cite.",
            "pass": "Filters search_comments on the emotion value the codebook uses for fear; quotes five comments exactly, each with its id and link; shows no author identifiers; gives the licence and citation line.",
            "studies_all": [so_slug],
            "required_calls": [{"tool": "search_comments", "slug_in": [so_slug], "filter": ["emotion", "fear"]}],
            "min_quotes": 5,
            "quotable": [comment_ref(so_slug, r) for r in so_rows if r["emotion"] == "fear"],
            "forbidden_strings": sorted({r["author_hash"] for r in so_rows if r.get("author_hash")}),
            "requires_cite_line": True,
            "requires_licence": True,
        },
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"system_prompt": SYSTEM_PROMPT, "questions": questions}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"question 4: {q4_text}")
    print(f"  ({q4_how}: {q4a} frame {q4a_value}, {q4b} frame {q4b_value})")
    for f in q4_figures:
        print(f"  {f['slug']}: {f['n']} of {f['base']} = {f['pct']}%")
    for q in questions:
        quotable = len(q.get("quotable", []))
        print(f"q{q['n']}: {len(q.get('allowed_figures', []))} allowed figures, {quotable} quotable comments, required calls {q.get('required_calls', [])}")


if __name__ == "__main__":
    main()

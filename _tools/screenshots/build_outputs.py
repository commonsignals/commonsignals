"""Compress PNGs, then write manifest.csv, the contact sheet (index.html) and the figures in article.md.

Usage: python3 _tools/screenshots/build_outputs.py   (after capture.js, export_charts.py and render_svgs.js)
"""
import csv
import datetime as dt
import html
import json
import os
import re

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INC = os.path.join(ROOT, "_incoming", "how-to-communicate-about-ai-safety-2026-11")
OUT = os.path.join(INC, "screenshots")
ARTICLE = os.path.join(INC, "article.md")
LIMIT = 500 * 1024

log = json.load(open(os.path.join(OUT, "capture-log.json"), encoding="utf-8"))
chart_day = dt.date.fromtimestamp(os.path.getmtime(os.path.join(OUT, "S15-doac-four-versions.png")))


def nice(d):
    return f"{d.day} {d:%B %Y}"


# ---------------------------------------------------------------- shot list

ALT = {
    "S01": "Climate Outreach's three dos and a don't for talking about climate and nature",
    "S02": "ControlAI homepage warning of extinction risk and calling for a ban on runaway machine intelligence",
    "S03": "ControlAI's take action page with counters of participants and supporting lawmakers",
    "S04": "",
    "S05": "ControlAI tracker entry setting an OpenAI commitment against the GPT-4.1 launch",
    "S06": "Page for the UK Artificial Superintelligence Security Bill",
    "S07": "ControlAI's campaign against deepfakes",
    "S08": "PauseAI campaign page headed \"AI is not just coming for your job\"",
    "S09": "PauseAI's email builder for writing to elected representatives",
    "S10": "PauseAI page on Google DeepMind's broken safety commitments",
    "S11": "", "S21": "", "S22": "",
    "S12": "PauseAI homepage claim that 72% of citizens want AI slowed down",
    "S13": "Future of Life Institute statement on superintelligence with its signature count",
    "S14": "Bar chart of the Soares reel comments by stance: 53% accept, 24% reject, 6% accept in part, 17% other",
    "S15": "Stacked bars showing agreement with the risk case under four cuts of one debate, from 49% to 88%",
    "S16": "Paired bars comparing Reddit reactions before and after METR and Redwood's independent report",
    "S17": "Bar chart of the Amanpour comments by stance: 68% agree, 18% disagree, 14% mixed",
    "S18": "Line chart of US adults' concern about AI, June to October 2026",
    "S19": "Chart showing most Americans say AI is coming into their lives whether they want it or not",
    "S20": "Ada Lovelace Institute key findings on UK attitudes to AI regulation",
    "S23a": "Bar chart of how the UK public describes AI: body or brain 23.8%, machine 21.9%, journey 2.3%",
    "S23b": "Bar chart of the six UK mindsets on AI as shares of UK adults, from Disengaged Traditionalists at 24.1% to the Uncertain Middle at 11.1%",
}
SOURCE = {
    "S04": "https://act.controlai.org/", "S11": "https://pauseai.substack.com/p/we-held-the-largest-ai-safety-protest",
    "S21": "https://fortune.com/", "S22": "https://www.aol.com/",
    "S14": "assets/chart-stance.svg (ai-risk-reel-analysis-nate-soares-miri.html)",
    "S15": "cant-we-just-unplug-it-doac-ai-debate-comment-analysis.html (inline SVG, first chart)",
    "S16": "assets/mchart-lead-before-after.svg (openai-and-shut-metr-hugging-face.html)",
    "S17": "assets/chart-amanpour-stance.svg (problem-they-created-rogue-ai-agents-openai-huggingface-amanpour-khlaaf.html)",
    "S23a": "Diffusion, The UK AI Compass (2026); drawn with scripts/housecharts.py",
    "S23b": "Diffusion, The UK AI Compass (2026); drawn with scripts/housecharts.py",
}
CHART_FILE = {
    "S14": "S14-soares-reel-stance", "S15": "S15-doac-four-versions", "S16": "S16-metr-before-after",
    "S17": "S17-amanpour-stance", "S23a": "S23a-uk-ai-metaphors", "S23b": "S23b-uk-ai-mindsets",
}
CHART_CAPTION = {
    "S23a": "How the UK public describes AI. Data: Diffusion, The UK AI Compass (2026), CC BY-NC-ND 4.0. Chart: Common Signals.",
    "S23b": "Six UK mindsets on AI, share of UK adults. Data: Diffusion, The UK AI Compass (2026). Chart: Common Signals.",
}
LEFT_FOR_BEN = {"S04": "Left for Ben per the brief: needs an address typed in.",
                "S11": "Left for Ben per the brief: photo of people.",
                "S21": "Left for Ben per the brief: headline page with photos of people.",
                "S22": "Left for Ben per the brief: headline page with photos of people."}
NEEDS_BEN = {
    "S03": ("The opening section sits beside a wall of more than 100 photographs of identifiable lawmakers, so the "
            "capture was discarded. A photo-free crop of only the left column (heading, '205+ lawmakers support our "
            "campaign' and the participation bar) is possible if you want it. The live counter read 10,785 of 20,000 "
            "on capture; the article says 10,556."),
    "S07": ("Capture discarded: the requested span (headline down to the 64 legislators line) includes the page's hero "
            "image, a large photographic face partly broken into pixels. It may be a stock or generated image, but I "
            "couldn't confirm the person isn't identifiable. A crop of the headline plus the Achievements paragraph, "
            "without the hero, is an alternative."),
}
NOTES = {
    "S01": "Heading and four bullets.",
    "S02": ("First screen at 1280x800 after choosing 'Only necessary' on the cookie banner. Over the 500KB target "
            "(about 1.7MB after reducing to 256 colours) because of the full-bleed photo; getting under 500KB would mean "
            "1x resolution or JPEG."),
    "S05": "The single say-and-do card for GPT-4.1.",
    "S06": "Title, rule and the scrolling ticker under it. The ticker is animated, so its text is caught mid-scroll and cut at the left edge.",
    "S07": "From the 'Campaign against Deepfakes' headline down to the paragraph with the 64 legislators line.",
    "S08": "Title and opening paragraph.",
    "S09": "Heading and the empty form; nothing typed or submitted.",
    "S10": "Title and the opening section up to the first subheading.",
    "S12": "Waited for the animated counter to reach 72%.",
    "S13": "Statement and the signature row; no signatory photos. Count read 145,700 on capture (including 72,360 from Ekō's petition); the article says 78,199.",
    "S14": ("No stance-by-emotion chart exists in the Soares article, so this is its main chart (stance). The placeholder "
            "caption mentions emotion and no longer matches. Alternatives: assets/chart-funnel.svg (what was coded), "
            "assets/chart-top-comments.svg (most-liked comments, coloured by stance). The emotion coding exists in "
            "data/studies/soares-reel-2026-08/comments.csv (2,136 rows; anger 292, fear 251, resignation 171), so a "
            "stance-by-emotion chart could be drawn with scripts/housecharts.py if you want the caption kept."),
    "S15": "Exact match: 'Four versions of one debate: agreement from 49% to 88%'.",
    "S16": "Exact match: 'What changed when someone else checked the work'.",
    "S17": ("No emotional-register chart exists in the Amanpour article, so this is its main chart (stance). The "
            "placeholder caption ('anger outnumbered fear') does not describe it. Alternatives: "
            "assets/chart-amanpour-frames.svg (comments v likes by frame, which carries the 23% of comments / 56% of "
            "likes blame finding), assets/chart-amanpour-stance-by-frame.svg, assets/chart-amanpour-top-comments.svg, "
            "assets/chart-amanpour-funnel.svg. The caption is supported by the data (emotion coding in "
            "data/studies/amanpour-segment-2026-09/comments.csv: anger 84, fear 41 of 322), so an emotion chart could "
            "be drawn with scripts/housecharts.py instead."),
    "S18": "Whole chart card: title, chart, note and source line. Waited for the chart SVG to render.",
    "S19": "Whole chart card. Waited for the chart SVG to render.",
    "S20": "'Key findings' heading and the list under it.",
    "S23a": "Built from the figures in the article's CHART comment, in the house funnel style. A 360px mobile SVG is also saved.",
    "S23b": "Built from the figures in the article's CHART comment, in the house funnel style. A 360px mobile SVG is also saved.",
}
ORDER = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S11", "S12", "S13", "S14",
         "S15", "S16", "S17", "S18", "S19", "S20", "S21", "S22", "S23a", "S23b"]

# ---------------------------------------------------------------- captions from the article

text = open(ARTICLE, encoding="utf-8").read()
PH = {m.group(1): m for m in re.finditer(r'<!-- SCREENSHOT (S\d+): (.*?)Caption: "(.*)" -->', text)}
CH = {m.group(1): m for m in re.finditer(r"<!-- CHART (S23[ab]): .*?-->", text, re.S)}

# ---------------------------------------------------------------- compress

for f in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, f)
    if f.endswith(".png") and os.path.getsize(p) > LIMIT:
        im = Image.open(p).convert("RGB")
        im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(p, optimize=True)
        print(f"compressed {f}: {os.path.getsize(p) // 1024} KB")

# ---------------------------------------------------------------- rows

rows = []
for sid in ORDER:
    entry = log.get(sid, {})
    if sid in CHART_FILE:
        status, method, file = "done", "repo chart", CHART_FILE[sid] + ".svg"
        when = chart_day
        src = SOURCE[sid]
    elif sid in LEFT_FOR_BEN or sid in NEEDS_BEN:
        status, method, file = ("skipped" if sid in LEFT_FOR_BEN else "needs Ben"), entry.get("method", ""), ""
        when = dt.datetime.fromisoformat(entry["captured_at"].replace("Z", "+00:00")).date() if entry.get("captured_at") else None
        src = entry.get("url") or SOURCE[sid]
    else:
        assert entry.get("file") and os.path.exists(os.path.join(OUT, entry["file"])), f"{sid} missing"
        status, method, file = "done", entry["method"], entry["file"]
        when = dt.datetime.fromisoformat(entry["captured_at"].replace("Z", "+00:00")).date()
        src = entry["url"]
    base = CHART_CAPTION.get(sid) or (PH[sid].group(3) if sid in PH else "")
    assert base or sid in LEFT_FOR_BEN, (f"{sid}: no caption found. Run this against the draft with its placeholders "
                                          "still in place (it rewrites them into figures).")
    caption = f"{base} Captured {nice(when)}." if status == "done" else base
    note = NEEDS_BEN.get(sid) or LEFT_FOR_BEN.get(sid) or NOTES.get(sid, "")
    if entry.get("fallback"):
        note = f"{note} Fallback: {entry['fallback']}.".strip()
    if entry.get("consent") and entry["consent"] != "no banner" and status == "done":
        note = f"{note} Cookie banner: {entry['consent']}.".strip()
    rows.append(dict(id=sid, file=file, source_url=src, captured_at=entry.get("captured_at", when.isoformat() if when else ""),
                     method=method, alt=ALT[sid], caption=caption, status=status, notes=note))

with open(os.path.join(OUT, "manifest.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

# ---------------------------------------------------------------- article figures


def figure(r):
    return (f'<figure>\n  <img src="screenshots/{r["file"]}" alt="{html.escape(r["alt"])}" />\n'
            f'  <figcaption>{html.escape(r["caption"], quote=False)}</figcaption>\n</figure>')


new = text
for r in rows:
    if r["status"] != "done":
        continue
    m = PH.get(r["id"]) or CH.get(r["id"])
    if m:  # already replaced on an earlier run
        new = new.replace(m.group(0), figure(r), 1)
open(ARTICLE, "w", encoding="utf-8").write(new)

# ---------------------------------------------------------------- contact sheet

cards = []
for r in rows:
    link = (f'<a href="{html.escape(r["source_url"])}">{html.escape(r["source_url"])}</a>'
            if r["source_url"].startswith("http") else f'<code>{html.escape(r["source_url"])}</code>')
    img = (f'<a href="{html.escape(r["file"])}"><img src="{html.escape(r["file"])}" alt="{html.escape(r["alt"])}" loading="lazy"></a>'
           if r["file"] else f'<div class="empty">{html.escape(r["status"])}</div>')
    cards.append(f"""<article class="card {r['status'].replace(' ', '-')}">
  <header><strong>{r['id']}</strong> <span class="status">{html.escape(r['status'])}</span> <span class="method">{html.escape(r['method'])}</span></header>
  {img}
  <p class="cap">{html.escape(r['caption'] or '(placeholder kept in article)')}</p>
  <p class="src">{link}</p>
  <p class="note">{html.escape(r['notes'])}</p>
</article>""")

page = f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Toolkit screenshots</title>
<style>
  :root {{ --paper: #f5f4ef; --ink: #232019; --muted: #635f54; --rule: #d8d6d1; --ok: #0f8a78; --warn: #a8323e; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 24px 16px 48px; background: var(--paper); color: var(--ink);
         font: 15px/1.45 "IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  h1 {{ font-family: Lora, Georgia, serif; font-size: 24px; margin: 0 0 4px; }}
  .lede {{ color: var(--muted); margin: 0 0 24px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 380px), 1fr)); gap: 20px; max-width: 1400px; }}
  .card {{ background: #fff; border: 1px solid var(--rule); border-radius: 6px; padding: 14px; min-width: 0; }}
  .card header {{ display: flex; gap: 8px; align-items: baseline; flex-wrap: wrap; margin-bottom: 10px; }}
  .status {{ font-size: 12px; padding: 1px 7px; border-radius: 10px; background: #e6f3f0; color: var(--ok); }}
  .needs-Ben .status, .skipped .status {{ background: #f6e6e8; color: var(--warn); }}
  .method {{ font-size: 12px; color: var(--muted); }}
  .card img {{ display: block; width: 100%; height: auto; max-height: 520px; object-fit: contain; object-position: top left;
              border: 1px solid var(--rule); background: var(--paper); }}
  .empty {{ height: 120px; display: grid; place-items: center; border: 1px dashed var(--rule); color: var(--muted); }}
  .cap {{ margin: 10px 0 4px; font-style: italic; }}
  .src, .note {{ margin: 4px 0; font-size: 13px; color: var(--muted); overflow-wrap: anywhere; }}
  a {{ color: var(--ink); }}
</style>
</head>
<body>
<h1>Toolkit screenshots</h1>
<p class="lede">How to communicate about AI safety, November 2026. {sum(r['status'] == 'done' for r in rows)} done, {sum(r['status'] == 'needs Ben' for r in rows)} need Ben, {sum(r['status'] == 'skipped' for r in rows)} left for Ben. Click an image to open it full size.</p>
<div class="grid">
{chr(10).join(cards)}
</div>
</body>
</html>
"""
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)
print("wrote manifest.csv, index.html and", sum(r["status"] == "done" for r in rows), "figures")

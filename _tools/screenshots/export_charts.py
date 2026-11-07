"""Export Common Signals charts (S14 to S17) and build the two new Diffusion charts (S23a, S23b).

Usage: python3 _tools/screenshots/export_charts.py   (from the repo root)

S14 to S17 are copied from the existing article charts. S23a and S23b are drawn with the
house chart code (scripts/housecharts.py), so they match the articles' charts exactly.
PNGs are made afterwards by render_svgs.js.
"""
import os
import re
import shutil
import sys

sys.dont_write_bytecode = True  # keep scripts/ free of __pycache__

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "_incoming", "how-to-communicate-about-ai-safety-2026-11", "screenshots")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import housecharts  # noqa: E402

os.makedirs(OUT, exist_ok=True)


def copy(src, dest):
    shutil.copyfile(os.path.join(ROOT, src), os.path.join(OUT, dest))
    print(dest, "<-", src)


# S14: the Soares reel article has no stance-by-emotion chart; its main chart is the stance chart.
copy("assets/chart-stance.svg", "S14-soares-reel-stance.svg")

# S15: "Four versions of one debate" is drawn inline in the DOAC article, not in assets/.
html = open(os.path.join(ROOT, "cant-we-just-unplug-it-doac-ai-debate-comment-analysis.html"), encoding="utf-8").read()
m = re.search(r'<div class="chart-desktop">(<svg.*?</svg>)</div>', html, re.S)
assert m and "Four versions of one debate" in m.group(1), "S15 chart not found"
open(os.path.join(OUT, "S15-doac-four-versions.svg"), "w", encoding="utf-8").write(m.group(1) + "\n")
print("S15-doac-four-versions.svg <- inline SVG in the DOAC article")

# S16: before and after independent verification.
copy("assets/mchart-lead-before-after.svg", "S16-metr-before-after.svg")

# S17: the Amanpour article has no emotional-register chart; its main chart is the stance chart.
copy("assets/chart-amanpour-stance.svg", "S17-amanpour-stance.svg")

# S23a and S23b: neutral bars (funnel type), label above each bar, value at its end.
SOURCE = "Data: Diffusion, The UK AI Compass (2026)"


def bars(rows):
    top = max(v for _, v in rows)
    return [dict(label=l, value=f"{v:.1f}%", frac=v / top) for l, v in rows]


s23a = dict(
    type="funnel",
    title="How the UK public describes AI",
    subs=["Share of open descriptions of AI using each image"],
    aria="How the UK public describes AI: body or brain 23.8%, machine 21.9%, journey 2.3%",
    rows=bars([("Body or brain", 23.8), ("Machine", 21.9), ("Journey", 2.3)]),
    feet=["Diffusion coded 2,758 open responses into 50 metaphor types; three shown.",
          f"{SOURCE}, CC BY-NC-ND 4.0. Chart: Common Signals."],
)
s23b = dict(
    type="funnel",
    title="Six UK mindsets on AI, share of UK adults",
    subs=[],
    aria=("Six UK mindsets on AI, share of UK adults: Disengaged Traditionalists 24.1%, Alarmed Populists 19.5%, "
          "Pragmatic Sceptics 16.3%, Market Optimists 16.3%, Hopeful Regulators 12.8%, Uncertain Middle 11.1%"),
    rows=bars([("Disengaged Traditionalists", 24.1), ("Alarmed Populists", 19.5), ("Pragmatic Sceptics", 16.3),
               ("Market Optimists", 16.3), ("Hopeful Regulators", 12.8), ("Uncertain Middle", 11.1)]),
    feet=[f"{SOURCE}, survey of 2,911 UK adults, December 2025. Chart: Common Signals."],
)
for name, model in (("S23a-uk-ai-metaphors", s23a), ("S23b-uk-ai-mindsets", s23b)):
    for mobile, suffix in ((False, ""), (True, "-mobile")):
        open(os.path.join(OUT, f"{name}{suffix}.svg"), "w", encoding="utf-8").write(housecharts.render(model, mobile))
        print(f"{name}{suffix}.svg built")

"""Draw the theory of change causal chain as SVG, desktop (600 wide) and phone (360 wide), in teal.

Run from the repo root: python3 scripts/draw-causal-chain.py
Edit the wording in STAGES below. Text is wrapped by an estimated character width, so
after a wording change open both SVGs and check nothing crowds its box.
"""
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PAPER = "#f5f4ef"
INK = "#232019"
SOFT = "#5a564c"
TEAL = "#006375"      # --teal-text
TEAL2 = "#008ba3"     # --teal
TINT = "#dde9e7"      # teal at about 10% on paper
TINT2 = "#e8efec"     # teal at about 6% on paper

LABEL = ("The causal chain from activities to impact: activities lead to outputs, which lead to communicator "
         "outcomes, which lead to public outcomes, which lead to a durable social mandate for AI governance, "
         "each step carrying an assumption")

STAGES = [
    dict(head="1. Activities: generate the evidence",
         body="Segmentation, message testing, comment analysis, messenger map, training", group="control"),
    dict(assume="measured effects predict real-campaign effects"),
    dict(head="2. Outputs: publish as open data",
         body="Published segments, tested frames, guides, trained messengers, impact report", group="control"),
    dict(assume="evidence is seen as credible by both sides"),
    dict(head="3. Communicator outcomes", sub="Our proximate outcome",
         body="Communicators change what they say and who says it", group="control"),
    dict(assume="communicators act on evidence"),
    dict(head="4. Public outcomes", body="Concern becomes commitment",
         pills=["Cross-societal concern", "Polarisation avoided", "Concern turned into action"], group="contrib"),
    dict(assume="better communication moves attitudes at scale"),
    dict(head="5. Impact: a durable social mandate for AI governance",
         body="Hard-to-reverse rules, and a social licence conditional on safety", group="contrib"),
]


def wrap(text, width, size, factor):
    """Greedy wrap by an estimated character width; checked afterwards in a browser."""
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = (line + " " + w).strip()
        if len(trial) * size * factor > width and line:
            lines.append(line)
            line = w
        else:
            line = trial
    lines.append(line)
    return lines


def esc(s):
    return html.escape(s, quote=False)


def build(W, phone):
    s = dict(head=15 if phone else 14, body=14 if phone else 13, assume=14 if phone else 12.5,
             title=19 if phone else 17, group=14 if phone else 12.5, lh=1.45)
    left = 16 if phone else 100
    right = W - (16 if phone else 20)
    bw = right - left
    pad = 18 if phone else 22
    out, y = [], 0
    marks = []  # (group, top, bottom) for brackets / group labels

    title_y = 34 if phone else 32
    out.append(f'<text class="title" x="{left}" y="{title_y}">The causal chain</text>')
    y = title_y + (18 if phone else 20)

    group_seen = None
    for st in STAGES:
        if "assume" in st:
            ax = left + (22 if phone else 24)
            tx = ax + 16
            avail = right - tx
            lines = wrap("Assumption: " + st["assume"], avail, s["assume"], 0.5)
            if st.get("note"):
                lines += wrap(st["note"], avail, s["assume"], 0.5)
            lh = s["assume"] * s["lh"]
            h = max(52, 16 + len(lines) * lh + 12)
            top, bot = y + 4, y + h - 6
            out.append(f'<path class="arrow" d="M{ax} {top} L{ax} {bot}"/>')
            ty = y + (h - len(lines) * lh) / 2 + s["assume"] * 0.9
            for i, ln in enumerate(lines):
                if i == 0 and ln.startswith("Assumption:"):
                    rest = ln[len("Assumption:"):]
                    out.append(f'<text class="as" x="{tx}" y="{ty:.1f}"><tspan class="ask">Assumption:</tspan>{esc(rest)}</text>')
                else:
                    out.append(f'<text class="as" x="{tx}" y="{ty:.1f}">{esc(ln)}</text>')
                ty += lh
            y += h
            continue

        g = st["group"]
        if phone and g != group_seen:
            label = "What we control and influence" if g == "control" else "What we contribute to"
            y += 6 if group_seen else 0
            out.append(f'<text class="grp" x="{left}" y="{y + s["group"]:.1f}">{label}</text>')
            y += s["group"] + 12
        group_seen = g

        inner = bw - 2 * pad
        head_lines = wrap(st["head"], inner, s["head"], 0.58)
        body_lines = wrap(st["body"], inner, s["body"], 0.5)
        sub_lines = wrap(st["sub"], inner, s["body"], 0.5) if st.get("sub") else []
        lh_h, lh_b = s["head"] * 1.35, s["body"] * s["lh"]
        top = y
        cy = top + pad + s["head"] * 0.85
        texts = []
        for ln in head_lines:
            texts.append(f'<text class="head" x="{left + bw / 2}" y="{cy:.1f}" text-anchor="middle">{esc(ln)}</text>')
            cy += lh_h
        cy += 2
        for ln in sub_lines:
            texts.append(f'<text class="sub" x="{left + bw / 2}" y="{cy:.1f}" text-anchor="middle">{esc(ln)}</text>')
            cy += lh_b
        for ln in body_lines:
            texts.append(f'<text class="body" x="{left + bw / 2}" y="{cy:.1f}" text-anchor="middle">{esc(ln)}</text>')
            cy += lh_b
        pills = []
        if st.get("pills"):
            cy += 6
            n = len(st["pills"])
            if phone:
                ph = 38
                for p in st["pills"]:
                    pills.append(f'<rect class="pill" x="{left + pad}" y="{cy:.1f}" width="{inner}" height="{ph}" rx="6"/>')
                    pills.append(f'<text class="pilltext" x="{left + bw / 2}" y="{cy + ph / 2 + s["body"] * 0.35:.1f}" text-anchor="middle">{esc(p)}</text>')
                    cy += ph + 8
                cy -= 8
            else:
                gap = 12
                pw = (inner - gap * (n - 1)) / n
                ph = 58
                for i, p in enumerate(st["pills"]):
                    px = left + pad + i * (pw + gap)
                    pl = wrap(p, pw - 20, s["body"], 0.5)
                    pills.append(f'<rect class="pill" x="{px:.1f}" y="{cy:.1f}" width="{pw:.1f}" height="{ph}" rx="6"/>')
                    py = cy + ph / 2 - (len(pl) - 1) * lh_b / 2 + s["body"] * 0.35
                    for ln in pl:
                        pills.append(f'<text class="pilltext" x="{px + pw / 2:.1f}" y="{py:.1f}" text-anchor="middle">{esc(ln)}</text>')
                        py += lh_b
                cy += ph
            cy += 4
        bottom = cy - lh_b + s["body"] * 0.3 + pad if not pills else cy + pad - 6
        h = bottom - top
        cls = "box-control" if g == "control" else "box-contrib"
        out.append(f'<rect class="{cls}" x="{left}" y="{top:.1f}" width="{bw}" height="{h:.1f}" rx="8"/>')
        out.extend(texts)
        out.extend(pills)
        marks.append((g, top, bottom))
        y = bottom

    H = round(y + (20 if phone else 22))
    if not phone:
        for g in ("control", "contrib"):
            tops = [m[1] for m in marks if m[0] == g]
            bots = [m[2] for m in marks if m[0] == g]
            t, b = min(tops), max(bots)
            cls = "bracket" if g == "control" else "bracket bracket-dash"
            out.append(f'<path class="{cls}" d="M65 {t:.1f} L55 {t:.1f} L55 {b:.1f} L65 {b:.1f}"/>')
            mid = (t + b) / 2
            label = "What we control and influence" if g == "control" else "What we contribute to"
            out.append(f'<text class="grp" x="38" y="{mid:.1f}" text-anchor="middle" transform="rotate(-90 38 {mid:.1f})">{label}</text>')

    style = f"""
.title{{font-family:"Lora",Georgia,serif;font-size:{s['title']}px;font-weight:600;fill:{INK}}}
.head{{font-family:"IBM Plex Sans",-apple-system,sans-serif;font-size:{s['head']}px;font-weight:600;fill:{INK}}}
.body,.sub,.pilltext{{font-family:"IBM Plex Sans",-apple-system,sans-serif;font-size:{s['body']}px;fill:{SOFT}}}
.sub{{fill:{TEAL}}}
.pilltext{{fill:{INK}}}
.as{{font-family:"IBM Plex Sans",-apple-system,sans-serif;font-size:{s['assume']}px;fill:{SOFT}}}
.ask{{font-weight:600;fill:{TEAL}}}
.grp{{font-family:"IBM Plex Sans",-apple-system,sans-serif;font-size:{s['group']}px;font-weight:600;fill:{TEAL}}}
.box-control{{fill:{TINT};stroke:{TEAL};stroke-width:1.4}}
.box-contrib{{fill:{PAPER};stroke:{TEAL2};stroke-width:1.4;stroke-dasharray:5 4}}
.pill{{fill:{TINT2};stroke:{TEAL2};stroke-width:1;stroke-opacity:.45}}
.arrow{{stroke:{TEAL};stroke-width:1.8;fill:none;marker-end:url(#tcc-arrow)}}
.bracket{{stroke:{TEAL};stroke-width:1.4;fill:none}}
.bracket-dash{{stroke:{TEAL2};stroke-dasharray:4 3}}
"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="{LABEL}"><style>{style}</style>\n<defs>\n'
            f'<marker id="tcc-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">'
            f'<path d="M0 0 L10 5 L0 10 z" fill="{TEAL}"/></marker>\n</defs>\n'
            f'<rect width="{W}" height="{H}" fill="{PAPER}"/>\n' + "\n".join(out) + "\n</svg>\n")


if __name__ == "__main__":
    (ROOT / "assets" / "chart-toc-causal-chain.svg").write_text(build(600, False), encoding="utf-8")
    (ROOT / "assets" / "chart-toc-causal-chain-mobile.svg").write_text(build(360, True), encoding="utf-8")
    print("Wrote assets/chart-toc-causal-chain.svg and assets/chart-toc-causal-chain-mobile.svg")

"""Portrait, phone-width versions of the theory-of-change diagrams.

Usage: python3 scripts/toc-mobile-charts.py
Writes assets/chart-toc-{vicious-cycle,virtuous-cycle,values-chain,safety-ecosystem,causal-chain}-mobile.svg.
The wording mirrors the desktop SVGs; change both together.
"""
import html

W, PAD = 360, 20
INK, MUTED, ACC, PAPER, RULE = "#232019", "#635f54", "#7a1e49", "#f5f4ef", "#d8d6d1"
SANS = '"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif'
SERIF = '"Lora",Georgia,serif'


def wrap(text, size, width, factor=0.55):
    per = max(6, int(width / (size * factor)))
    lines, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + (1 if cur else 0) <= per:
            cur = f"{cur} {w}".strip()
        else:
            lines.append(cur)
            cur = w
    return lines + [cur] if cur else lines


class D:
    def __init__(self, marker_colours):
        self.p, self.y = [], PAD
        self.defs = "".join(
            f'<marker id="{mid}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="{c}"/></marker>'
            for mid, c in marker_colours.items())

    def t(self, x, y, s, size, fill, weight=None, serif=False, anchor="start", spacing=None, italic=False):
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        a += ' font-style="italic"' if italic else ""
        wt = f' font-weight="{weight}"' if weight else ""
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        self.p.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{SERIF if serif else SANS}\' font-size="{size}"'
                      f'{wt}{a}{ls} fill="{fill}">{html.escape(s, quote=False)}</text>')

    def title(self, s):
        for line in wrap(s, 19, W - 2 * PAD, 0.59):
            self.y += 19
            self.t(PAD, self.y, line, 19, INK, 600, serif=True)
            self.y += 5
        self.y += 14

    def box(self, x, y, w, head, lines, stroke, sw=1.3, centre=True, item_size=14, fill=PAPER, fill_op=1):
        """Draw a box sized to its text; returns its height."""
        inner = w - 28
        heads = wrap(head, 15.5, inner, 0.56)
        body = [l for s in lines for l in wrap(s, item_size, inner, 0.54)]
        h = 16 + len(heads) * 20 + (6 + len(body) * 19 if body else 0) + 10
        fo = f' fill-opacity="{fill_op}"' if fill_op < 1 else ""
        self.p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}"{fo} stroke="{stroke}" stroke-width="{sw}"/>')
        cx, ty, anchor = (x + w / 2, y + 16, "middle") if centre else (x + 14, y + 16, "start")
        for hl in heads:
            ty += 16
            self.t(cx, ty, hl, 15.5, INK, 600, anchor=anchor)
            ty += 4
        if body:
            ty += 6
            for bl in body:
                ty += 15
                self.t(cx, ty, bl, item_size, MUTED, anchor=anchor)
                ty += 4
        return h

    def path(self, d, colour, marker, dashed=False, width=1.7, both=False):
        dash = ' stroke-dasharray="4 3"' if dashed else ""
        start = f' marker-start="url(#{marker})"' if both else ""
        self.p.append(f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{width}"{dash}{start} marker-end="url(#{marker})"/>')

    def svg(self, label):
        h = int(self.y + PAD)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" '
                f'aria-label="{html.escape(label)}"><defs>{self.defs}</defs><rect width="{W}" height="{h}" fill="{PAPER}"/>'
                + "".join(self.p) + "</svg>\n")


def cycle(name, title, stages, loop_label, colour, box_stroke, label, dashed_loop=False, centre=True):
    d = D({"a": colour, "b": MUTED if dashed_loop else colour})
    d.title(title)
    bw = W - 2 * PAD - 36          # leave a right-hand channel for the return arrow
    tops, bottoms = [], []
    for i, (head, lines) in enumerate(stages):
        h = d.box(PAD, d.y, bw, head, lines, box_stroke, centre=centre)
        tops.append(d.y); bottoms.append(d.y + h)
        d.y += h
        if i < len(stages) - 1:
            cx = PAD + bw / 2
            d.path(f"M{cx} {d.y + 2} L{cx} {d.y + 22}", colour, "a")
            d.y += 26
    # Return arrow: out of the last box's right edge, up the channel, into the first box.
    rx, first_mid, last_mid = PAD + bw, tops[0] + 30, bottoms[-1] - 30
    ch = W - PAD - 8
    d.path(f"M{rx + 2} {last_mid} L{ch - 10} {last_mid} Q{ch} {last_mid} {ch} {last_mid - 10} "
           f"L{ch} {first_mid + 10} Q{ch} {first_mid} {ch - 10} {first_mid} L{rx + 4} {first_mid}",
           MUTED if dashed_loop else colour, "b", dashed=dashed_loop, width=1.5)
    d.y += 22
    d.t(W / 2, d.y, loop_label, 14, MUTED, anchor="middle")
    d.y += 4
    open(f"assets/chart-toc-{name}-mobile.svg", "w", encoding="utf-8").write(d.svg(label))


def ecosystem():
    d = D({"a": MUTED, "b": ACC})
    d.title("Two models of AI safety")
    cw = W - 2 * PAD
    # Prescriptive model
    d.y += 2
    d.t(PAD, d.y + 13, "PRESCRIPTIVE MODEL", 13.5, ACC, 600, spacing="0.5")
    d.y += 26
    bw = 220; bx = (W - bw) / 2
    h = d.box(bx, d.y, bw, "AI safety experts", [], MUTED)
    d.y += h
    d.path(f"M{W/2} {d.y + 2} L{W/2} {d.y + 30}", MUTED, "a")
    d.y += 34
    h = d.box(bx, d.y, bw, "Society & AI users", ["Passive recipients of rules handed down"], MUTED)
    d.y += h + 24
    d.p.append(f'<line x1="{PAD}" y1="{d.y}" x2="{W - PAD}" y2="{d.y}" stroke="{RULE}" stroke-width="1"/>')
    d.y += 24
    # Collaborative ecosystem
    d.t(PAD, d.y + 13, "COLLABORATIVE ECOSYSTEM", 13.5, ACC, 600, spacing="0.5")
    d.y += 26
    top_y = d.y
    h1 = d.box(bx, d.y, bw, "Regulatory bodies & safety institutes", [], MUTED)
    d.y += h1 + 40
    row_y, sw_ = d.y, (cw - 16) / 2
    h2 = d.box(PAD, row_y, sw_, "AI safety researchers & ethicists", [], MUTED)
    h3 = d.box(PAD + sw_ + 16, row_y, sw_, "AI industry & tech developers", [], MUTED)
    d.y = row_y + max(h2, h3) + 40
    hub_y = d.y
    h4 = d.box(bx, hub_y, bw, "Society & AI users", ["Active stakeholders in value alignment"], ACC, sw=1.8)
    d.y += h4
    # Two-way links from the public hub to each of the other three.
    d.path(f"M{W/2} {hub_y - 3} L{W/2} {top_y + h1 + 3}", ACC, "b", dashed=True, width=1.4, both=True)
    d.path(f"M{bx + 30} {hub_y - 3} L{PAD + sw_ / 2} {row_y + h2 + 3}", ACC, "b", dashed=True, width=1.4, both=True)
    d.path(f"M{bx + bw - 30} {hub_y - 3} L{PAD + sw_ * 1.5 + 16} {row_y + h3 + 3}", ACC, "b", dashed=True, width=1.4, both=True)
    open("assets/chart-toc-safety-ecosystem-mobile.svg", "w", encoding="utf-8").write(d.svg(
        "Two models compared: a prescriptive model where experts dictate rules to passive users, versus a "
        "collaborative ecosystem where researchers, regulators, industry and the public actively co-create safety "
        "measures through networked feedback"))


def causal_chain():
    d = D({"a": ACC, "b": MUTED})
    d.title("The causal chain")
    cw = W - 2 * PAD

    def group(label):
        d.t(PAD, d.y + 13, label, 13.5, ACC, 600, spacing="0.5")
        d.y += 24

    def link(text, colour, marker):
        # Arrow down the left, the assumption it rests on in italics beside it.
        lines = [l for s in text for l in wrap(s, 13.5, cw - 44, 0.52)]
        h = max(36, len(lines) * 18 + 12)
        x = PAD + 16
        d.path(f"M{x} {d.y + 3} L{x} {d.y + h - 3}", colour, marker)
        ty = d.y + (h - len(lines) * 18) / 2 + 2
        for l in lines:
            ty += 13
            d.t(x + 18, ty, l, 13.5, MUTED, italic=True)
            ty += 5
        d.y += h

    group("WHAT WE CONTROL AND INFLUENCE")
    stages = [
        ("1. Activities: generate the evidence", ["Segmentation, message testing, comment analysis, messenger map, training"], ["measured effects predict real-campaign effects"]),
        ("2. Outputs: publish as open data", ["Published segments, tested frames, guides, trained messengers, impact report"], ["evidence seen as credible by both sides"]),
        ("3. Communicator outcomes", ["(our proximate outcome)", "Communicators change what they say and who says it"], ["communicators act on evidence, not instinct", "(the assumption the whole model rests on)"]),
    ]
    for head, body, assumption in stages:
        d.y += d.box(PAD, d.y, cw, head, body, ACC, sw=1.4, fill=ACC, fill_op=0.1)
        if head.startswith("3."):
            d.y += 4
            link(assumption, ACC, "a")
            d.y += 10
            group("WHAT WE CONTRIBUTE TO")
        else:
            link(assumption, ACC, "a")
    d.y += d.box(PAD, d.y, cw, "4. Public outcomes",
                 ["Concern becomes commitment", "", "Cross-societal concern", "Polarisation avoided", "Concern turned into action"], MUTED)
    link(["better communication moves attitudes at scale"], MUTED, "b")
    d.y += d.box(PAD, d.y, cw, "5. Impact: a durable social mandate for AI governance",
                 ["Hard-to-reverse rules, and a social licence conditional on safety"], MUTED)
    open("assets/chart-toc-causal-chain-mobile.svg", "w", encoding="utf-8").write(d.svg(
        "The causal chain from activities to impact: activities lead to outputs, which lead to communicator "
        "outcomes, which lead to public outcomes, which lead to a durable social mandate for AI governance, each "
        "step carrying an assumption"))


if __name__ == "__main__":
    cycle("vicious-cycle", "We are in a vicious cycle", [
        ("Weak social mandate", ["A minority see AI as a priority issue"]),
        ("Weak governance", ["No mandate to hold the line on rules"]),
        ("Companies not incentivised", ["No pressure to trade capability for safety"]),
        ("Passive public behaviour", ["People adopt tools without questioning"]),
    ], "Each stage feeds the next", MUTED, MUTED,
        "A vicious cycle: weak social mandate leads to weak governance, companies not incentivised, and passive "
        "public behaviour, which loops back to a weak mandate")
    cycle("virtuous-cycle", "A strong social mandate creates a virtuous circle", [
        ("Strong social mandate", ["A majority see AI governance as a priority"]),
        ("Durable governance", ["Rules the public supports and drives"]),
        ("Companies compelled", ["Social licence makes safety a condition"]),
        ("Active public behaviour", ["People question, choose, get involved"]),
    ], "Each stage reinforces the next", ACC, ACC,
        "A virtuous circle: a strong social mandate drives durable governance, compels companies, and produces "
        "active public behaviour, which reinforces the mandate")
    cycle("values-chain", "Values reinforce actions, and actions reinforce values", [
        ("Foundational values", ["Wellbeing", "Fairness", "Transparency"]),
        ("Systemic & risk beliefs", ["Capability awareness", "Risk awareness", "Developer responsibility"]),
        ("Technical & governance norms", ["Safety processes", "Red-teaming", "Transparency reports"]),
        ("Implemented actions", ["Interpretability tools", "Independent auditing", "Regulatory compliance"]),
    ], "Reinforcing", ACC, ACC,
        "The systemic process of integrating AI safety: aligning foundational values, cultivating risk awareness, "
        "establishing technical norms, and implementing concrete actions, which reinforce the values in turn",
        dashed_loop=True)
    ecosystem()
    causal_chain()
    print("toc mobile charts written")

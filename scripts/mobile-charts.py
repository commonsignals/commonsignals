"""Build phone-width versions of the house-style article charts.

Usage: python3 scripts/mobile-charts.py assets/chart-x.svg [...]
Writes assets/chart-x-mobile.svg next to each input.

Reads the numbers, labels, colours and bar proportions straight from the
desktop SVG (as drawn by the social-comment-analysis charts.py, or by hand
in the same structure), then redraws it 360 wide with labels above the bars
and text sized to stay legible on a phone. Articles swap it in with
<picture><source media="(max-width: 640px)" ...>.
"""
import html
import re
import sys
import xml.etree.ElementTree as ET

W = 360          # viewBox width; shown at ~330-350px on phones, so ~1:1
PAD = 20
CW = W - 2 * PAD  # content width
SANS = '"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif'
SERIF = '"Lora",Georgia,serif'
# Type scale for phones (px in viewBox units, which render at ~0.92-0.97x).
F_TITLE, F_SUB, F_LABEL, F_NUM, F_SMALL = 19, 14, 15, 15, 14
BAR_PCT = re.compile(r"^([\d.]+)% of \w+$")


def char_w(size, serif=False):
    return size * (0.59 if serif else 0.535)


def wrap(text, size, width, serif=False):
    per_line = max(8, int(width / char_w(size, serif)))
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= per_line:
            cur = f"{cur} {w}".strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


# ---------- Parsing ----------

def parse_css(svg_text):
    rules = {}
    for m in re.finditer(r"\.([\w-]+)((?:\.[\w-]+)*)\s*\{([^}]*)\}", svg_text):
        key = "." + m.group(1) + m.group(2)
        props = dict((k.strip(), v.strip()) for k, v in
                     (p.split(":", 1) for p in m.group(3).split(";") if ":" in p))
        rules[key] = props
    return rules


def colour(fill, opacity, style_rules, cls):
    """Return (hex, opacity) for a rect, resolving class fills and rgba()."""
    props = {}
    if cls:
        parts = cls.split()
        for n in range(len(parts), 0, -1):  # most specific compound class first
            key = "." + ".".join(parts[:n])
            if key in style_rules:
                props = {**style_rules[key], **props}
        for p in parts:
            props = {**style_rules.get("." + p, {}), **props}
    fill = fill or props.get("fill", "#000")
    op = float(opacity) if opacity is not None else float(props.get("opacity", 1))
    m = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)", fill)
    if m:
        r, g, b, a = m.groups()
        fill, op = "#%02x%02x%02x" % (int(r), int(g), int(b)), op * float(a)
    return fill.lower(), op


def parse(path):
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"<metadata>.*?</metadata>", "", raw, flags=re.S)
    rules = parse_css(raw)
    root = ET.fromstring(raw)
    ns = "{http://www.w3.org/2000/svg}"
    items = []

    def walk(node, dx, dy):
        for el in node:
            tag = el.tag.replace(ns, "")
            if tag == "g":
                m = re.match(r"translate\(([-\d.]+)[ ,]+([-\d.]+)\)", el.get("transform", ""))
                walk(el, dx + float(m.group(1)) if m else dx, dy + float(m.group(2)) if m else dy)
            elif tag == "text":
                style = el.get("style", "")
                sf = re.search(r"fill:\s*(#[0-9a-fA-F]{3,6})", style)
                items.append(dict(kind="text", cls=el.get("class", ""), x=float(el.get("x", 0)) + dx,
                                  y=float(el.get("y", 0)) + dy, anchor=el.get("text-anchor", "start"),
                                  text="".join(el.itertext()).strip(),
                                  fill=(sf.group(1) if sf else el.get("fill"))))
            elif tag == "rect":
                if el.get("width") in (None,) or el.get("x") is None:
                    continue  # background
                fill, op = colour(el.get("fill"), el.get("opacity"), rules, el.get("class"))
                items.append(dict(kind="rect", x=float(el.get("x")) + dx, y=float(el.get("y")) + dy,
                                  w=float(el.get("width")), h=float(el.get("height")), fill=fill, op=op))
    walk(root, 0, 0)
    paper = re.search(r'<rect width="\d+" height="\d+" fill="(#[0-9a-fA-F]{6})"', raw)
    ink = re.search(r"\.h\s*\{[^}]*fill:\s*(#[0-9a-fA-F]{6})", raw)
    muted = re.search(r"\.t\s*\{[^}]*fill:\s*(#[0-9a-fA-F]{6})", raw)
    return dict(items=items, label=root.get("aria-label", ""),
                paper=paper.group(1) if paper else "#f5f4ef",
                ink=ink.group(1) if ink else "#232019",
                muted=muted.group(1) if muted else "#635f54")


def split_header(P):
    texts = [i for i in P["items"] if i["kind"] == "text"]
    rects = [i for i in P["items"] if i["kind"] == "rect"]
    title = next(t for t in texts if t["cls"] == "h")
    first_row = min(r["y"] for r in rects) if rects else 1e9
    subs = [t for t in texts if t["cls"] == "t" and t["y"] < first_row - 4 and t["anchor"] == "start"]
    last_row = max(r["y"] + r["h"] for r in rects) if rects else 0
    feet = [t for t in texts if t["cls"] == "t" and t["y"] > last_row + 8 and t["anchor"] == "start"]
    return title["text"], [s["text"] for s in sorted(subs, key=lambda t: t["y"])], feet


def near(texts, y, tol=14):
    return [t for t in texts if abs(t["y"] - y) <= tol]


# ---------- Rendering ----------

class Canvas:
    def __init__(self, P):
        self.P, self.parts, self.y = P, [], PAD + 4

    def text(self, x, y, s, size, fill, weight=None, serif=False, anchor="start"):
        wt = f' font-weight="{weight}"' if weight else ""
        an = f' text-anchor="{anchor}"' if anchor != "start" else ""
        self.parts.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{SERIF if serif else SANS}\' '
                          f'font-size="{size}"{wt}{an} fill="{fill}">{html.escape(s, quote=False)}</text>')

    def rect(self, x, y, w, h, fill, op):
        o = f' opacity="{op:.2f}"' if op < 0.999 else ""
        self.parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 2):.1f}" height="{h}" fill="{fill}"{o} rx="2"/>')

    def para(self, s, size, fill, weight=None, serif=False, gap=1.3):
        for line in wrap(s, size, CW, serif):
            self.y += size
            self.text(PAD, self.y, line, size, fill, weight, serif)
            self.y += size * (gap - 1)

    def header(self, title, subs):
        self.para(title, F_TITLE, self.P["ink"], 600, serif=True, gap=1.25)
        self.y += 4
        for s in subs:
            self.para(s, F_SUB, self.P["muted"])
        self.y += 14

    def footer(self, feet):
        if feet:
            self.y += 6
        for f in feet:
            self.para(f["text"], F_SMALL, self.P["muted"])

    def svg(self):
        h = int(self.y + PAD)
        label = html.escape(self.P["label"])
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" '
                f'role="img" aria-label="{label}"><rect width="{W}" height="{h}" fill="{self.P["paper"]}"/>'
                + "".join(self.parts) + "</svg>\n")


def bar_rows(c, rows, bar_h=22, value_room=64):
    """rows: [(label_lines, frac, fill, op, value)] drawn label-above-bar."""
    max_w = CW - value_room
    for label, frac, fill, op, value in rows:
        for line in wrap(label, F_LABEL, CW):
            c.y += F_LABEL
            c.text(PAD, c.y, line, F_LABEL, c.P["ink"])
            c.y += 3
        c.y += 4
        w = max_w * frac
        c.rect(PAD, c.y, w, bar_h, fill, op)
        c.text(PAD + w + 8, c.y + bar_h / 2 + F_NUM * 0.35, value, F_NUM, c.P["ink"], 600)
        c.y += bar_h + 14


def funnel_or_stance(P, c):
    texts = [i for i in P["items"] if i["kind"] == "text"]
    rects = sorted((i for i in P["items"] if i["kind"] == "rect"), key=lambda r: r["y"])
    mx = max(r["w"] for r in rects)
    rows = []
    for r in rects:
        mid = r["y"] + r["h"] / 2
        row_t = near(texts, mid + 5, 9)
        num = next(t for t in row_t if t["cls"] == "n")
        lab = next(t for t in row_t if t is not num and t["cls"] in ("t", "l", "lbl"))
        rows.append((lab["text"], r["w"] / mx, r["fill"], r["op"], num["text"]))
    # Stance bars are shares of 100%, not of the longest bar: keep that scale.
    if all(v.endswith("%") for *_, v in rows):
        rows = [(l, float(v.rstrip("%")) / 100 / max(float(x[4].rstrip("%")) / 100 for x in rows), f, o, v)
                for l, _, f, o, v in rows]
    bar_rows(c, rows)


def top_comments(P, c):
    texts = [i for i in P["items"] if i["kind"] == "text"]
    rects = sorted((i for i in P["items"] if i["kind"] == "rect" and i["h"] > 12), key=lambda r: r["y"])
    legend = sorted((i for i in P["items"] if i["kind"] == "rect" and i["h"] <= 12 and i["w"] <= 12), key=lambda r: r["x"])
    mx = max(r["w"] for r in rects)
    max_w = CW - 70
    for r in rects:
        q = min((t for t in texts if t["cls"] == "q"), key=lambda t: abs(t["y"] - (r["y"] + 11)))
        n = min((t for t in texts if t["cls"] == "n"), key=lambda t: abs(t["y"] - (r["y"] + 26)))
        for line in wrap(q["text"], F_LABEL, CW)[:2]:
            c.y += F_LABEL
            c.text(PAD, c.y, line, F_LABEL, c.P["ink"])
            c.y += 3
        c.y += 4
        w = max_w * r["w"] / mx
        c.rect(PAD, c.y, w, 14, r["fill"], r["op"])
        c.text(PAD + w + 8, c.y + 12, n["text"], F_NUM, c.P["ink"], 600)
        c.y += 14 + 16
    if legend:
        x = PAD
        c.y += 4
        for sw in legend:
            lab = min((t for t in texts if t["cls"] == "t" and t["x"] > sw["x"]), key=lambda t: (abs(t["y"] - (sw["y"] + 9)), t["x"]))
            width = 16 + len(lab["text"]) * char_w(F_SMALL) + 18
            if x + width > W - PAD and x > PAD:
                x, c.y = PAD, c.y + F_SMALL + 10
            c.rect(x, c.y, 11, 11, sw["fill"], sw["op"])
            c.text(x + 16, c.y + 10, lab["text"], F_SMALL, c.P["muted"])
            x += width
        c.y += F_SMALL + 6


def frames(P, c):
    texts = [i for i in P["items"] if i["kind"] == "text"]
    labels = sorted((t for t in texts if t["cls"] == "l"), key=lambda t: t["y"])
    rects = [i for i in P["items"] if i["kind"] == "rect"]
    max_w = CW - 150
    pct_texts = [t for t in texts if t["cls"] == "t" and BAR_PCT.match(t["text"])]
    scale = max(float(BAR_PCT.match(t["text"]).group(1)) for t in pct_texts) or 100
    for lab in labels:
        c.y += F_LABEL
        c.text(PAD, c.y, lab["text"], F_LABEL, c.P["ink"], 600)
        c.y += 6
        row_rects = sorted((r for r in rects if lab["y"] - 16 <= r["y"] <= lab["y"] + 20), key=lambda r: r["y"])
        for r in row_rects:
            t = min(pct_texts, key=lambda t: abs(t["y"] - (r["y"] + 9)))
            pct = float(BAR_PCT.match(t["text"]).group(1))
            w = max_w * pct / scale
            c.rect(PAD, c.y, w, 13, r["fill"], r["op"])
            c.text(PAD + w + 8, c.y + 11.5, t["text"], F_SMALL, c.P["ink"])
            c.y += 13 + 6
        c.y += 10


def stance_by_frame(P, c):
    texts = [i for i in P["items"] if i["kind"] == "text"]
    rects = [i for i in P["items"] if i["kind"] == "rect"]
    heads = sorted((t for t in texts if t["cls"] == "t" and t["anchor"] == "middle"), key=lambda t: t["x"])
    labels = sorted((t for t in texts if t["cls"] == "l"), key=lambda t: t["y"])
    gap, cell_h = 4, 30
    cw = (CW - gap * (len(heads) - 1)) / len(heads)
    for j, h in enumerate(heads):
        c.text(PAD + j * (cw + gap) + cw / 2, c.y + F_SMALL, h["text"], F_SMALL, c.P["muted"], anchor="middle")
    c.y += F_SMALL + 10
    for lab in labels:
        c.y += F_LABEL
        c.text(PAD, c.y, lab["text"], F_LABEL, c.P["ink"])
        c.y += 6
        cells = sorted((r for r in rects if abs((r["y"] + r["h"] / 2) - (lab["y"] - 4)) < 12), key=lambda r: r["x"])
        for j, r in enumerate(cells):
            v = min((t for t in texts if t["cls"] == "n"), key=lambda t: abs(t["x"] - (r["x"] + r["w"] / 2)) + abs(t["y"] - (r["y"] + 19)))
            x = PAD + j * (cw + gap)
            c.rect(x, c.y, cw, cell_h, r["fill"], r["op"])
            c.text(x + cw / 2, c.y + cell_h / 2 + F_NUM * 0.35, v["text"], F_NUM, v["fill"] or c.P["ink"], 600, anchor="middle")
        c.y += cell_h + 10


def kind(P):
    texts = [i for i in P["items"] if i["kind"] == "text"]
    if any(t["cls"] == "q" for t in texts):
        return top_comments
    if any(t["anchor"] == "middle" and t["cls"] == "t" for t in texts):
        return stance_by_frame
    if sum(1 for t in texts if BAR_PCT.match(t["text"])) >= 2:
        return frames
    return funnel_or_stance


def build(path):
    P = parse(path)
    title, subs, feet = split_header(P)
    c = Canvas(P)
    c.header(title, subs)
    kind(P)(P, c)
    c.footer(feet)
    out = re.sub(r"\.svg$", "-mobile.svg", path)
    open(out, "w", encoding="utf-8").write(c.svg())
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        print(build(p))

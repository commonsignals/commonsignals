"""House-style article charts: one data model, a desktop and a phone rendering.

Usage:
  python3 scripts/housecharts.py assets/chart-x.svg [--comments data/studies/<slug>/comments.csv]

Rewrites assets/chart-x.svg in the current palette and writes assets/chart-x-mobile.svg.
The chart's data is embedded in each SVG (<desc> JSON), so re-running is lossless. Older
charts without it are parsed from their drawn marks; --comments lets top-comment bars be
coloured by each comment's coded stance (matched on quote text) rather than guessed.

Colour follows meaning and is the same on every chart:
  agree = green-teal, disagree = red-maroon, mixed = mid grey, no clear position = pale grey.
Charts that are not about stance (funnel, comments v engagement) use neutral greys, so
green and red always mean agree and disagree. Colour is never the only cue: every bar
and segment is labelled in text.
"""
import csv
import html
import json
import re
import sys
import xml.etree.ElementTree as ET

PAPER, INK, MUTED, RULE = "#f5f4ef", "#232019", "#635f54", "#d8d6d1"
STANCE = {
    "agree": "#0f8a78",       # green-teal
    "agree_part": "#7fbfb5",  # lighter green-teal: agrees in part
    "mixed": "#8c8579",       # mid grey
    "disagree": "#a8323e",    # red-maroon
    "none": "#c9c2b6",        # pale grey: no clear position / other
    "action": INK,            # names an action (Soares reel)
}
NEUTRAL_DARK, NEUTRAL_LIGHT = "#5b554c", "#c9c2b6"
LEGEND_DEFAULT = {"agree": "Agrees", "agree_part": "Agrees in part", "mixed": "Mixed",
                  "disagree": "Disagrees", "none": "No clear position", "action": "Names an action"}
SANS = '"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif'
SERIF = '"Lora",Georgia,serif'

# Two sizes: desktop is 720 wide (shown ~640-700px), phone is 360 wide (shown ~330-350px).
SIZES = {
    False: dict(W=720, PAD=32, title=17, sub=13, label=14, num=13, small=12.5, bar=20),
    True: dict(W=360, PAD=20, title=19, sub=14, label=15, num=15, small=14, bar=20),
}


def stance_key(label):
    l = label.lower()
    if "in part" in l or "partly" in l:
        return "agree_part"
    if l.startswith(("agree", "accept")):
        return "agree"
    if l.startswith(("disagree", "reject")):
        return "disagree"
    if l.startswith("mixed"):
        return "mixed"
    return "none"


# ---------------------------------------------------------------- text helpers

def wrap(text, size, width, serif=False):
    per = max(8, int(width / (size * (0.59 if serif else 0.535))))
    lines, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + (1 if cur else 0) <= per:
            cur = f"{cur} {w}".strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    return lines + [cur] if cur else (lines or [""])


class Canvas:
    def __init__(self, model, mobile):
        self.m, self.s, self.parts = model, SIZES[mobile], []
        self.W, self.PAD = self.s["W"], self.s["PAD"]
        self.CW = self.W - 2 * self.PAD
        self.y = self.PAD - 6 if not mobile else self.PAD + 4

    def text(self, x, y, s, size, fill=INK, weight=None, serif=False, anchor="start"):
        wt = f' font-weight="{weight}"' if weight else ""
        an = f' text-anchor="{anchor}"' if anchor != "start" else ""
        self.parts.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{SERIF if serif else SANS}\' '
                          f'font-size="{size}"{wt}{an} fill="{fill}">{html.escape(s, quote=False)}</text>')

    def rect(self, x, y, w, h, fill, rx=2):
        self.parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 2):.1f}" height="{h}" fill="{fill}" rx="{rx}"/>')

    def para(self, s, size, fill, weight=None, serif=False, lead=1.3, width=None):
        for line in wrap(s, size, width or self.CW, serif):
            self.y += size
            self.text(self.PAD, self.y, line, size, fill, weight, serif)
            self.y += size * (lead - 1)

    def header(self):
        self.para(self.m["title"], self.s["title"], INK, 600, serif=True, lead=1.25)
        self.y += 3
        for sub in self.m.get("subs", []):
            self.para(sub, self.s["sub"], MUTED)
        self.y += 12

    def legend(self, items):
        """items: [(colour, label)] laid out in rows."""
        x, size = self.PAD, self.s["small"]
        self.y += 2
        for colour, label in items:
            w = 17 + len(label) * size * 0.54 + 18
            if x + w > self.W - self.PAD and x > self.PAD:
                x, self.y = self.PAD, self.y + size + 9
            self.rect(x, self.y, 11, 11, colour, rx=2)
            self.text(x + 16, self.y + 10, label, size, MUTED)
            x += w
        self.y += size + 12

    def footer(self):
        feet = self.m.get("feet", [])
        if feet:
            self.y += 4
        for f in feet:
            self.para(f, self.s["small"], MUTED)

    def svg(self):
        h = int(self.y + self.PAD - 8)
        data = html.escape(json.dumps(self.m, ensure_ascii=False), quote=False)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.W} {h}" width="{self.W}" height="{h}" '
                f'role="img" aria-label="{html.escape(self.m.get("aria", self.m["title"]))}">'
                f'<desc id="chart-data">{data}</desc><rect width="{self.W}" height="{h}" fill="{PAPER}"/>'
                + "".join(self.parts) + "</svg>\n")


# ---------------------------------------------------------------- renderers

def bar_rows(c, rows, value_room):
    """rows: [(label, frac, colour, value)]; label above a full-width bar."""
    s, max_w = c.s, c.CW - value_room
    for label, frac, colour, value in rows:
        for line in wrap(label, s["label"], c.CW):
            c.y += s["label"]
            c.text(c.PAD, c.y, line, s["label"])
            c.y += 3
        c.y += 4
        w = max_w * frac
        c.rect(c.PAD, c.y, w, s["bar"], colour)
        c.text(c.PAD + w + 8, c.y + s["bar"] / 2 + s["num"] * 0.36, value, s["num"], INK, 600)
        c.y += s["bar"] + 13


def r_funnel(c):
    rows = c.m["rows"]
    bar_rows(c, [(r["label"], r["frac"], NEUTRAL_DARK, r["value"]) for r in rows], 70)


def r_stance(c):
    rows = c.m["rows"]
    top = max(r["pct"] for r in rows) or 1
    bar_rows(c, [(r["label"], r["pct"] / top, STANCE[r["key"]], r["value"]) for r in rows], 60)


def r_top(c, mobile):
    s, rows = c.s, c.m["rows"]
    if mobile:
        max_w = c.CW - 70
        for r in rows:
            for line in wrap(r["quote"], s["label"], c.CW)[:3]:
                c.y += s["label"]
                c.text(c.PAD, c.y, line, s["label"])
                c.y += 3
            c.y += 4
            w = max_w * r["frac"]
            c.rect(c.PAD, c.y, w, 14, STANCE[r["key"]])
            c.text(c.PAD + w + 8, c.y + 12, r["value"], s["num"], INK, 600)
            c.y += 14 + 16
    else:
        qx, bx = c.PAD, c.PAD + 368
        max_w = c.W - c.PAD - bx - 62
        for r in rows:
            q = wrap(r["quote"], 13, 350)[0]
            q = q if len(q) == len(r["quote"]) else r["quote"]
            c.text(qx, c.y + 14, q if len(q) <= 54 else q[:51].rstrip() + "...", 13)
            c.text(qx, c.y + 30, r["value"], s["num"], INK, 600)
            w = max_w * r["frac"]
            c.rect(bx, c.y + 4, w, 16, STANCE[r["key"]])
            c.y += 38
        c.y += 4
    seen = []
    for r in rows:
        if r["key"] not in seen:
            seen.append(r["key"])
    order = ["agree", "agree_part", "mixed", "disagree", "none", "action"]
    labels = c.m.get("legend", {})
    c.legend([(STANCE[k], labels.get(k, LEGEND_DEFAULT[k])) for k in order if k in seen])


def r_frames(c, mobile):
    s, rows = c.s, c.m["rows"]
    top = max(max(r["comments"][1], (r.get("engagement") or ("", 0))[1]) for r in rows) or 1
    c.legend([(NEUTRAL_LIGHT, "Share of comments"), (NEUTRAL_DARK, "Share of engagement")]
             if any(r.get("engagement") for r in rows) else [(NEUTRAL_DARK, "Share of comments")])
    if mobile:
        max_w, x0 = c.CW - 150, c.PAD
    else:
        x0 = c.PAD + 210
        max_w = c.W - c.PAD - x0 - 140
    for r in rows:
        bars = [(r["comments"], NEUTRAL_LIGHT if r.get("engagement") else NEUTRAL_DARK)]
        if r.get("engagement"):
            bars.append((r["engagement"], NEUTRAL_DARK))
        if mobile:
            c.y += s["label"]
            c.text(c.PAD, c.y, r["label"], s["label"], INK, 600)
            c.y += 6
        else:
            c.text(x0 - 12, c.y + 12 + (6 if len(bars) > 1 else 0), r["label"], s["label"], INK, anchor="end")
        for (txt, pct), colour in bars:
            w = max_w * pct / top
            c.rect(x0, c.y, w, 13, colour)
            c.text(x0 + w + 8, c.y + 11.5, txt, s["small"], INK)
            c.y += 13 + 5
        c.y += 12 if mobile else 8


SBF_SUB = ("Each bar splits the frame's positioned comments by stance. "
           "A frame with both green and red in its bar is used by both sides.")


def r_sbf(c, mobile):
    s, rows = c.s, c.m["rows"]
    order = [k for k in ("agree", "mixed", "disagree") if k in c.m["cols"]]
    names = c.m["cols"]
    c.legend([(STANCE[k], names[k]) for k in order])
    x0 = c.PAD if mobile else c.PAD + 210
    bw = (c.CW if mobile else c.W - c.PAD - x0)
    for r in rows:
        if mobile:
            c.y += s["label"]
            c.text(c.PAD, c.y, r["label"], s["label"], INK, 600)
            c.y += 6
        else:
            c.text(x0 - 12, c.y + 15, r["label"], s["label"], INK, anchor="end")
        total = sum(r["cells"][k][1] for k in order) or 1
        x = x0
        for k in order:
            w = bw * r["cells"][k][1] / total
            if w > 0.5:
                c.rect(x, c.y, max(w - 2, 1), 20, STANCE[k], rx=1)
            x += w
        c.y += 20 + 4
        vals = " · ".join(f'{r["cells"][k][0]} {names[k].lower()}' for k in order)
        c.y += s["small"]
        c.text(x0, c.y, vals, s["small"], MUTED)
        c.y += 12 if mobile else 10


def render(model, mobile):
    c = Canvas(model, mobile)
    c.header()
    t = model["type"]
    if t == "funnel":
        r_funnel(c)
    elif t == "stance":
        r_stance(c)
    elif t == "top":
        r_top(c, mobile)
    elif t == "frames":
        r_frames(c, mobile)
    elif t == "sbf":
        r_sbf(c, mobile)
    c.footer()
    return c.svg()


# ---------------------------------------------------------------- extraction

BAR_PCT = re.compile(r"^([\d.]+)% of \w+$")


def _css(raw):
    rules = {}
    for m in re.finditer(r"\.([\w-]+)((?:\.[\w-]+)*)\s*\{([^}]*)\}", raw):
        rules["." + m.group(1) + m.group(2)] = dict(
            (k.strip(), v.strip()) for k, v in (p.split(":", 1) for p in m.group(3).split(";") if ":" in p))
    return rules


def _parse_marks(raw):
    rules = _css(raw)
    root = ET.fromstring(raw)
    ns, items = "{http://www.w3.org/2000/svg}", []

    def walk(node, dx, dy):
        for el in node:
            tag = el.tag.replace(ns, "")
            if tag == "g":
                m = re.match(r"translate\(([-\d.]+)[ ,]+([-\d.]+)\)", el.get("transform", ""))
                walk(el, dx + (float(m.group(1)) if m else 0), dy + (float(m.group(2)) if m else 0))
            elif tag == "text":
                items.append(dict(kind="text", cls=el.get("class", ""), x=float(el.get("x", 0)) + dx,
                                  y=float(el.get("y", 0)) + dy, anchor=el.get("text-anchor", "start"),
                                  text="".join(el.itertext()).strip()))
            elif tag == "rect" and el.get("x") is not None:
                cls = el.get("class", "")
                props = {}
                for p in cls.split():
                    props.update(rules.get("." + p, {}))
                op = el.get("opacity") or props.get("opacity") or "1"
                items.append(dict(kind="rect", x=float(el.get("x")) + dx, y=float(el.get("y")) + dy,
                                  w=float(el.get("width")), h=float(el.get("height")), cls=cls, op=float(op)))
    walk(root, 0, 0)
    return items, root.get("aria-label", "")


def _header(texts, rects):
    title = next(t for t in texts if t["cls"] == "h")["text"]
    first = min(r["y"] for r in rects)
    last = max(r["y"] + r["h"] for r in rects)
    subs = [t["text"] for t in sorted(texts, key=lambda t: t["y"])
            if t["cls"] == "t" and t["y"] < first - 4 and t["anchor"] == "start"]
    feet = [t for t in sorted(texts, key=lambda t: t["y"])
            if t["cls"] == "t" and t["y"] > last + 8 and t["anchor"] == "start"]
    return title, subs, feet


def _norm(x):
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", x.lower().replace("’", "'"))).strip()


def _lookup_stance(quote, comments):
    core = quote.strip().removesuffix("(reply)").strip().strip('"').strip()
    parts = [p for p in re.split(r"\.\.\.|…", core) if len(_norm(p)) > 6]
    if not parts:
        return None
    hits = [r for r in comments if all(_norm(p) in _norm(r["text"]) for p in parts)]
    if len({h["stance"] for h in hits}) != 1:
        return None
    s = hits[0]["stance"]
    return {"agree": "agree", "disagree": "disagree", "mixed": "mixed"}.get(s, "none")


def extract(path, comments=None):
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"<metadata>.*?</metadata>", "", raw, flags=re.S)
    m = re.search(r'<desc id="chart-data">(.*?)</desc>', raw, re.S)
    if m:
        model = json.loads(html.unescape(m.group(1)))
        if model["type"] == "sbf" and any(x.startswith("Cell value") for x in model.get("subs", [])):
            model["subs"] = [SBF_SUB]
        return model
    items, aria = _parse_marks(raw)
    texts = [i for i in items if i["kind"] == "text"]
    rects = [i for i in items if i["kind"] == "rect"]
    title, subs, feet_t = _header(texts, [r for r in rects if r["h"] > 12 or r["w"] > 12])
    model = dict(title=title, subs=subs, aria=aria)
    feet = [f["text"] for f in feet_t]

    if any(t["cls"] == "q" for t in texts):
        bars = sorted((r for r in rects if r["h"] > 12), key=lambda r: r["y"])
        swatches = sorted((r for r in rects if r["h"] <= 12 and r["w"] <= 12), key=lambda r: r["x"])
        legend_txt = {}
        for sw in swatches:
            lab = min((t for t in texts if t["cls"] == "t" and t["x"] > sw["x"]),
                      key=lambda t: (abs(t["y"] - (sw["y"] + 9)), t["x"]))
            legend_txt[(sw["cls"], round(sw["op"], 2))] = lab["text"]
        legend_names = set(legend_txt.values())
        feet = [f for f in feet if f not in legend_names]
        mx = max(b["w"] for b in bars)
        rows, legend = [], {}
        for b in bars:
            q = min((t for t in texts if t["cls"] == "q"), key=lambda t: abs(t["y"] - (b["y"] + 11)))
            n = min((t for t in texts if t["cls"] == "n"), key=lambda t: abs(t["y"] - (b["y"] + 26)))
            key = None
            if "prac" in b["cls"]:
                key = "action"
            elif "rej" in b["cls"]:
                key = "disagree"
            elif "acc" in b["cls"]:
                key = "agree"
            elif comments is not None:
                key = _lookup_stance(q["text"], comments)
            if key is None:
                key = "agree" if b["op"] >= 0.99 else "none"
            src_label = legend_txt.get((b["cls"], round(b["op"], 2)))
            if src_label and key in ("agree", "action") or (src_label and "rej" in b["cls"]):
                legend[key] = src_label
            rows.append(dict(quote=q["text"], value=n["text"], frac=b["w"] / mx, key=key))
        model.update(type="top", rows=rows, legend=legend)
    elif any(t["cls"] == "t" and t["anchor"] == "middle" for t in texts):
        heads = sorted((t for t in texts if t["cls"] == "t" and t["anchor"] == "middle"), key=lambda t: t["x"])
        cols = {stance_key(h["text"]): h["text"] for h in heads}
        rows = []
        for lab in sorted((t for t in texts if t["cls"] == "l"), key=lambda t: t["y"]):
            cells = sorted((r for r in rects if abs((r["y"] + r["h"] / 2) - (lab["y"] - 4)) < 12), key=lambda r: r["x"])
            vals = {}
            for h, r in zip(heads, cells):
                v = min((t for t in texts if t["cls"] == "n"),
                        key=lambda t: abs(t["x"] - (r["x"] + r["w"] / 2)) + abs(t["y"] - (r["y"] + 19)))
                vals[stance_key(h["text"])] = (v["text"], float(v["text"].rstrip("%")))
            rows.append(dict(label=lab["text"], cells=vals))
        model.update(type="sbf", cols=cols, rows=rows)
        if any(x.startswith("Cell value") for x in subs):
            model["subs"] = [SBF_SUB]
    elif sum(1 for t in texts if BAR_PCT.match(t["text"])) >= 2:
        pct_t = [t for t in texts if t["cls"] == "t" and BAR_PCT.match(t["text"])]
        rows = []
        for lab in sorted((t for t in texts if t["cls"] == "l"), key=lambda t: t["y"]):
            rr = sorted((r for r in rects if lab["y"] - 16 <= r["y"] <= lab["y"] + 20), key=lambda r: r["y"])
            vals = []
            for r in rr:
                t = min(pct_t, key=lambda t: abs(t["y"] - (r["y"] + 9)))
                vals.append((t["text"], float(BAR_PCT.match(t["text"]).group(1))))
            rows.append(dict(label=lab["text"], comments=vals[0], engagement=vals[1] if len(vals) > 1 else None))
        model.update(type="frames", rows=rows)
    else:
        bars = sorted(rects, key=lambda r: r["y"])
        mx = max(b["w"] for b in bars)
        rows = []
        for b in bars:
            mid = b["y"] + b["h"] / 2
            row_t = [t for t in texts if abs(t["y"] - (mid + 5)) <= 9]
            num = next(t for t in row_t if t["cls"] == "n")
            lab = next(t for t in row_t if t is not num and t["cls"] in ("t", "l", "lbl"))
            rows.append(dict(label=lab["text"], value=num["text"], frac=b["w"] / mx))
        if all(r["value"].endswith("%") for r in rows):
            model.update(type="stance", rows=[dict(label=r["label"], value=r["value"],
                                                   pct=float(r["value"].rstrip("%")), key=stance_key(r["label"]))
                                              for r in rows])
        else:
            model.update(type="funnel", rows=rows)
    model["feet"] = feet
    return model


def build(path, comments_csv=None):
    comments = list(csv.DictReader(open(comments_csv, encoding="utf-8"))) if comments_csv else None
    model = extract(path, comments)
    open(path, "w", encoding="utf-8").write(render(model, mobile=False))
    mobile_path = re.sub(r"\.svg$", "-mobile.svg", path)
    open(mobile_path, "w", encoding="utf-8").write(render(model, mobile=True))
    return model


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    csv_path = None
    if "--comments" in args:
        i = args.index("--comments")
        csv_path = args[i + 1]
        del args[i:i + 2]
    for p in args:
        m = build(p, csv_path)
        print(p, m["type"], len(m["rows"]), "rows")

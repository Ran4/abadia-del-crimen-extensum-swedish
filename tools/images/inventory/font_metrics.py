# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Metrics per font from auto_index.json: x-height/cap/asc/desc, baselines per line, intra-word gaps,
word gaps, line pitch; plus per-font character inventory. Usage: font_metrics.py GLYPHDIR"""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

G = Path(sys.argv[1])
idx = json.loads((G / "auto_index.json").read_text())["glyphs"]
XL = set("acemnoruvwxsz")  # x-height letters without asc/desc (fraktur s is round s)
lines = defaultdict(list)
for g in idx:
    lines[(g["font"], g["lang"], g["source"], g["line_text"])].append(g)
out = {}
for font in sorted(set(g["font"] for g in idx)):
    fl = {k: v for k, v in lines.items() if k[0] == font}
    rep = {"lines": []}
    xh, base_off = [], []
    intra, words = [], []
    for k, gl in fl.items():
        gl = sorted(gl, key=lambda g: g["ink_bbox"][0])
        xs = [g for g in gl if g["char"] in XL]
        if xs:
            bl = Counter(g["ink_bbox"][3] for g in xs).most_common(1)[0][0]
            top = Counter(g["ink_bbox"][1] for g in xs).most_common(1)[0][0]
        else:
            bl = top = None
        caps = [g for g in gl if g["char"].isupper()]
        rep["lines"].append({"lang": k[1], "image": k[2], "text": k[3], "baseline_y(last ink row of x-letters)": bl,
                             "xheight_top_y": top, "x_extent": [gl[0]["ink_bbox"][0], gl[-1]["ink_bbox"][2]],
                             "y_extent": [min(g["ink_bbox"][1] for g in gl), max(g["ink_bbox"][3] for g in gl)],
                             "caps_top_y": sorted(set(g["ink_bbox"][1] for g in caps))})
        if bl is not None:
            xh.append(bl - top + 1)
        for a, b in zip(gl, gl[1:]):
            gap = b["ink_bbox"][0] - a["ink_bbox"][2] - 1
            (intra if a["word"] == b["word"] and gap < 6 else words).append(gap)
    rep["x_height_px(median)"] = median(xh) if xh else None
    rep["intra_word_gap_px"] = dict(sorted(Counter(intra).items()))
    rep["inter_word_gap_px"] = dict(sorted(Counter(words).items()))
    # per char sizes
    per = defaultdict(list)
    for g in idx:
        if g["font"] == font:
            per[g["char"]].append(g)
    rep["inventory"] = {ch: {"n": len(v), "w_h": sorted(set((g["w"], g["h"]) for g in v)),
                             "langs": sorted(set(g["lang"] for g in v)),
                             "example": {"source": v[0]["source"], "ink_bbox": v[0]["ink_bbox"], "file": v[0]["file"]}}
                        for ch, v in sorted(per.items())}
    rep["chars"] = "".join(sorted(per))
    out[font] = rep
(G / "font_metrics.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
for f, r in out.items():
    print(f"== {f}: chars={r['chars']!r}")
    print("   x-height", r["x_height_px(median)"], "intra gaps", r["intra_word_gap_px"], "word gaps", r["inter_word_gap_px"])
    for ln in r["lines"]:
        print("   ", ln["lang"], ln["image"].split("/")[-1], repr(ln["text"]), "base", ln["baseline_y(last ink row of x-letters)"],
              "xtop", ln["xheight_top_y"], "x", ln["x_extent"], "y", ln["y_extent"], "caps", ln["caps_top_y"])

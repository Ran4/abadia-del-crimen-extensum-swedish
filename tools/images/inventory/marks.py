# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0", "numpy==2.3.2"]
# ///
"""Cut diacritic / dot models: rows strictly above the x-height top of the glyph's line, taken from the glyph's
_mask file (only that glyph's pixels). Writes GLYPHDIR/<font>/marks/*.png (+ x8 previews) and marks_index.json.
Usage: marks.py GLYPHDIR"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

G = Path(sys.argv[1])
idx = json.loads((G / "auto_index.json").read_text())["glyphs"]
met = json.loads((G / "font_metrics.json").read_text())
xtop = {}
for font, r in met.items():
    for ln in r["lines"]:
        xtop[(font, ln["lang"], ln["image"], ln["text"])] = ln["xheight_top_y"]
WANT = set("iíéáàêóśćńżjęą")
out = []; seen = set()
for g in idx:
    ch = g["char"]
    if ch not in WANT:
        continue
    key = (g["font"], g["lang"], g["source"], g["line_text"])
    top = xtop.get(key)
    if top is None:
        # lines without x-letters: use glyph's own stem start heuristics -> skip
        continue
    if ch in "ęą":  # ogonek is below baseline: cut rows below baseline instead
        continue
    m = np.array(Image.open(G / g["mask_file"]).convert("RGBA"))
    cx0, cy0 = g["crop_bbox"][0], g["crop_bbox"][1]
    cut = top - cy0 - 1  # rows above x-height top (leave 1 px gap)
    if cut <= 0:
        continue
    part = m[:cut]
    ys, xs = np.nonzero(part[..., 3] > 0)
    if len(xs) == 0:
        continue
    part = part[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    k = (g["font"], ch, part.shape, g["lang"])
    if (g["font"], ch, g["lang"]) in seen:
        continue
    seen.add((g["font"], ch, g["lang"]))
    d = G / g["font"] / "marks"; d.mkdir(exist_ok=True)
    nm = f"mark_of_{'U%04X' % ord(ch)}_{g['lang']}_{Path(g['source']).stem}_{cx0 + xs.min()}_{cy0 + ys.min()}"
    Image.fromarray(part).save(d / f"{nm}.png")
    bg = Image.new("RGBA", (part.shape[1], part.shape[0]), (0, 0, 90, 255)); bg.alpha_composite(Image.fromarray(part))
    bg.resize((part.shape[1] * 8, part.shape[0] * 8), Image.NEAREST).save(d / f"{nm}_x8.png")
    out.append({"font": g["font"], "base_char": ch, "lang": g["lang"], "source": g["source"],
                "mark_bbox_abs": [int(cx0 + xs.min()), int(cy0 + ys.min()), int(cx0 + xs.max()), int(cy0 + ys.max())],
                "size_wh": [int(part.shape[1]), int(part.shape[0])], "glyph_ink_bbox": g["ink_bbox"],
                "xheight_top_y": top, "file": f"{g['font']}/marks/{nm}.png"})
(G / "marks_index.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
for o in out:
    print(o["font"], o["base_char"], o["lang"], o["source"].split("/")[-1], "mark bbox", o["mark_bbox_abs"], "size", o["size_wh"], "glyph", o["glyph_ink_bbox"])

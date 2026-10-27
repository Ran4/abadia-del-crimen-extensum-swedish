# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow", "numpy"]
# ///
"""HUD (res/<lang>/marcador.png) day-word glyphs: manual boxes (inclusive), font-colour masks,
and a reconstructed clean background for the word area.
Font colours (VERIFIED from palettes): greys/whites #ecebec #d7d8d8 #abb2b3 #9ca2a4 and reds #96020a #6d0211 #54020c.
Usage: hud_glyphs.py RES OUTDIR"""
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

RES = Path(sys.argv[1]); OUT = Path(sys.argv[2]); (OUT / "hud").mkdir(parents=True, exist_ok=True)
FONT = {(0xec, 0xeb, 0xec), (0xd7, 0xd8, 0xd8), (0xab, 0xb2, 0xb3), (0x9c, 0xa2, 0xa4),
        (0x96, 0x02, 0x0a), (0x6d, 0x02, 0x11), (0x54, 0x02, 0x0c)}
# (lang, char, x0, y0, x1, y1) inclusive boxes, from pixel dumps (see images.md)
BOXES = [
    ("es", "D", 1, 1, 17, 17), ("es", "í", 19, 5, 22, 17), ("es", "a", 24, 7, 35, 17),
    ("en", "D", 1, 1, 17, 17), ("en", "a", 18, 6, 29, 17), ("en", "y", 30, 4, 38, 18),
    ("it", "D", 1, 1, 17, 17), ("it", "i", 19, 5, 23, 17), ("it", "e", 24, 7, 35, 17),
    ("fr", "J", 1, 0, 12, 16), ("fr", "o", 13, 7, 19, 16), ("fr", "u", 20, 7, 28, 16), ("fr", "r", 29, 5, 35, 16),
    ("pl", "D", 1, 1, 13, 17), ("pl", "z", 14, 7, 19, 17), ("pl", "i", 20, 4, 22, 17), ("pl", "e", 23, 7, 30, 17),
    ("pl", "ń", 31, 4, 38, 17),
]
WORD = {"es": "Día", "en": "Day", "it": "Die", "fr": "Jour", "pl": "Dzień"}
arr = {l: np.array(Image.open(RES / l / "marcador.png").convert("RGBA")) for l in WORD}


def fontmask(a):
    rgb = a[..., :3]
    m = np.zeros(a.shape[:2], bool)
    for c in FONT:
        m |= np.all(rgb == np.array(c), axis=2)
    return m


index = []
for (l, ch, x0, y0, x1, y1) in BOXES:
    a = arr[l]
    crop = a[y0:y1 + 1, x0:x1 + 1]
    fm = fontmask(crop)
    only = crop.copy(); only[~fm] = 0
    name = f"{ch if ch.isascii() else 'U%04X' % ord(ch)}__{l}_marcador_{x0}_{y0}"
    Image.fromarray(crop).save(OUT / "hud" / f"{name}.png")
    Image.fromarray(only).save(OUT / "hud" / f"{name}_mask.png")
    index.append({"font": "hud", "char": ch, "codepoint": "U+%04X" % ord(ch), "lang": l,
                  "source": f"res/{l}/marcador.png", "box_incl": [x0, y0, x1, y1], "w": x1 - x0 + 1, "h": y1 - y0 + 1,
                  "word": WORD[l], "file": f"hud/{name}.png", "mask_file": f"hud/{name}_mask.png",
                  "font_pixels": int(fm.sum())})
# word crops
for l, w in WORD.items():
    Image.fromarray(arr[l][0:21, 0:42]).save(OUT / "hud" / f"WORD_{l}_{w.encode('ascii', 'replace').decode()}_x0-41_y0-20.png")
# clean background reconstruction for x 0..41, y 0..21: per pixel, most common value among languages
# where that pixel is NOT a font colour; report pixels where every language has a font colour.
X1, Y1 = 42, 22
bg = np.zeros((Y1, X1, 4), np.uint8); unresolved = []
for y in range(Y1):
    for x in range(X1):
        vals = [tuple(arr[l][y, x]) for l in WORD if tuple(arr[l][y, x][:3]) not in FONT]
        if vals:
            bg[y, x] = Counter(vals).most_common(1)[0][0]
        else:
            bg[y, x] = (5, 2, 4, 255); unresolved.append([x, y])
Image.fromarray(bg).save(OUT / "hud" / "BACKGROUND_reconstructed_x0-41_y0-21.png")
Image.fromarray(bg).resize((X1 * 10, Y1 * 10), Image.NEAREST).save(OUT / "hud" / "BACKGROUND_reconstructed_x10_preview.png")
(OUT / "hud" / "hud_index.json").write_text(json.dumps({"glyphs": index, "background_unresolved_pixels": unresolved,
    "font_colours": ["#ecebec", "#d7d8d8", "#abb2b3", "#9ca2a4", "#96020a", "#6d0211", "#54020c"]}, indent=1, ensure_ascii=False))
print(len(index), "hud glyphs; unresolved bg pixels:", unresolved)

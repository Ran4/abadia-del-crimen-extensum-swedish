# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Merge auto_index.json, hud/hud_index.json, marks_index.json, font_metrics.json into GLYPHDIR/index.json
with per-font descriptions and Swedish-letter notes. Usage: merge_index.py GLYPHDIR"""
import json, sys
from collections import defaultdict
from pathlib import Path

G = Path(sys.argv[1])
auto = json.loads((G / "auto_index.json").read_text())
hud = json.loads((G / "hud" / "hud_index.json").read_text())
marks = json.loads((G / "marks_index.json").read_text())
met = json.loads((G / "font_metrics.json").read_text())

FONTS = {
    "fraktur": {
        "used_in": "res/{es,en,it,fr,de}/intro/{manuydani,novela,pacoyjuan,pelicula}.png (de == en byte-identical)",
        "style": "anti-aliased blackletter (Fraktur), fill (253,246,231) cream, AA edge pixels are opaque blends toward "
                 "(29,8,27); outer glow colour (29,8,27) with alpha ~230/164/92/51/24/11/3/0 at 1..8 px from ink; "
                 "everything else alpha 0",
        "metrics": "x-height 17 rows (e.g. rows 98..114), ascender/cap top 21 rows above baseline (rows 93/123/153 vs "
                   "baselines 114/144/174), descender 4 px (p,q,y in-line) up to 8 px ('by' y tail); baseline pitch 30 px; "
                   "intra-word ink gap 1-2 px (0..3), word gap 10-12 px; text left-aligned with indents, not centered",
        "same_rendering_across_langs": "VERIFIED: en vs es 'Eco' identical after 1 px shift (sumabs 28/78580); it differs slightly "
                                       "(56 px >40 levels, sub-pixel AA)",
    },
    "fraktur_pl": {
        "used_in": "res/pl/intro/{manuydani,novela,pacoyjuan,pelicula}.png",
        "style": "a DIFFERENT blackletter rendering (redrawn by the Polish translator): thinner, x-height 14, glow colour (28,2,21); "
                 "do NOT mix with 'fraktur' glyphs (en vs pl 'Eco': 309 px differ >40)",
    },
    "pulsa": {
        "used_in": "res/{es,en(=it=fr=de),pl}/intro/pulsa.png",
        "style": "blackletter ('Old English'-like) fill (253,246,231) with grey AA shading, opaque black (0,0,0) 2 px outline, "
                 "3rd px partially transparent black, nothing beyond; x-height 12 (rows 171..182), cap top row 166, "
                 "descender to row 185; drawn OVER monje.png+logo.png (outline visible against the artwork); "
                 "text centered around x~160 (es 76..243, en 101..219, pl 94..224)",
    },
    "loadline": {
        "used_in": "bottom line of res/<lang>/intro/loading.png (rows 181..193)",
        "style": "1-bit, 1-px-stroke joined handwriting, colour (252,254,252) (es) / white, alpha 0 or 255 only; caps 8 rows "
                 "(182..189), x-height 6 (184..189), baseline row 189, descenders to 192; letters often connected by joins "
                 "(vertical cuts in this index are approximate); word gap 4-7 px",
    },
    "script": {
        "used_in": "conjunctions y/and/e/et/i in manuydani, pacoyjuan, pelicula",
        "style": "anti-aliased handwriting, cream (253,246,231) with partial alpha, NO dark glow; x-height ~9 (en 'and' rows 149..157), "
                 "ascender 'd' 15 rows; only glyphs a d e i n t y exist",
    },
    "hud": {
        "used_in": "res/<lang>/marcador.png day word, x 1..38, y 0..18 (screen y = 176 + y)",
        "style": "hand-pixelled gothic: greys #ecebec #d7d8d8 #abb2b3 #9ca2a4 + 'blood' band #96020a #6d0211 #54020c on rows ~13..17, "
                 "on opaque near-black #050204 with ivy greens; fr uses a different (outlined, 2-grey) variant",
    },
}
by_font = defaultdict(list)
for g in auto["glyphs"]:
    by_font[g["font"]].append(g)
for g in hud["glyphs"]:
    by_font["hud"].append(g)
fonts = {}
for f, desc in FONTS.items():
    gl = by_font.get(f, [])
    chars = sorted(set(g["char"] for g in gl))
    fonts[f] = dict(desc)
    fonts[f]["chars_available"] = "".join(chars)
    fonts[f]["n_glyph_crops"] = len(gl)
    sw = {}
    for ch in "ÅÄÖåäö":
        base = {"Å": "A", "Ä": "A", "Ö": "O", "å": "a", "ä": "a", "ö": "o"}[ch]
        sw[ch] = {"exists": ch in chars, "base_letter_exists": base in chars,
                  "mark_needed": "ring" if ch in "Åå" else "diaeresis"}
    fonts[f]["swedish"] = sw
    if f in met:
        fonts[f]["measured"] = {k: met[f][k] for k in ("x_height_px(median)", "intra_word_gap_px", "inter_word_gap_px")}
        fonts[f]["lines"] = met[f]["lines"]
index = {
    "about": "Glyph inventory of text-bearing images of La Abadia del Crimen Extensum (phase A). Coordinates are pixel "
             "coordinates in the source PNG (0-based); ink_bbox/crop_bbox/box_incl are inclusive [x0,y0,x1,y1]. "
             "'file' = full RGBA crop (may contain neighbour pixels), 'mask_file' = only this glyph's pixels "
             "(component mask dilated 1 px). Ink = lum*alpha/255 >= 128.",
    "fonts": fonts,
    "glyphs": auto["glyphs"] + hud["glyphs"],
    "marks": marks,
    "hud_background": {"file": "hud/BACKGROUND_reconstructed_x0-41_y0-21.png",
                       "unresolved_pixels_filled_with_050204": hud["background_unresolved_pixels"]},
    "no_diaeresis_or_ring_in_any_image_font": True,
}
(G / "index.json").write_text(json.dumps(index, indent=1, ensure_ascii=False))
for f, d in fonts.items():
    print(f, d["n_glyph_crops"], repr(d["chars_available"]))
    print("   ", {k: (v["exists"], v["base_letter_exists"]) for k, v in d["swedish"].items()})

# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0", "numpy==2.3.2", "scipy==1.16.1"]
# ///
"""Cut glyphs out of the language versions of the intro images, per font, using connected components.

ink weight v = luminance * alpha/255 (premultiplied over black); components = 8-connected v >= THR.
Components whose x-ranges overlap are merged (i-dots, accents, colons, two-part glyphs).
Merged components are grouped into words by horizontal gaps >= WORDGAP; the transcription's words
(split on spaces) must match in number; words written as {xyz} are skipped (other font).
Within a word, #components must equal #chars (a char may be a multi-char token in [..], e.g. [oe]).
Lines whose counts don't match are reported and handled by explicit manual boxes (MANUAL).

Outputs into OUT/<font>/: <char-name>__<lang>_<image>_<x0>_<y0>.png (RGBA crop of bbox padded by PAD,
all pixels), ..._mask.png (only this glyph's pixels: component mask dilated by 1, other pixels cleared),
index.json; and OUT/<font>_verify.png sheets.
Usage: glyph_inventory.py RES OUT"""
import json, sys, unicodedata
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

RES = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)

# (font, lang, image, x0, y0, x1, y1, text, thr, wordgap)
L = []
def add(font, lang, img, box, text, thr=128, gap=5):
    L.append((font, lang, img, *box, text, thr, gap))

FR = "fraktur"
# --- manuydani
for lang, dy in (("es", 0), ("en", 0), ("it", 0), ("fr", 6)):
    add(FR, lang, "manuydani", (0, 104 + dy, 320, 133 + dy), "Manuel Pazos")
add(FR, "es", "manuydani", (90, 133, 320, 166), "Daniel Celemín")
add(FR, "en", "manuydani", (90, 133, 320, 166), "Daniel Celemin")
# --- novela
add(FR, "es", "novela", (0, 90, 320, 117), "en la novela")
add(FR, "es", "novela", (0, 119, 320, 147), "“El Nombre de la Rosa”")
add(FR, "es", "novela", (0, 150, 320, 177), "de Umberto Eco")
add(FR, "en", "novela", (0, 90, 320, 120), "inspired by the novel")
add(FR, "en", "novela", (0, 121, 320, 149), "“The Name of the Rose”")
add(FR, "en", "novela", (0, 150, 320, 186), "by Umberto Eco")
add(FR, "it", "novela", (0, 105, 320, 132), "liberamente tratto dal libro")
add(FR, "it", "novela", (0, 134, 320, 162), "\"Il Nome della Rosa\"")
add(FR, "it", "novela", (0, 165, 320, 192), "di Umberto Eco")
add(FR, "fr", "novela", (0, 97, 320, 127), "inspiré par le roman")
add(FR, "fr", "novela", (0, 128, 320, 153), "“Le Nom de la Rose”")
add(FR, "fr", "novela", (0, 157, 320, 184), "d’Umberto Eco")
# --- pacoyjuan
add(FR, "es", "pacoyjuan", (0, 90, 320, 121), "inspirado en la obra de")
add(FR, "es", "pacoyjuan", (0, 120, 320, 150), "Paco Menéndez")
add(FR, "es", "pacoyjuan", (78, 149, 320, 183), "Juan Delcán")
add(FR, "en", "pacoyjuan", (0, 89, 320, 121), "based on the work of")
add(FR, "it", "pacoyjuan", (0, 90, 320, 117), "basato sul lavoro_di")
add(FR, "fr", "pacoyjuan", (0, 97, 320, 129), "à partir de l’[oe]uvre de")
# --- pelicula
add(FR, "es", "pelicula", (40, 90, 320, 121), "en la película de")
add(FR, "es", "pelicula", (0, 121, 320, 151), "Jean Jacques Annaud")
add(FR, "es", "pelicula", (0, 150, 320, 177), "del mismo nombre")
add(FR, "en", "pelicula", (0, 101, 320, 133), "in Jean-Jacques Annaud’s")
add(FR, "en", "pelicula", (0, 131, 320, 163), "film of the same name")
add(FR, "it", "pelicula", (0, 101, 320, 133), "dall’omonimo film di")
add(FR, "it", "pelicula", (0, 131, 320, 163), "Jean-Jacques Annaud")
add(FR, "fr", "pelicula", (0, 97, 320, 129), "dans le film de")
add(FR, "fr", "pelicula", (0, 127, 320, 159), "Jean-Jacques Annaud du")
add(FR, "fr", "pelicula", (0, 159, 320, 185), "même nom")

FP = "fraktur_pl"
add(FP, "pl", "manuydani", (0, 108, 320, 140), "Manuel Pazos")
add(FP, "pl", "manuydani", (85, 138, 320, 165), "Daniel Celemin")
add(FP, "pl", "novela", (0, 92, 320, 125), "gra inspirowana powieścią")
add(FP, "pl", "novela", (0, 124, 320, 156), "„Imię róży”")
add(FP, "pl", "novela", (0, 155, 320, 181), "Umberta Eco")
add(FP, "pl", "pacoyjuan", (0, 97, 320, 130), "na podstawie dzieła")
add(FP, "pl", "pacoyjuan", (0, 128, 320, 160), "Paca Menéndeza")
add(FP, "pl", "pacoyjuan", (75, 158, 320, 189), "Juana Delcána")
add(FP, "pl", "pelicula", (0, 90, 320, 121), "i filmem")
add(FP, "pl", "pelicula", (0, 120, 320, 151), "Jeana-Jacques’a Annauda")
add(FP, "pl", "pelicula", (0, 151, 320, 181), "o tym samym tytule")

PU = "pulsa"
add(PU, "es", "pulsa", (0, 160, 320, 192), "Pulsa para empezar")
add(PU, "en", "pulsa", (0, 160, 320, 192), "Press to start")
add(PU, "pl", "pulsa", (0, 160, 320, 192), "Naciśnij spację")

LD = "loadline"
add(LD, "es", "loading", (0, 176, 320, 200), "CARGANDO: Por favor, espere", gap=4)
add(LD, "en", "loading", (0, 176, 320, 200), "LOADING: Please wait...", gap=4)
add(LD, "it", "loading", (0, 176, 320, 200), "CARICAMENTO: Attendere per favore", gap=4)
add(LD, "fr", "loading", (0, 176, 320, 200), "CHARGEMENT: veuillez patienter", gap=4)
add(LD, "pl", "loading", (0, 176, 320, 200), "WCZYTYWANIE: Proszę czekać...", gap=4)

SC = "script"
add(SC, "es", "manuydani", (60, 133, 92, 170), "y")
add(SC, "en", "manuydani", (40, 133, 90, 170), "and")
add(SC, "it", "manuydani", (60, 133, 90, 170), "e")
add(SC, "fr", "manuydani", (40, 139, 90, 175), "et")
add(SC, "pl", "manuydani", (40, 138, 85, 170), "i")
add(SC, "es", "pelicula", (20, 100, 40, 125), "y")
add(SC, "en", "pelicula", (20, 74, 62, 96), "and")
add(SC, "it", "pelicula", (30, 78, 56, 96), "e")
add(SC, "es", "pacoyjuan", (55, 149, 78, 183), "y")
add(SC, "en", "pacoyjuan", (40, 149, 82, 183), "and")
add(SC, "it", "pacoyjuan", (50, 149, 78, 183), "e")
add(SC, "fr", "pacoyjuan", (40, 157, 72, 190), "et")
add(SC, "pl", "pacoyjuan", (40, 158, 75, 189), "i")

# per-line overrides keyed by (font, lang, image, text):
#  split: list of (x, ylim|None, refine) -> group containing column x is cut: left = cols < x (and rows < ylim)
#  join:  list of x -> group starting at column x is joined to the previous group
#  gap:   word gap override
OV = {}
for lg in ("es", "en", "it", "fr"):
    OV[(FR, lg, "manuydani", "Manuel Pazos")] = {"split": [(128, None, False)]}
OV[(FR, "en", "novela", "by Umberto Eco")] = {"split": [(49, 176, False)]}
OV[(FR, "fr", "novela", "d’Umberto Eco")] = {"split": [(86, 170, False)]}
OV[(FR, "it", "pacoyjuan", "basato sul lavoro_di")] = {"split": [(206, None, True)]}
OV[(FR, "es", "novela", "“El Nombre de la Rosa”")] = {"join": [44, 280]}
OV[(FR, "en", "novela", "“The Name of the Rose”")] = {"join": [44, 276], "split": [(262, None, True)]}
OV[(FR, "it", "novela", "\"Il Nome della Rosa\"")] = {"join": [31, 243]}
OV[(FR, "fr", "novela", "“Le Nom de la Rose”")] = {"join": [45, 246], "split": [(232, None, True)]}
OV[(FP, "pl", "novela", "gra inspirowana powieścią")] = {"split": [(110, None, True), (234, None, True)]}
OV[(FP, "pl", "novela", "„Imię róży”")] = {"split": [(46, None, False), (121, None, True)], "join": [42, 144]}
OV[(FP, "pl", "novela", "Umberta Eco")] = {"split": [(90, None, True)]}
OV[(FP, "pl", "pacoyjuan", "na podstawie dzieła")] = {"split": [(189, None, True)]}
OV[(FP, "pl", "pelicula", "i filmem")] = {"split": [(45, None, True), (54, None, True)]}
OV[(FP, "pl", "pelicula", "o tym samym tytule")] = {"split": [(67, 175, False), (113, None, True), (186, 175, False)]}
OV[(PU, "es", "pulsa", "Pulsa para empezar")] = {"join": [191, 196]}
OV[(PU, "pl", "pulsa", "Naciśnij spację")] = {"join": [154]}
OV[(SC, "pl", "manuydani", "i")] = {"join": [73]}
OV[(SC, "pl", "pacoyjuan", "i")] = {"join": [66]}
OV[(LD, "es", "loading", "CARGANDO: Por favor, espere")] = {"split": [(186, None, False), (229, None, False)]}
OV[(LD, "en", "loading", "LOADING: Please wait...")] = {"split": [(179, None, False), (186, None, False), (220, None, False)]}
OV[(LD, "it", "loading", "CARICAMENTO: Attendere per favore")] = {"split": [(167, None, False), (184, None, False), (241, None, False)]}
OV[(LD, "fr", "loading", "CHARGEMENT: veuillez patienter")] = {"split": [(69, None, False)] + [(x, None, False) for x in (164, 169, 178, 182, 187, 192, 198, 216, 224, 229, 232, 238, 247, 252, 257)]}
OV[(LD, "pl", "loading", "WCZYTYWANIE: Proszę czekać...")] = {"split": [(104, None, False), (109, None, False), (119, None, False), (124, None, False)] + [(x, None, False) for x in (179, 195, 200, 215, 221, 230)]}

ONLY = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
PAD = 1


def tokens(word):
    out = []; i = 0
    while i < len(word):
        if word[i] == "[":
            j = word.index("]", i); out.append({"oe": "œ"}.get(word[i + 1:j], word[i + 1:j])); i = j + 1
        elif word[i] == "_":
            i += 1
        else:
            out.append(word[i]); i += 1
    return out


def cname(ch):
    if ch.isalnum() and ch.isascii():
        return ("U_" if ch.isupper() else "") + ch
    try:
        return unicodedata.name(ch).replace(" ", "_")
    except ValueError:
        return "U%04X" % ord(ch)


index = []; problems = []
cache = {}
for (font, lang, img, x0, y0, x1, y1, text, thr, gap) in L:
    if ONLY and font not in ONLY:
        continue
    key = (lang, img)
    if key not in cache:
        cache[key] = np.array(Image.open(RES / lang / "intro" / f"{img}.png").convert("RGBA"))
    a = cache[key]; af = a.astype(float)
    v = (0.299 * af[..., 0] + 0.587 * af[..., 1] + 0.114 * af[..., 2]) * af[..., 3] / 255
    sub = v[y0:y1, x0:x1] >= thr
    ov = OV.get((font, lang, img, text), {})
    gap = ov.get("gap", gap)
    lab, n = ndimage.label(sub, structure=np.ones((3, 3)))
    comps = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        mk = lab == (i + 1)
        npx = int(mk.sum()); hh = sl[0].stop - sl[0].start
        ys, xs = np.nonzero(mk)
        bx = float(xs[ys == ys.max()].mean())  # mean x of bottom row
        comps.append({"x0": sl[1].start, "x1": sl[1].stop, "mask": mk, "mark": npx < 12 and hh <= 6, "bx": bx})
    comps.sort(key=lambda c: c["x0"])
    mains = []
    for c in [c for c in comps if not c["mark"]]:
        if mains and c["x0"] < mains[-1]["x1"]:
            m = mains[-1]; m["x1"] = max(m["x1"], c["x1"]); m["mask"] = m["mask"] | c["mask"]
        else:
            mains.append(dict(c))
    marks = []
    for c in [c for c in comps if c["mark"]]:
        ov_m = [m for m in mains if c["x0"] < m["x1"] and m["x0"] < c["x1"]]
        if len(ov_m) == 1:
            tgt = ov_m[0]
        elif len(ov_m) > 1:
            inside = [m for m in ov_m if m["x0"] <= c["bx"] < m["x1"]]
            tgt = inside[0] if inside else min(ov_m, key=lambda m: abs((m["x0"] + m["x1"]) / 2 - c["bx"]))
        else:
            tgt = None
        if tgt is not None:
            tgt["mask"] = tgt["mask"] | c["mask"]
        else:
            if marks and c["x0"] < marks[-1]["x1"]:  # mark-mark overlap (colon)
                marks[-1]["mask"] = marks[-1]["mask"] | c["mask"]; marks[-1]["x1"] = max(marks[-1]["x1"], c["x1"])
            else:
                marks.append(dict(c))
    merged = sorted(mains + marks, key=lambda c: c["x0"])
    # splits
    for (sx, ylim, refine) in ov.get("split", []):
        lx = sx - x0
        g = next((m for m in merged if m["x0"] <= lx < m["x1"]), None)
        if g is None:
            print("  split column not in any group", font, lang, img, sx); continue
        if refine:
            cand = [cx for cx in range(lx - 2, lx + 3) if g["x0"] < cx < g["x1"]]
            colsum = {cx: int(g["mask"][:, cx].sum()) for cx in cand}
            lx = min(cand, key=lambda cx: (colsum[cx], abs(cx - (sx - x0))))
        cols = np.arange(g["mask"].shape[1])[None, :]; rows = np.arange(g["mask"].shape[0])[:, None]
        left_sel = cols < lx
        if ylim is not None:
            left_sel = left_sel & (rows < (ylim - y0))
        lm = g["mask"] & left_sel; rm = g["mask"] & ~left_sel
        merged.remove(g)
        for mm in (lm, rm):
            xs = np.nonzero(mm.any(axis=0))[0]
            merged.append({"x0": int(xs.min()), "x1": int(xs.max()) + 1, "mask": mm})
        merged.sort(key=lambda c: c["x0"])
        print(f"  split {font} {lang} {img} at x={lx + x0}{' (refined from %d)' % sx if refine and lx + x0 != sx else ''}")
    for jx in ov.get("join", []):
        k = next((i for i, m in enumerate(merged) if m["x0"] == jx - x0), None)
        if not k:
            print("  join target not found", font, lang, img, jx); continue
        p_, c_ = merged[k - 1], merged[k]
        p_["mask"] = p_["mask"] | c_["mask"]; p_["x1"] = max(p_["x1"], c_["x1"]); merged.pop(k)
    for m in merged:
        ys, xs = np.nonzero(m["mask"]); m["y0"], m["y1"] = int(ys.min()), int(ys.max()) + 1
        m["x0"], m["x1"] = int(xs.min()), int(xs.max()) + 1
    # words
    words = []
    for c in merged:
        if words and c["x0"] - words[-1][-1]["x1"] < gap:
            words[-1].append(c)
        else:
            words.append([c])
    twords = text.split(" ")
    status = "ok"
    if len(words) != len(twords):
        status = f"WORDCOUNT {len(words)} vs {len(twords)}"
    else:
        for w, tw in zip(words, twords):
            if tw.startswith("{"):
                continue
            tk = tokens(tw)
            if len(w) != len(tk):
                status = f"CHARCOUNT word '{tw}': {len(w)} comps vs {len(tk)} chars; comps x=" + ",".join(f"{c['x0']+x0}-{c['x1']+x0-1}" for c in w)
                break
    line = {"font": font, "lang": lang, "image": f"{lang}/intro/{img}.png", "text": text, "status": status,
            "n_words": len(words), "word_x": [[w[0]["x0"] + x0, w[-1]["x1"] + x0 - 1] for w in words]}
    if status != "ok":
        problems.append(line)
        print("PROBLEM", font, lang, img, repr(text), status, "word x:", line["word_x"])
        continue
    fdir = OUT / font; fdir.mkdir(exist_ok=True)
    for w, tw in zip(words, twords):
        if tw.startswith("{"):
            continue
        for c, ch in zip(w, tokens(tw)):
            gx0, gy0, gx1, gy1 = c["x0"] + x0, c["y0"] + y0, c["x1"] + x0, c["y1"] + y0  # exclusive
            bx0, by0, bx1, by1 = max(0, gx0 - PAD), max(0, gy0 - PAD), min(a.shape[1], gx1 + PAD), min(a.shape[0], gy1 + PAD)
            crop = Image.fromarray(a[by0:by1, bx0:bx1])
            # masked: this glyph's components dilated by 1 (AA ring)
            msk = c["mask"]
            msk = ndimage.binary_dilation(msk, structure=np.ones((3, 3)), iterations=1)
            full = np.zeros(a.shape[:2], bool); full[y0:y1, x0:x1] = msk
            ma = a.copy(); ma[~full] = 0
            mcrop = Image.fromarray(ma[by0:by1, bx0:bx1])
            fn = f"{cname(ch)}__{lang}_{img}_{gx0}_{gy0}"
            crop.save(fdir / f"{fn}.png"); mcrop.save(fdir / f"{fn}_mask.png")
            index.append({"font": font, "char": ch, "codepoint": "U+%04X" % ord(ch[0]) if len(ch) == 1 else ch,
                          "lang": lang, "source": f"res/{lang}/intro/{img}.png",
                          "ink_bbox": [gx0, gy0, gx1 - 1, gy1 - 1], "crop_bbox": [bx0, by0, bx1 - 1, by1 - 1],
                          "w": gx1 - gx0, "h": gy1 - gy0, "word": tw.replace("_", " "), "line_text": text, "file": f"{font}/{fn}.png",
                          "mask_file": f"{font}/{fn}_mask.png"})

(OUT / "auto_index.json").write_text(json.dumps({"glyphs": index, "problems": problems}, indent=1, ensure_ascii=False))
print(len(index), "glyphs;", len(problems), "problem lines")

# verification sheets: per font, every glyph at 4x with its char label
for font in sorted(set(g["font"] for g in index)):
    gl = [g for g in index if g["font"] == font]
    S = 4; cell_w = max(g["crop_bbox"][2] - g["crop_bbox"][0] + 1 for g in gl) * S + 6
    cell_h = max(g["crop_bbox"][3] - g["crop_bbox"][1] + 1 for g in gl) * S + 16
    cols = max(1, 1900 // cell_w); rows = (len(gl) + cols - 1) // cols
    sh = Image.new("RGB", (cols * cell_w, rows * cell_h), (40, 40, 40)); d = ImageDraw.Draw(sh)
    for i, g in enumerate(gl):
        im = Image.open(OUT / g["file"]).convert("RGBA")
        bg = Image.new("RGBA", im.size, (0, 0, 110, 255)); bg.alpha_composite(im)
        cx, cy = (i % cols) * cell_w, (i // cols) * cell_h
        d.text((cx + 2, cy), f"{g['char']} {g['lang']}", fill=(255, 255, 0))
        sh.paste(bg.convert("RGB").resize((im.width * S, im.height * S), Image.NEAREST), (cx, cy + 14))
    sh.save(OUT / f"{font}_verify.png"); print(font, "verify sheet", sh.size)

# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Build the Swedish credit screen res/de/intro/novela.png:
    "efter romanen" / "”Rosens namn”" / "av Umberto Eco"            (GLOSSARY §8)

Deterministic. Inputs (read-only):
  - work/jar/res/es/intro/novela.png   base: "en la novela" / "“El Nombre de la Rosa”" /
                                       "de Umberto Eco". Everything outside the three text lines
                                       and their glow is kept byte for byte (RGB of transparent
                                       pixels included).
  - work/jar/res/en/intro/novela.png   only to check that the base choice does not matter
                                       outside the text (es and en differ only there) and
  - work/jar/res/de/intro/novela.png   that de == en byte for byte (its colour type, RGBA, is kept)
  - tools/images/fraktur.py            the Fraktur kit (imported, never modified; bytecode off so
                                       no __pycache__ is written next to it)
  - through fraktur.py also:           work/jar/res/{es,en,fr,it}/intro/{manuydani,pacoyjuan,
                                       novela,pelicula}.png and work/phaseA/images/glyphs/
                                       {index.json,font_metrics.json,fraktur/*_mask.png}
                                       (checked with strace: nothing else in the project is read)
Output:
  - assets_sv/res/de/intro/novela.png  (8-bit RGBA, IHDR + one IDAT + IEND, no gAMA/iCCP)

What it does (FORMAT §6.1-§6.4, images.md §2.6 and §3.1):
  1. Canvas = es novela in coverage space (fraktur.Canvas.shipped; novela has no script ink).
     The old line 1 and line 2 are erased as whole connected components (their ink, their AA
     fringe and, at render, their glow); the old line 3 is erased letter-exact (its Phase A
     letters), after "Umberto Eco" has been lifted as shipped coverage (fraktur.letters()).
     Check: no coverage at all is left anywhere in the image (es novela holds only these lines).
  2. Line 1 "efter romanen": typeset with the font's own glyphs, advances and word space, left
     ink edge X1, baseline 114 (es: "en la novela" starts at x 28).
  3. Line 2 "”Rosens namn”": the shipped ” at both ends (Swedish style), the shipped R; left ink
     edge X2, baseline 144 (es/en: the opening quote's ink starts at x 40). The kit fits the
     capital 1 px of ink after the opening ” (the gap of the shipped “E, “T, “L).
  4. Line 3 "av Umberto Eco": "Umberto Eco" is the shipped es letters (coverage) moved by DX3
     whole pixels; "av" is typeset before its U with the font's word space (line_before), and
     DX3 = align_before(...) puts the left ink edge of "av" at X3 (es/en: line 3 starts at x 40,
     with line 2). Baseline 174 as shipped.
  5. Render: the glow is regenerated from the union of all cores (kit colour model); pixels
     farther than 6 px from any changed coverage keep the base's bytes.
     Then the moved name takes the shipped pixels back: every pixel of the moved name and its
     glow whose whole glow support (Chebyshev GLOW_R = 6, the shipped glow's measured reach,
     work/phaseD/novela/glowreach.py) holds exactly the coverage its es source pixel had around
     it is copied from es byte for byte. Only pixels with "av" or the erased "de" within 6 px
     keep the model render (there the neighbourhood really differs from the shipped one).
  6. Checks (SystemExit through need(), so they also run under python -O): 320x208 RGBA; no
     FrakturSpacingWarning (no guessed advance, no crowded mark); the three lines' ink boxes and
     baselines; every pixel that differs from the base lies within 6 px (Chebyshev) of a changed
     coverage pixel and inside TEXT_BAND; no alpha > 0 in the moon window (x >= 250, y < 100);
     the moved "Umberto Eco": all its opaque-core pixels and every coverage pixel farther than 6 px
     from "av" and from the erased "de" equal the es pixels shifted by DX3 exactly (reported: how
     many coverage pixels are exact copies, and the largest difference of the rest).
  7. Encodes with fraktur.save_rgba_png (bytes only) and verifies them independently before
     writing: exactly IHDR, IDAT, IEND with good CRCs, 320x208 8-bit RGBA, no interlace, Pillow
     decodes them to the rendered pixels. Written to "<name>.tmp" and renamed over the output;
     a failed write removes the .tmp (tools/build.py refuses stray files under assets_sv/res/de).

usage: uv run tools/images/build_novela.py [--out PATH] [--x1 N] [--x2 N] [--x3 N] [--quiet]
  --out PATH   write there instead (inside the project: the real output or anywhere under
               work/phaseD/, so a critic can use its own scratch directory)
  --x1/2/3 N   left ink edges of the three lines (scratch experiments: need an --out other than
               the real output)
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import struct
import sys
import warnings
import zlib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "work/jar/res"
OUT = ROOT / "assets_sv/res/de/intro/novela.png"
SCRATCH = ROOT / "work/phaseD"        # every track's scratch (never assets_sv/ or work/jar/)

sys.dont_write_bytecode = True        # importing fraktur must not write tools/images/__pycache__
sys.path.insert(0, str(ROOT / "tools/images"))
import fraktur as fk  # noqa: E402

BASE_LANG = "es"
OLD_L3 = "de Umberto Eco"             # Phase A line text of the es line 3
KEEP = "Umberto Eco"

LINE1, LINE2, LINE3_HEAD = "efter romanen", "”Rosens namn”", "av "
BASE1, BASE2, BASE3 = 114, 144, 174   # es/en baselines, pitch 30
X1, X2, X3 = 28, 40, 40               # left ink edges: the es indents (en: 21 / 40 / 40)

# Old lines 1 and 2 of es novela (ink [28,93,141,114] and [40,123,284,144], images.md §2.6),
# boxed generously: erase() takes whole connected components and refuses to split one.
ERASE1 = (20, 85, 300, 119)
ERASE2 = (30, 120, 300, 150)
TEXT_BAND = (12, 84, 293, 190)        # every changed pixel must lie in here (ink + 6 px glow)


def need(cond, msg: str) -> None:
    if not cond:
        raise SystemExit(f"build_novela: {msg}")


def rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def build(x1: int, x2: int, x3: int) -> tuple[Image.Image, dict]:
    """The Swedish novela as an RGBA image, plus a report dict."""
    base_path = RES / BASE_LANG / "intro/novela.png"
    cv = fk.Canvas.shipped(BASE_LANG, "novela")
    need(cv.script_boxes == [], "es novela should have no script boxes")
    n_px = cv.w * cv.h

    # 1. lift "Umberto Eco", erase the three old lines
    um = fk.letters(BASE_LANG, "novela", OLD_L3, KEEP)
    need(len(um.glyphs) == len(KEEP.replace(" ", "")), f"letters({KEEP!r}) gave {len(um.glyphs)} letters")
    u_id = um.glyphs[0]["source"]
    need(um.glyphs[0]["char"] == "U", f"first kept letter is {um.glyphs[0]['char']!r}, not U")
    cv.erase(ERASE1)
    cv.erase(ERASE2)
    cv.erase_letters(BASE_LANG, "novela", OLD_L3)
    left = [(i % cv.w, i // cv.w) for i in range(n_px) if cv.c[i] or cv.s[i]]
    need(not left, f"old text left after erasing: {len(left)} coverage px, bbox {fk.bbox_of(left)}")

    # 2-4. typeset
    with warnings.catch_warnings():
        warnings.simplefilter("error", fk.FrakturSpacingWarning)
        l1 = fk.line(LINE1, x1, BASE1)
        l2 = fk.line(LINE2, x2, BASE2)
        dx3 = fk.align_before(u_id, LINE3_HEAD, x3)
        name = um.moved(dx3, 0)
        head = fk.line_before(u_id, LINE3_HEAD, dx3)
    for lay in (l1, l2, head):
        for g in lay.glyphs:
            need(not g.get("spacing_guessed") and not g.get("mark_crowded") and not g.get("to_kept_off"),
                 f"{lay.text!r}: glyph {g['char']!r} flagged {g}")
    need(head.glyphs[-1].get("to_kept_err") is not None and abs(head.glyphs[-1]["to_kept_err"]) <= 0.25,
         f"'av' does not end at the font's advance before the U: {head.glyphs[-1].get('to_kept_err')}")
    for lay in (l1, l2, name, head):
        cv.draw(lay)

    # 5. render, then give the moved name its shipped pixels back
    img = cv.render()
    base = rgba(base_path)
    bpx, opx = base.load(), img.load()
    R, w, h = fk.GLOW_R, cv.w, cv.h
    src = set()                                   # the es name's coverage px and their glow support
    for x, y, _ in um.pixels():
        for yy in range(y - R, y + R + 1):
            for xx in range(x - R, x + R + 1):
                src.add((xx, yy))

    def same_support(x: int, y: int) -> bool:
        """The new coverage around (x + dx3, y) equals the es coverage around (x, y)."""
        for yy in range(y - R, y + R + 1):
            r = yy * w
            if (cv.c[r + x + dx3 - R:r + x + dx3 + R + 1] != cv.c0[r + x - R:r + x + R + 1]
                    or cv.s[r + x + dx3 - R:r + x + dx3 + R + 1] != cv.s0[r + x - R:r + x + R + 1]):
                return False
        return True

    reused, own = set(), set()                    # es px copied / px left to the model render
    for x, y in sorted(src):
        need(R <= min(x, x + dx3) and max(x, x + dx3) < w - R and R <= y < h - R,
             f"moved name pixel {(x, y)} too close to the image edge for the support test")
        if same_support(x, y):
            if bpx[x, y][3] or opx[x + dx3, y][3]:
                opx[x + dx3, y] = bpx[x, y]
                reused.add((x, y))
        else:
            own.add((x, y))

    # 6. checks
    need(img.size == (320, 208) and img.mode == "RGBA", f"image is {img.size} {img.mode}")
    ib = {"line1": l1.ink_bbox(), "line2": l2.ink_bbox(), "line3": fk.Layer.union([head, name]).ink_bbox()}
    for k, (x, b, lays) in enumerate(((x1, BASE1, [l1]), (x2, BASE2, [l2]), (x3, BASE3, [head, name])), 1):
        box = ib[f"line{k}"]
        bases = {g["baseline"] for lay in lays for g in lay.glyphs}
        need(box[0] == x and bases == {b} and box[1] == b - fk.CAP_TOP,
             f"line {k}: ink box {box}, baselines {bases} (want left edge {x}, baseline {b}, top {b - fk.CAP_TOP})")
    moon = fk.moon_pixels(img)
    need(moon == [], f"{len(moon)} px with alpha > 0 in the moon window, bbox {fk.bbox_of(moon)}")
    diff = fk.diff_pixels(base, img)
    changed_cov = [i for i in range(n_px) if cv.c[i] != cv.c0[i] or cv.s[i] != cv.s0[i]]
    near = set()
    for i in changed_cov:
        x, y = i % cv.w, i // cv.w
        for yy in range(max(0, y - fk.GLOW_R), min(cv.h - 1, y + fk.GLOW_R) + 1):
            for xx in range(max(0, x - fk.GLOW_R), min(cv.w - 1, x + fk.GLOW_R) + 1):
                near.add((xx, yy))
    stray = [p for p in diff if p not in near]
    need(not stray, f"{len(stray)} px differ from the base away from the edited text, bbox {fk.bbox_of(stray)}")
    tb = TEXT_BAND
    out_band = [p for p in diff if not (tb[0] <= p[0] <= tb[2] and tb[1] <= p[1] <= tb[3])]
    need(not out_band, f"{len(out_band)} changed px outside TEXT_BAND, bbox {fk.bbox_of(out_band)}")
    # the moved name against the es pixels shifted by dx3: every pixel whose support matched is
    # an exact copy, every opaque core pixel is exact, and only pixels near "av" / "de" differ
    def pxdiff(a, b) -> int:                      # two transparent pixels count as equal
        return 0 if a[3] == 0 and b[3] == 0 else max(abs(p - q) for p, q in zip(a, b))

    md = {(x, y): pxdiff(bpx[x, y], opx[x + dx3, y]) for x, y in src}
    bad = [p for p in reused if md[p]]
    need(not bad, f"{len(bad)} reused name px are not the es bytes, bbox {fk.bbox_of(bad)}")
    core = [(x, y) for x, y, v in um.pixels() if v == 255]
    need(core and all(md[p] == 0 for p in core), "an opaque core pixel of the moved name differs from es")
    cov = [(x, y) for x, y, _ in um.pixels()]
    stray_n = [p for p in src if md[p] and p not in own]
    need(not stray_n, f"{len(stray_n)} name px differ from es without a different support, bbox {fk.bbox_of(stray_n)}")
    rest = [md[p] for p in cov if md[p]]
    rep = {"dx3": dx3, "ink": ib, "diff_px": len(diff), "diff_bbox": fk.bbox_of(diff),
           "name_core_px": len(core), "name_src_px": len(src), "name_reused": len(reused),
           "name_own": len(own), "name_own_bbox": fk.bbox_of(own),
           "name_all_px": len(cov), "name_all_exact": len(cov) - len(rest),
           "name_rest_maxdiff": max(rest, default=0),
           "name_src_exact": sum(1 for p in src if md[p] == 0),
           "glyphs": [(lay.text, [(g["char"], g["x"], g["phase"], g["ink_left"], g["ink_right"])
                                   for g in lay.glyphs]) for lay in (l1, l2, head)]}
    return img, rep


def png_bytes(img: Image.Image) -> bytes:
    """fraktur.save_rgba_png's bytes, verified independently."""
    data = fk.save_rgba_png(img, None)
    need(data[:8] == b"\x89PNG\r\n\x1a\n", "PNG signature")
    pos, chunks = 8, []
    while pos < len(data):
        (ln,) = struct.unpack(">I", data[pos:pos + 4])
        t, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + ln]
        (crc,) = struct.unpack(">I", data[pos + 8 + ln:pos + 12 + ln])
        need(zlib.crc32(t + body) & 0xFFFFFFFF == crc, f"bad CRC in {t!r}")
        chunks.append((t, body))
        pos += 12 + ln
    need([t for t, _ in chunks] == [b"IHDR", b"IDAT", b"IEND"], f"chunks {[t for t, _ in chunks]}")
    need(chunks[0][1] == struct.pack(">IIBBBBB", 320, 208, 8, 6, 0, 0, 0), "IHDR is not 320x208 8-bit RGBA")
    raw = zlib.decompress(chunks[1][1])
    need(len(raw) == 208 * (1 + 320 * 4) and all(raw[y * 1281] == 0 for y in range(208)), "IDAT rows")
    back = Image.open(io.BytesIO(data))
    need(back.mode == "RGBA" and back.size == (320, 208), f"decoded {back.mode} {back.size}")
    need("gamma" not in back.info and "icc_profile" not in back.info, "gAMA/iCCP present")
    need(back.tobytes() == img.tobytes(), "decoded pixels differ from the rendered image")
    return data


def write(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    if tmp.exists():
        tmp.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out")
    ap.add_argument("--x1", type=int, default=X1)
    ap.add_argument("--x2", type=int, default=X2)
    ap.add_argument("--x3", type=int, default=X3)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out).resolve() if a.out else OUT
    if (a.x1, a.x2, a.x3) != (X1, X2, X3):
        need(a.out is not None and out != OUT,
             f"--x1/--x2/--x3 are for scratch experiments: give an --out other than {OUT}")
    if ROOT in out.parents:
        need(out == OUT or SCRATCH in out.parents, f"--out inside the project must be {OUT} or under {SCRATCH}/")

    # the base choice: es and en differ only in the text; de == en
    es, en = rgba(RES / "es/intro/novela.png"), rgba(RES / "en/intro/novela.png")
    need((RES / "de/intro/novela.png").read_bytes() == (RES / "en/intro/novela.png").read_bytes(),
         "de novela.png is not en byte for byte")
    need(Image.open(RES / "de/intro/novela.png").mode == "RGBA", "de novela.png is not RGBA")
    d = fk.bbox_of(fk.diff_pixels(es, en))
    tb = TEXT_BAND
    need(d is not None and tb[0] <= d[0] and tb[1] <= d[1] and d[2] <= tb[2] and d[3] <= tb[3],
         f"es and en novela differ outside the text band: {d}")

    img, rep = build(a.x1, a.x2, a.x3)
    data = png_bytes(img)
    write(out, data)
    if not a.quiet:
        for text, gl in rep["glyphs"]:
            print(f"  {text!r}: " + " ".join(f"{c}@{x}{'+' if p else ''}[{l}..{r}]" for c, x, p, l, r in gl))
        print(f"  ink boxes {rep['ink']}; 'Umberto Eco' moved {rep['dx3']:+d} px")
        print(f"  moved name vs es pixels: {rep['name_all_px']} coverage px ({rep['name_core_px']} opaque core), "
              f"{rep['name_all_exact']} exact, the rest max diff {rep['name_rest_maxdiff']}; with glow "
              f"{rep['name_src_px']} px: {rep['name_reused']} copied from es, {rep['name_src_exact']} exact, "
              f"{rep['name_own']} model-rendered next to 'av'/'de' (bbox {rep['name_own_bbox']}, es coords)")
        print(f"  {rep['diff_px']} px differ from es novela, bbox {rep['diff_bbox']}; moon window clear")
    print(f"{out} sha256 {hashlib.sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

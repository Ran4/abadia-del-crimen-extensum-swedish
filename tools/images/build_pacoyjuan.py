# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Build the Swedish credit screen res/de/intro/pacoyjuan.png
("efter spelet av" / "Paco Menéndez" / "och Juan Delcán").

Deterministic. Inputs (read-only):
  - work/jar/res/es/intro/pacoyjuan.png   base: "inspirado en la obra de" / "Paco Menéndez" /
                                          "y Juan Delcán" (the names keep their accents);
                                          everything except line 1 and the script "y" is kept
  - work/jar/res/en/intro/pacoyjuan.png   only to assert de == en byte for byte
  - work/jar/res/de/intro/pacoyjuan.png   only to assert de == en and to take its colour type
  - tools/images/fraktur.py               the Fraktur kit, through its documented API only
                                          (Canvas.shipped/erase/draw/draw_script/coverage_layer/
                                          render, line, Layer, SCRIPT_BOXES, moon_pixels,
                                          save_rgba_png): line 1 is typeset with the font built
                                          from the shipped credit screens, and the glow is
                                          regenerated from the union of all cores
  - tools/images/script_och.py            och_layer(): the composed script "och" (cream, alpha in
                                          multiples of 17, no glow)
  Both modules are imported with bytecode writing off (no __pycache__ in tools/images/).
Output:
  - assets_sv/res/de/intro/pacoyjuan.png

What it does (images.md §2.5, §3.1, §3.5; FORMAT §6.1-§6.4; GLOSSARY §8):
  1. checks the inputs: de == en byte for byte and is 8-bit RGBA 320x208; the es base is too;
     the es script "y" in Y_BOX is Y_PIXELS cream pixels with alpha in multiples of 17 and the
     one-pixel ring around Y_BOX is fully transparent (the "y" touches nothing, no glow);
  2. opens the es image as a Fraktur canvas (fk.Canvas.shipped, which knows the "y" is script
     ink without glow) and erases line 1 "inspirado en la obra de" as whole components with
     OLD_LINE1_BOX; its glow goes with it (including the 17 glow pixels es ships at x 250..252
     inside the moon window), the glow of "Paco Menéndez" below is regenerated, not eaten;
  3. erases the script "y" (the components inside Y_BOX: exactly the Y_PIXELS of step 1);
  4. typesets LINE1 = "efter spelet av" with fk.line at the es line-1 indent (left ink edge
     x = 28) on the es line-1 baseline (row 114), with the font's own spacing and word space;
     any FrakturSpacingWarning (guessed advance or crowded mark) is fatal;
  5. puts the script "och" where the "y" was, before the J of "Juan" (first ink column 85):
     OCH_GAP = 11 empty columns after the och's last alpha column (12 after its last ink
     column), as the och before "Daniel" in manuydani; es "y": 9 (10 by ink), en "and": 6,
     which is too tight; its baseline on the es "y"'s (row 173), one row above the Fraktur
     baseline 174, as the och in manuydani (157 vs 158);
  6. renders (pixels farther than 6 px from every changed coverage pixel keep the es bytes);
     then copies the es bytes back onto every pixel of kept text (es coverage > 0 outside the
     edits): render() gives such a pixel the es glow plus the model's glow delta, and where the
     old line 1's glow reached the top of "Paco" (rows 123..125) that moved KEPT_RESTORED (10)
     anti-aliased pixels of the P by 1-6 alpha levels (seen on black: <= 1); a pixel outside
     rows LINE2_TOP..KEEP_BELOW-1, or one off by more than LINE2_GLOW_TOL seen levels, is fatal;
  7. checks: 320x208 RGBA; coverage unchanged outside old line 1, new line 1, the "y" and the
     och; every changed pixel within 6 px of changed coverage; every kept-text pixel is the es
     bytes; from row KEEP_BELOW (126) down nothing changes outside the conjunction area
     (x 30..78), so "Juan Delcán" with its glow (x >= 79) and the lower part of "Paco Menéndez"
     are the es bytes; on rows 121..125, where the old line 1's glow overlapped the top of
     line 2's glow, removing it changes what the black screen shows by at most LINE2_GLOW_TOL
     levels (measured 3, glow pixels only); the och pixels are exactly the layer (cream, its
     alpha, no glow blended); nothing else with alpha > 0 in the conjunction area; nothing in
     the moon-window clip (x >= 250, y < 100); line 1 starts at x = 28 with its x-height
     letters ending on row 114;
  8. encodes with fk.save_rgba_png (IHDR, one IDAT, IEND; zlib level 9; no gAMA/iCCP/pHYs) and
     verifies those bytes independently before anything is written, then writes "<name>.tmp"
     and renames it over the output (a stale .tmp is removed first; tools/build.py refuses
     unexpected files under assets_sv/res/de).

Every check raises SystemExit("build_pacoyjuan: ...") through need(), so the checks also run
under python -O.

usage: uv run tools/images/build_pacoyjuan.py [--out PATH] [--och-dx N] [--och-dy N] [--quiet]
  --out PATH   write there instead (inside the project only the real output or a path under
               work/phaseD/pacoyjuan/ is allowed)
  --och-dx N   shift "och" N columns right (scratch experiments only: needs --out; the gap
  --och-dy N   check then allows 9..13), or N rows down
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
OUT = ROOT / "assets_sv/res/de/intro/pacoyjuan.png"
SCRATCH = ROOT / "work/phaseD/pacoyjuan"

sys.dont_write_bytecode = True        # importing the kits must not write tools/images/__pycache__
sys.path.insert(0, str(ROOT / "tools/images"))
import fraktur as fk  # noqa: E402
from script_och import och_layer, och_metrics  # noqa: E402

W, H = 320, 208
CREAM = (253, 246, 231)
PNG_SIG = b"\x89PNG\r\n\x1a\n"

LINE1 = "efter spelet av"                 # GLOSSARY §8
LINE1_X = 28                              # es "inspirado en la obra de" ink [28,93,246,118]
LINE1_BASELINE = 114                      # es line-1 baseline (x-height rows 98..114)
OLD_LINE1_BOX = (20, 85, 300, 120)        # whole words of es line 1 (line 2 starts at row 123)
OLD_LINE1_INK = (28, 93, 246, 118)        # its ink box (coverage >= 128), Phase A
Y_BOX = (65, 165, 75, 181)                # es script "y", alpha > 0 box (= fk.SCRIPT_BOXES)
Y_PIXELS = 82                             # its pixels with alpha > 0
NAME_FIRST_INK = 85                       # first ink column of the J of "Juan" (es and en)
NAME_GLOW_X = 79                          # first column of the J's glow
OCH_GAP = 11                              # empty columns after the och's last alpha column (12
                                          # after its last ink column), as the och in manuydani;
                                          # es "y": 9 (10 by ink), en "and": 6
OCH_BASELINE = 173                        # the es "y"'s baseline (Fraktur baseline 174)
CONJ_AREA = (30, 154, 78, 184)            # nothing but the conjunction may have alpha > 0 here
KEEP_BELOW = 126                          # rows >= this change only inside CONJ_AREA (line-1
                                          # coverage ends on row 119, its glow reaches 6 px)
LINE2_TOP = 121                           # rows LINE2_TOP..KEEP_BELOW-1: where the line-1 glow
LINE2_GLOW_TOL = 4                        # overlapped the top of line 2's glow; the change seen
                                          # over the black screen stays <= this (measured: 3)
KEPT_RESTORED = 10                        # kept-text px whose es bytes step 6 copies back
MOON = (250, 0, 319, 99)                  # r draws luna/niebla/ventana there from manuydani on
GLOW_R = 6                                # fraktur.py: render() rewrites only pixels within 6 px
                                          # (Chebyshev) of changed coverage; the rest keep the base


def need(cond: object, msg: str) -> None:
    """A check that survives python -O (unlike assert)."""
    if not cond:
        raise SystemExit(f"build_pacoyjuan: {msg}")


def inside(box, x: int, y: int) -> bool:
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def bbox_of(points) -> tuple[int, int, int, int] | None:
    pts = list(points)
    if not pts:
        return None
    xs, ys = [x for x, _ in pts], [y for _, y in pts]
    return min(xs), min(ys), max(xs), max(ys)


def xy(i: int) -> tuple[int, int]:
    return i % W, i // W


def coverage(cv: fk.Canvas) -> tuple[dict[int, int], dict[int, int]]:
    """(glowing, script) coverage of a canvas as {pixel index: c} for c > 0, read through the
    kit's documented Canvas.coverage_layer()."""
    return tuple({y * W + x: v for x, y, v in cv.coverage_layer(script=s).pixels()} for s in (False, True))


def covered(cv: fk.Canvas) -> set[int]:
    """Pixel indices with any (glowing or script) coverage."""
    c, s = coverage(cv)
    return c.keys() | s.keys()


def chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    """Split a PNG into (type, body) pairs, checking the signature, lengths and CRCs."""
    need(data[:8] == PNG_SIG, "not a PNG")
    out, i = [], 8
    while i < len(data):
        need(i + 12 <= len(data), "truncated PNG chunk header")
        (n,) = struct.unpack(">I", data[i:i + 4])
        need(i + 12 + n <= len(data), "truncated PNG chunk")
        typ, body = data[i + 4:i + 8], data[i + 8:i + 8 + n]
        (crc,) = struct.unpack(">I", data[i + 8 + n:i + 12 + n])
        need(zlib.crc32(typ + body) == crc, f"bad CRC in {typ!r}")
        out.append((typ, body))
        i += 12 + n
    return out


def ihdr_fields(body: bytes) -> tuple[int, ...]:
    """(width, height, depth, colour type, compression, filter, interlace)."""
    need(len(body) == 13, f"IHDR has {len(body)} bytes")
    return struct.unpack(">IIBBBBB", body)


def open_rgba(path: Path | io.BytesIO) -> Image.Image:
    with Image.open(path) as im:
        need(im.size == (W, H), f"{path}: size {im.size}, expected {(W, H)}")
        return im.convert("RGBA")


# ------------------------------------------------------------------------------------- step 1
def check_inputs() -> Image.Image:
    en_b = (RES / "en/intro/pacoyjuan.png").read_bytes()
    de_b = (RES / "de/intro/pacoyjuan.png").read_bytes()
    need(de_b == en_b, "de pacoyjuan.png is no longer en byte for byte")
    for lang, data in (("de", de_b), ("es", (RES / "es/intro/pacoyjuan.png").read_bytes())):
        typ, body = chunks(data)[0]
        need(typ == b"IHDR", f"{lang} pacoyjuan.png does not start with IHDR")
        w, h, depth, ctype, _, _, interlace = ihdr_fields(body)
        need((w, h, depth, ctype, interlace) == (W, H, 8, 6, 0),
             f"{lang} pacoyjuan.png is not 8-bit RGBA 320x208: {(w, h, depth, ctype, interlace)}")
    es = open_rgba(RES / "es/intro/pacoyjuan.png")
    px = es.load()
    x0, y0, x1, y1 = Y_BOX
    ring = [(x, y) for x in range(x0 - 1, x1 + 2) for y in range(y0 - 1, y1 + 2)
            if not inside(Y_BOX, x, y) and px[x, y][3]]
    need(not ring, f"es 'y' is not isolated: alpha at {ring[:5]}")
    ys = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if px[x, y][3]]
    need(len(ys) == Y_PIXELS, f"es 'y' has {len(ys)} pixels, expected {Y_PIXELS}")
    bad = [p for p in ys if px[p][:3] != CREAM or px[p][3] % 17]
    need(not bad, f"es 'y' pixels not cream / 16-level: {[(p, px[p]) for p in bad[:5]]}")
    return es


# ------------------------------------------------------------------------------------- steps 2-5
def typeset_line1() -> fk.Layer:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        lay = fk.line(LINE1, LINE1_X, LINE1_BASELINE)
    msgs = [str(w.message) for w in caught if issubclass(w.category, fk.FrakturSpacingWarning)]
    need(not msgs, f"line 1 spacing warnings: {msgs}")
    for g in lay.glyphs:
        need(not g.get("spacing_guessed") and not g.get("mark_crowded"),
             f"line 1 glyph {g['char']!r} at index {g['index']}: guessed spacing or crowded mark")
    ib = lay.ink_bbox()
    need(ib is not None and ib[0] == LINE1_X, f"line 1 ink starts at {ib}, expected x {LINE1_X}")
    need(ib[2] < MOON[0] - 8, f"line 1 ink reaches x {ib[2]}: its glow would enter the moon window")
    return lay


def och_place(dx: int, dy: int) -> tuple[int, int, Image.Image]:
    layer = och_layer()
    met = och_metrics()
    need(layer.size == met["size"], f"och layer {layer.size} vs metrics {met['size']}")
    x = NAME_FIRST_INK - OCH_GAP - layer.width + dx      # last alpha column = 85 - 11 - 1 = 73
    y = OCH_BASELINE - met["baseline_row"] + dy
    return x, y, layer


def edit(es: Image.Image, och_dx: int, och_dy: int):
    base = fk.Canvas.shipped("es", "pacoyjuan")         # never edited: the es coverage
    need(base.render().tobytes() == es.tobytes(), "the canvas base is not the es pacoyjuan pixels")
    boxes = fk.SCRIPT_BOXES[("es", "pacoyjuan")]
    need(boxes == [Y_BOX], f"script boxes {boxes}, expected [{Y_BOX}]")
    c0, s0 = coverage(base)
    cv = fk.Canvas.shipped("es", "pacoyjuan")

    # step 2: old line 1 (whole components) and its glow
    before = covered(cv)
    gone1 = cv.erase(OLD_LINE1_BOX)
    after = covered(cv)
    old1 = before - after
    need(old1, "erasing line 1 removed nothing")
    bb = bbox_of(xy(i) for i in old1)
    need(bb[1] >= OLD_LINE1_BOX[1] and bb[3] <= OLD_LINE1_BOX[3] + 2,
         f"line-1 erase took coverage outside its rows: bbox {bb}")
    ink1 = bbox_of(xy(i) for i in old1 if c0.get(i, 0) >= 128)
    need(ink1 == OLD_LINE1_INK, f"erased line-1 ink box {ink1}, expected {OLD_LINE1_INK}")
    left = sorted(i for i in after if 80 <= i // W <= 121)
    need(not left, f"coverage left in the line-1 rows: {[xy(i) for i in left[:5]]}")

    # step 3: the script "y"
    before = after
    cv.erase(Y_BOX)
    after = covered(cv)
    ypx = before - after
    need(len(ypx) == Y_PIXELS and all(inside(Y_BOX, *xy(i)) and s0.get(i) and not c0.get(i) for i in ypx),
         f"the 'y' erase removed {len(ypx)} px (expected the {Y_PIXELS} script px of the 'y')")
    left = sorted(i for i in after if inside(Y_BOX, *xy(i)))
    need(not left, f"coverage left in the 'y' box: {[xy(i) for i in left[:5]]}")

    # step 4: new line 1
    lay = typeset_line1()
    cv.draw(lay)
    new1 = {y * W + x for x, y, _ in lay.pixels()}

    # step 5: och (script ink: no glow, adds none)
    ox, oy, och = och_place(och_dx, och_dy)
    need(0 <= ox and ox + och.width <= W and 0 <= oy and oy + och.height <= H, f"och at {(ox, oy)} is off the screen")
    och_lay = fk.Layer.from_rgba(och, ox, oy)
    now = covered(cv)
    under = [(x, y) for x, y, _ in och_lay.pixels() if y * W + x in now]
    need(not under, f"och would land on coverage at {under[:5]}")
    cv.draw_script(och_lay)
    ochpx = {y * W + x for x, y, _ in och_lay.pixels()}
    c1, s1 = coverage(cv)
    sets = {"old1": old1, "y": ypx, "new1": new1, "och": ochpx, "gone1": gone1,
            "edited": old1 | ypx | new1 | ochpx}
    return cv, lay, (ox, oy, och), sets, {"c0": c0, "s0": s0, "c1": c1, "s1": s1}


# ------------------------------------------------------------------------------------- step 6
def seen(pp) -> tuple[int, int, int]:
    """What the black screen shows for an RGBA pixel."""
    return tuple((v * pp[3] + 127) // 255 for v in pp[:3])


def seen_delta(a, b) -> int:
    return max(abs(u - v) for u, v in zip(seen(a), seen(b)))


def restore_kept_text(img: Image.Image, es: Image.Image, cov: dict, sets: dict) -> list[tuple[int, int, int]]:
    """Copy the es bytes back onto every changed pixel of kept text (es coverage > 0 outside the
    edits); returns (x, y, seen delta before the copy). Only the glow under it may have changed
    (check_result proves its coverage did not), so only the line-2 band may need it."""
    p, q = img.load(), es.load()
    out = []
    for i in sorted((cov["c0"].keys() | cov["s0"].keys()) - sets["edited"]):
        x, y = xy(i)
        if p[x, y] != q[x, y]:
            out.append((x, y, seen_delta(p[x, y], q[x, y])))
            p[x, y] = q[x, y]
    bad = [r for r in out if not (LINE2_TOP <= r[1] < KEEP_BELOW) or r[2] > LINE2_GLOW_TOL]
    need(not bad, f"kept text changed outside rows {LINE2_TOP}..{KEEP_BELOW - 1} or by more than "
                  f"{LINE2_GLOW_TOL} seen levels: {bad[:5]}")
    need(len(out) == KEPT_RESTORED, f"{len(out)} kept-text px restored, expected {KEPT_RESTORED}: {out[:5]}")
    return out


# ------------------------------------------------------------------------------------- step 7
def check_result(img: Image.Image, es: Image.Image, lay, och_pos, sets, cov, och_dx: int) -> dict:
    need(img.mode == "RGBA" and img.size == (W, H), f"result is {img.mode} {img.size}")
    p, q = img.load(), es.load()
    edited = sets["edited"]
    c0, s0, c1, s1 = cov["c0"], cov["s0"], cov["c1"], cov["s1"]
    keys = c0.keys() | s0.keys() | c1.keys() | s1.keys()
    cov_changed = {i for i in keys if c1.get(i, 0) != c0.get(i, 0) or s1.get(i, 0) != s0.get(i, 0)}
    stray = sorted(cov_changed - edited)
    need(not stray, f"coverage changed outside the edits: {[xy(i) for i in stray[:5]]}")
    kept = sorted((c0.keys() | s0.keys()) - edited)
    kept_changed = [xy(i) for i in kept if p[xy(i)] != q[xy(i)]]
    need(not kept_changed, f"kept text is not the es bytes at {kept_changed[:5]}")

    changed = [(x, y) for y in range(H) for x in range(W) if p[x, y] != q[x, y]]
    near = set()
    R = GLOW_R
    for i in cov_changed:
        x, y = xy(i)
        for yy in range(max(0, y - R), min(H - 1, y + R) + 1):
            for xx in range(max(0, x - R), min(W - 1, x + R) + 1):
                near.add((xx, yy))
    far = [c for c in changed if c not in near]
    need(not far, f"pixels changed farther than {R} px from any changed coverage: {far[:5]}")
    low = [(x, y) for x, y in changed if y >= KEEP_BELOW and not inside(CONJ_AREA, x, y)]
    need(not low, f"pixels changed below row {KEEP_BELOW - 1} outside the conjunction area: {low[:5]}")
    # the conjunction area ends before the J's glow (es: columns 76..78 empty, 79 holds glow), so
    # with the KEEP_BELOW rule above every pixel of "Juan Delcán" and its glow is the es bytes
    need(CONJ_AREA[2] == NAME_GLOW_X - 1, "CONJ_AREA must end just before the J's glow")
    rows = range(CONJ_AREA[1], CONJ_AREA[3] + 1)
    need(all(q[x, y][3] == 0 for y in rows for x in range(Y_BOX[2] + 1, NAME_GLOW_X))
         and any(q[NAME_GLOW_X, y][3] for y in rows), f"es: the J's glow does not start at x {NAME_GLOW_X}")

    band = [seen_delta(p[x, y], q[x, y]) for x, y in changed
            if LINE2_TOP <= y < KEEP_BELOW and not inside(CONJ_AREA, x, y)]
    need(max(band, default=0) <= LINE2_GLOW_TOL,
         f"rows {LINE2_TOP}..{KEEP_BELOW - 1} (line 2's glow) change by {max(band)} > {LINE2_GLOW_TOL}")

    ox, oy, och = och_pos
    lp = och.load()
    for ly in range(och.height):
        for lx in range(och.width):
            want = lp[lx, ly]
            got = p[ox + lx, oy + ly]
            if want[3]:
                need(want[:3] == CREAM and want[3] % 17 == 0, f"och layer pixel {(lx, ly)} is {want}")
                need(got == want, f"och pixel {(ox + lx, oy + ly)} is {got}, the layer has {want} (glow blended?)")
    x0, y0, x1, y1 = CONJ_AREA
    area = {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if p[x, y][3]}
    ochset = {xy(i) for i in sets["och"]}
    need(area == ochset, f"conjunction area holds more than the och: {sorted(area - ochset)[:5]}")
    gap = NAME_FIRST_INK - (ox + och.width)
    lo, hi = (OCH_GAP, OCH_GAP) if och_dx == 0 else (9, 13)
    need(lo <= gap <= hi, f"{gap} empty columns between och and 'Juan'")

    moon = fk.moon_pixels(img)
    need(not moon, f"alpha in the moon window: {moon[:5]}")

    g0 = lay.glyphs[0]
    xh = [g for g in lay.glyphs if g["char"] in "acemnorsuvwz"]
    bottoms = []
    for g in xh:
        pts = [(x, y) for x, y, c in lay.pixels() if c >= 128 and g["ink_left"] <= x <= g["ink_right"]]
        if pts:
            bottoms.append(max(y for _, y in pts))
    need(bottoms and max(set(bottoms), key=bottoms.count) == LINE1_BASELINE,
         f"line-1 x-height letters end on rows {bottoms}, expected {LINE1_BASELINE}")
    need(g0["ink_left"] == LINE1_X, f"line 1 first glyph ink at {g0['ink_left']}")
    return {"changed": len(changed), "changed_box": bbox_of(changed), "band": max(band, default=0),
            "kept": len(kept)}


# ------------------------------------------------------------------------------------- step 8
def encode_checked(img: Image.Image) -> bytes:
    png = fk.save_rgba_png(img, None)
    cs = chunks(png)
    need([t for t, _ in cs] == [b"IHDR", b"IDAT", b"IEND"],
         f"chunk list is {[t for t, _ in cs]}, expected IHDR, IDAT, IEND")
    need(ihdr_fields(cs[0][1]) == (W, H, 8, 6, 0, 0, 0),
         f"IHDR is {ihdr_fields(cs[0][1])}, expected 320x208 8-bit RGBA, no interlace")
    need(cs[2][1] == b"", "IEND is not empty")
    raw = zlib.decompress(cs[1][1])
    stride = 1 + 4 * W
    need(len(raw) == H * stride, f"IDAT inflates to {len(raw)} bytes, expected {H * stride}")
    need({raw[y * stride] for y in range(H)} == {0}, "row filter bytes other than 0")
    with Image.open(io.BytesIO(png)) as back:
        need(back.mode == "RGBA" and back.size == (W, H), f"decodes as {back.mode} {back.size}")
        need(back.info.get("interlace", 0) == 0, "decodes as interlaced")
        need(back.tobytes() == img.tobytes(), "PNG round trip changed pixels")
    return png


def write_atomic(out_path: Path, data: bytes) -> None:
    """Write via '<name>.tmp' + rename; never leave the .tmp behind."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(out_path.name + ".tmp")
    tmp.unlink(missing_ok=True)       # left over by a run that was killed mid-write
    try:
        tmp.write_bytes(data)
        os.replace(tmp, out_path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def safe_out(out: Path) -> Path:
    out = out.resolve()
    if (out == ROOT or ROOT in out.parents) and out != OUT and SCRATCH not in out.parents:
        sys.exit(f"refusing --out {out}: inside the project it must be {OUT} or under {SCRATCH}/")
    return out


def build(out_path: Path, och_dx: int, och_dy: int, quiet: bool) -> int:
    es = check_inputs()
    cv, lay, och_pos, sets, cov = edit(es, och_dx, och_dy)
    img = cv.render()
    restored = restore_kept_text(img, es, cov, sets)
    info = check_result(img, es, lay, och_pos, sets, cov, och_dx)
    png = encode_checked(img)
    write_atomic(out_path, png)
    if not quiet:
        ox, oy, och = och_pos
        print(f"line 1 erased: {len(sets['old1'])} coverage px in {len(sets['gone1'])} components "
              f"(es ink {OLD_LINE1_INK}); es 'y' erased: {len(sets['y'])} px")
        print(f"line 1 {LINE1!r}: ink {lay.ink_bbox()}, baseline {LINE1_BASELINE}; glyphs "
              + " ".join(f"{g['char']}@{g['x']}p{g['phase']}" for g in lay.glyphs))
        print(f"'och' at {(ox, oy)}: x {ox}..{ox + och.width - 1}, baseline {oy + och_metrics()['baseline_row']}, "
              f"{NAME_FIRST_INK - (ox + och.width)} empty columns before 'Juan' (x={NAME_FIRST_INK})")
        print(f"{len(restored)} kept-text px given back their es bytes (seen change before: "
              f"<= {max((r[2] for r in restored), default=0)}): "
              + " ".join(f"({x},{y})" for x, y, _ in restored))
        print(f"{info['changed']} px differ from es, inside {info['changed_box']}; moon window clear; "
              f"line 2 glow band changes <= {info['band']}; all {info['kept']} kept-text px are the es bytes")
        print(f"wrote {out_path} ({len(png)} B, sha256 {hashlib.sha256(png).hexdigest()})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--och-dx", type=int, default=0)
    ap.add_argument("--och-dy", type=int, default=0)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    out = safe_out(a.out)
    if (a.och_dx or a.och_dy) and out == OUT:
        sys.exit("--och-dx/--och-dy are for scratch experiments: pass --out under work/phaseD/pacoyjuan/")
    return build(out, a.och_dx, a.och_dy, a.quiet)


if __name__ == "__main__":
    sys.exit(main())

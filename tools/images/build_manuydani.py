# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Build the Swedish credit screen res/de/intro/manuydani.png ("Manuel Pazos / och Daniel Celemín").

Deterministic. Inputs (read-only; RES = res/ of original/TheAbbeyOfCrimeExtensum.jar and GLYPHS = the
glyph inventory, both made from original/ by tools/images/inputs.py):
  - RES/es/intro/manuydani.png   base: "Manuel Pazos" / "y Daniel Celemín" (the es file
                                          keeps the í of Celemín); everything except the script
                                          "y" is kept pixel for pixel, RGB of transparent pixels
                                          included
  - RES/en/intro/manuydani.png   only for the cross-check in step 5 (and de == en)
  - RES/de/intro/manuydani.png   only to assert de == en and to take its colour type
  - tools/images/script_och.py            och_layer(): the composed script "och" (cream, alpha in
                                          multiples of 17, no glow), its placement on the en
                                          "and"'s baseline (och_position), and the deterministic
                                          RGBA PNG writer (png_rgba_bytes). Imported with bytecode
                                          writing off, so no __pycache__ is written next to it.
Output:
  - assets_sv/res/de/intro/manuydani.png

What it does (images.md §2.4 and §3.5, FORMAT §6.1-§6.4, GLOSSARY §8):
  1. decodes the es manuydani.png (RGBA) and checks the script "y": inside Y_BOX every pixel with
     alpha > 0 is cream (253,246,231) with alpha a multiple of 17, there are Y_PIXELS of them, and
     the one-pixel ring around Y_BOX is fully transparent (the "y" touches nothing, in particular
     not the glow of "Daniel", which starts at x=88);
  2. removes the "y": those pixels become (253,246,231,0), which is what every transparent pixel
     around them already holds in the es file (it carries a cream-RGB patch under the y's tail);
  3. puts "och" where en puts "and": och_position("manuydani", "right") = (51,143), i.e. the
     layer's right alpha edge on the "and"'s (x=82), its baseline on the "and"'s (row 157), so
     there are GAP_TO_NAME empty columns before the first ink column of "Daniel" (x=94), the same
     as en. Every pixel under the ink must be fully transparent cream, so only alpha changes and
     no glow is blended;
  4. checks the result: 320x208 RGBA; only the y's and the och's pixels differ from the es file;
     no pixel left in the conjunction area except the och's; nothing in the moon-window clip
     (x >= 250, y < 100); alpha in multiples of 17 in the conjunction area;
  5. cross-checks against an independent route: en manuydani with script_och.erase_and +
     place_och (the en "and" swapped for "och" by the och track's own code). The visible pixels
     (alpha, and RGB where alpha > 0) of the two must differ only inside ACCENT_BOX, the í accent
     of "Celemín" with its glow, which is the only visible difference between es and en besides
     the conjunction;
  6. encodes with script_och.png_rgba_bytes and verifies those bytes independently before
     anything is written: exactly IHDR, IDAT, IEND with good CRCs; IHDR 320x208, 8-bit RGBA,
     no interlace; the IDAT inflates to 208 rows that each start with filter byte 0; Pillow
     decodes it back to the same pixels. The file is then written to "<name>.tmp" next to the
     output and renamed over it. If the write fails or is interrupted the .tmp is removed (and a
     stale one left by a killed run is removed first), because tools/build.py step 8 refuses any
     unexpected file under assets_sv/res/de.

Every check raises SystemExit("build_manuydani: ...") through need(), not assert, so the checks
also run under python -O / PYTHONOPTIMIZE.

usage: uv run tools/images/build_manuydani.py [--out PATH] [--dx N] [--quiet]
  --out PATH  write there instead (inside the project only the real output or a path under
              work/phaseD/manuydani/ is allowed)
  --dx N      shift "och" N columns from the en placement (scratch experiments; step 5 is then
              skipped, and --dx needs --out)
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import struct
import sys
import zlib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True        # importing inputs must not write tools/images/__pycache__
sys.path.insert(0, str(ROOT / "tools/images"))
import inputs  # noqa: E402  (original/ jar res/ + glyph inventory, see tools/images/inputs.py)
RES = inputs.RES
OUT = ROOT / "assets_sv/res/de/intro/manuydani.png"
SCRATCH = ROOT / "work/phaseD/manuydani"

sys.dont_write_bytecode = True        # importing script_och must not write tools/images/__pycache__
sys.path.insert(0, str(ROOT / "tools/images"))
from script_och import (  # noqa: E402
    erase_and, och_layer, och_metrics, och_position, place_och, png_rgba_bytes)

W, H = 320, 208
CREAM = (253, 246, 231)
CLEAR = CREAM + (0,)                  # the transparent pixels around the es "y"
Y_BOX = (74, 149, 83, 164)            # es script "y", alpha > 0 box, inclusive (ink [74,150,82,164])
Y_PIXELS = 82                         # its pixels with alpha > 0
CONJ_AREA = (40, 140, 86, 166)        # nothing but the conjunction may have alpha > 0 here
EN_AND_RIGHT = 82                     # right alpha edge of the en "and" (ink 81)
EN_AND_BASELINE = 157                 # last core row of the en "and" (and of the es "y"'s bowl)
NAME_FIRST_INK = 94                   # first ink column of "Daniel" (lum*alpha/255 >= 128)
GAP_TO_NAME = (10, 12)                # empty columns between the conjunction and "Daniel" (en: 11)
ACCENT_BOX = (222, 131, 236, 144)     # the í accent + glow: the only visible es/en difference
                                      # outside the conjunction (169 px)
MOON = (250, 0, 319, 99)              # r draws luna/niebla/ventana there from manuydani on
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def need(cond: object, msg: str) -> None:
    """A check that survives python -O (unlike assert)."""
    if not cond:
        raise SystemExit(f"build_manuydani: {msg}")


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


def visible(p: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """A pixel as the screen sees it: RGB only matters where alpha > 0."""
    return p if p[3] else (0, 0, 0, 0)


def inside(box, x: int, y: int) -> bool:
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def check_inputs() -> None:
    en_b = (RES / "en/intro/manuydani.png").read_bytes()
    de_b = (RES / "de/intro/manuydani.png").read_bytes()
    need(de_b == en_b, "de manuydani.png is no longer en byte for byte")
    typ, body = chunks(de_b)[0]
    need(typ == b"IHDR", "de manuydani.png does not start with IHDR")
    w, h, depth, ctype, _, _, interlace = ihdr_fields(body)
    need((w, h, depth, ctype, interlace) == (W, H, 8, 6, 0),
         f"de manuydani.png is not 8-bit RGBA 320x208: {(w, h, depth, ctype, interlace)}")


def erase_y(img: Image.Image) -> set[tuple[int, int]]:
    """Step 1-2: check and remove the es script "y"; returns the cleared pixels."""
    px = img.load()
    x0, y0, x1, y1 = Y_BOX
    ring = [(x, y) for x in range(x0 - 1, x1 + 2) for y in range(y0 - 1, y1 + 2)
            if not inside(Y_BOX, x, y) and px[x, y][3]]
    need(not ring, f"es 'y' is not isolated: alpha at {ring[:5]}")
    ys = {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if px[x, y][3]}
    need(len(ys) == Y_PIXELS, f"es 'y' has {len(ys)} pixels, expected {Y_PIXELS}")
    bad = sorted(p for p in ys if px[p][:3] != CREAM or px[p][3] % 17)
    need(not bad, f"es 'y' pixels not cream / 16-level: {[(p, px[p]) for p in bad[:5]]}")
    for p in ys:
        px[p] = CLEAR
    return ys


def put_och(img: Image.Image, dx: int) -> tuple[tuple[int, int], set[tuple[int, int]]]:
    """Step 3: composite the script "och" on fully transparent cream pixels only."""
    layer = och_layer()
    met = och_metrics()
    x, y = och_position("manuydani", "right")
    x += dx
    need(y + met["baseline_row"] == EN_AND_BASELINE, "och is not on the en 'and' baseline")
    lw, lh = layer.size
    if dx == 0:
        need(x + lw - 1 == EN_AND_RIGHT, f"och ends at x={x + lw - 1}, en 'and' at {EN_AND_RIGHT}")
    gap = NAME_FIRST_INK - (x + lw)
    need(GAP_TO_NAME[0] <= gap <= GAP_TO_NAME[1], f"{gap} empty columns before 'Daniel'")
    need(0 <= x and x + lw <= W and 0 <= y and y + lh <= H, f"och at {(x, y)} is off the screen")
    lp, px = layer.load(), img.load()
    ink = set()
    for ly in range(lh):
        for lx in range(lw):
            a = lp[lx, ly][3]
            if not a:
                continue
            p = (x + lx, y + ly)
            if px[p] != CLEAR:
                need(False, f"och would land on {px[p]} at {p}")
            if lp[lx, ly][:3] != CREAM or a % 17:
                need(False, f"och layer pixel {(lx, ly)} is {lp[lx, ly]}")
            px[p] = CREAM + (a,)
            ink.add(p)
    return (x, y), ink


def check_result(img: Image.Image, es: Image.Image, ys: set, ink: set) -> None:
    """Step 4."""
    need(img.mode == "RGBA" and img.size == (W, H), f"result is {img.mode} {img.size}")
    p, q = img.load(), es.load()
    changed = {(x, y) for y in range(H) for x in range(W) if p[x, y] != q[x, y]}
    stray = sorted(changed - ys - ink)
    need(not stray, f"pixels changed outside the y and the och: {stray[:5]}")
    x0, y0, x1, y1 = CONJ_AREA
    left = {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if p[x, y][3]}
    need(left == ink, f"conjunction area holds more than the och: {sorted(left - ink)[:5]}")
    need(all(p[c][:3] == CREAM and p[c][3] % 17 == 0 for c in left),
         "conjunction ink is not cream with alpha in multiples of 17")
    mx0, my0, mx1, my1 = MOON
    moon = [(x, y) for y in range(my0, my1 + 1) for x in range(mx0, mx1 + 1) if p[x, y][3]]
    need(not moon, f"alpha in the moon window: {moon[:5]}")


def cross_check(img: Image.Image) -> int:
    """Step 5: compare with en + erase_and + place_och; returns the number of differing pixels."""
    ref = open_rgba(RES / "en/intro/manuydani.png")
    erase_and(ref, "manuydani")
    place_och(ref, "manuydani")
    p, q = img.load(), ref.load()
    diff = [(x, y) for y in range(H) for x in range(W) if visible(p[x, y]) != visible(q[x, y])]
    outside = [c for c in diff if not inside(ACCENT_BOX, *c)]
    need(not outside, f"differs from the en-based och screen outside the í accent: {outside[:5]}")
    return len(diff)


def encode_checked(img: Image.Image) -> bytes:
    """Step 6: encode with script_och.png_rgba_bytes and verify the bytes without trusting it."""
    png = png_rgba_bytes(img)
    cs = chunks(png)
    need([t for t, _ in cs] == [b"IHDR", b"IDAT", b"IEND"],
         f"chunk list is {[t for t, _ in cs]}, expected IHDR, IDAT, IEND")
    need(ihdr_fields(cs[0][1]) == (W, H, 8, 6, 0, 0, 0),
         f"IHDR is {ihdr_fields(cs[0][1])}, expected 320x208 8-bit RGBA, no interlace")
    need(cs[2][1] == b"", "IEND is not empty")
    raw = zlib.decompress(cs[1][1])
    stride = 1 + 4 * W
    need(len(raw) == H * stride, f"IDAT inflates to {len(raw)} bytes, expected {H * stride}")
    filters = {raw[y * stride] for y in range(H)}
    need(filters == {0}, f"row filter bytes {sorted(filters)}, expected only 0")
    with Image.open(io.BytesIO(png)) as back:
        need(back.mode == "RGBA" and back.size == (W, H), f"decodes as {back.mode} {back.size}")
        need(back.info.get("interlace", 0) == 0, "decodes as interlaced")
        need(back.tobytes() == img.tobytes(), "PNG round trip changed pixels")
    return png


def write_atomic(out_path: Path, data: bytes) -> None:
    """Write via '<name>.tmp' + rename; never leave the .tmp behind (tools/build.py step 8 would
    reject it as an unexpected file under assets_sv/res/de)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(out_path.name + ".tmp")
    tmp.unlink(missing_ok=True)       # left over by a run that was killed (SIGKILL) mid-write
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


def build(out_path: Path, dx: int, quiet: bool) -> int:
    check_inputs()
    es = open_rgba(RES / "es/intro/manuydani.png")
    img = es.copy()
    ys = erase_y(img)
    pos, ink = put_och(img, dx)
    check_result(img, es, ys, ink)
    ndiff = cross_check(img) if dx == 0 else None
    png = encode_checked(img)
    write_atomic(out_path, png)
    if not quiet:
        lw = och_layer().width
        print(f"es 'y' removed: {len(ys)} px in {Y_BOX}")
        print(f"'och' at {pos}: {len(ink)} px, x {pos[0]}..{pos[0] + lw - 1}, "
              f"{NAME_FIRST_INK - (pos[0] + lw)} empty columns before 'Daniel' (x={NAME_FIRST_INK})")
        if ndiff is not None:
            print(f"cross-check vs en + och: {ndiff} visible px differ, all inside the í accent {ACCENT_BOX}")
        print(f"wrote {out_path} ({len(png)} B, sha256 {hashlib.sha256(png).hexdigest()})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--dx", type=int, default=0)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    out = safe_out(a.out)
    if a.dx and out == OUT:
        sys.exit("--dx is for scratch experiments: pass --out under work/phaseD/manuydani/")
    return build(out, a.dx, a.quiet)


if __name__ == "__main__":
    sys.exit(main())

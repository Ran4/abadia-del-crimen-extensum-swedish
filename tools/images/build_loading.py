# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Build the Swedish first screen res/de/intro/loading.png ("LADDAR: var god vänta...").

Deterministic. Inputs (read-only; RES = res/ of original/TheAbbeyOfCrimeExtensum.jar and GLYPHS = the
glyph inventory, both made from original/ by tools/images/inputs.py):
  - RES/es/intro/loading.png   base: the es title art (everything above row 175) is kept
                                        pixel for pixel; its bottom line "CARGANDO: Por favor,
                                        espere" (rows 181..193) is removed
  - RES/{en,es,it}/intro/loading.png   the shipped loadline letters, cut by box (CUT)
  - RES/de/intro/loading.png   only to assert de == en and to take its colour type (RGBA)
  - assets_sv/image_src/loading/g.txt     the hand-pixelled 'g' (the loadline font has none)
  - assets_sv/image_src/loading/auml.txt  the hand-pixelled 'ä' (en 'a' + two 1-px dots)
Output:
  - assets_sv/res/de/intro/loading.png

What it does:
  1. decodes the es loading.png (RGBA, 1-bit alpha, transparent pixels are (4,2,4,0)) and clears
     every pixel of rows 175..207 back to (4,2,4,0) (those rows hold nothing but the text line);
  2. cuts the letters it reuses out of the shipped en/es/it lines; every box is checked: the ink
     count and colour match, the box is tight in x, the ink in the box forms the expected number
     of 8-connected pieces (one per letter, two for ':'), and no ink just outside the box touches
     the letter (except the known joins in TOUCH_OK). Together the last two mean no fragment of a
     neighbouring letter was cut and no part of the letter was left behind;
  3. lays the line out from LAYOUT (glyph + number of empty columns before it), centred so that
     the ink midpoint is at x MID, on the font's fixed rows (caps 182..189, x-height 184..189,
     baseline 189, descenders to 193), and paints it with the cut letters and the hand-drawn
     g and ä (joins between letters come from the spacing, see LAYOUT);
  4. checks: size, mode, 1-bit alpha, colour, nothing outside rows 175..207 changed, line inside
     rows 181..193, word gaps 4..7, midpoint 164..167, nothing in the moon window clip
     (x >= 250, y < 100);
  5. encodes the PNG chunk by chunk: IHDR (8-bit RGBA, no interlace), one IDAT (filter 0 on every
     row, zlib level 9), IEND. No gAMA/iCCP/pHYs/text chunks. The bytes are decoded again in memory
     and checked (pixels, mode, chunk list) before anything is written; the file is then written
     to a temporary name next to the output and renamed over it, so a failed build never leaves a
     bad or half-written loading.png behind.

usage: uv run tools/images/build_loading.py [--src DIR] [--out PATH] [--quiet]
  --src DIR  read g.txt and auml.txt from DIR instead (for scratch variants)
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
SRC_DIR = ROOT / "assets_sv/image_src/loading"
OUT = ROOT / "assets_sv/res/de/intro/loading.png"

W, H = 320, 208
INK = (252, 254, 252, 255)           # loadline colour in es/en/it/fr (pl uses white)
CLEAR = (4, 2, 4, 0)                 # what every transparent pixel of the es file holds
LINE_ROWS = (175, 207)               # es rows that hold the text line and nothing else
INK_ROWS = (181, 193)                # where the line may put ink (FORMAT 6.1)
MID = 166                            # target ink midpoint (shipped lines: 162.5..167.5)
MOON = (250, 0, 319, 99)             # r draws the moon window there from screen 1 on

# Letters cut from the shipped lines: name -> (lang, x0, y0, x1, y1 (inclusive), pixel count).
# Every box was read off a pixel dump of the shipped line. cut() asserts the ink count, that the
# ink in the box is PIECES[name] 8-connected pieces (1 unless listed), and that no ink outside the
# box touches the letter (8-neighbourhood; TOUCH_OK lists the known joins). A stray piece of a
# neighbour inside the box would add a piece; a piece joined to the letter or reaching out of the
# box would touch outside ink; a letter cut short would leave touching ink outside.
CUT = {
    "L": ("en", 102, 182, 107, 189, 13),   # LOADING
    "A": ("en", 117, 182, 124, 189, 18),   # LOADING (= es/it/pl A, pixel-identical)
    "D": ("en", 127, 182, 134, 189, 25),   # LOADING (= es D)
    "R": ("es", 99, 182, 105, 189, 21),    # CARGANDO (= it R)
    ":": ("es", 152, 184, 152, 188, 2),    # CARGANDO:
    "v": ("es", 192, 184, 197, 189, 12),   # favor (= it favore)
    "a": ("en", 211, 184, 216, 189, 18),   # wait
    "r": ("es", 205, 184, 209, 189, 11),   # favor
    "o": ("es", 199, 184, 203, 189, 12),   # favor
    "d": ("it", 184, 182, 191, 189, 21),   # Attendere
    "n": ("it", 179, 185, 183, 189, 14),   # Attendere
    "t": ("en", 220, 183, 224, 189, 13),   # wait (= it Attendere t)
    ".": ("en", 226, 189, 226, 189, 1),    # wait...
}
PIECES = {":": 2}                     # 8-connected pieces per cut letter when not 1
# Neighbouring ink that touches a cut box diagonally or orthogonally in the shipped line and is
# known to belong to the neighbour (a join in the original handwriting): allowed, not cut.
TOUCH_OK = {
    "d": {(183, 188), (183, 189)},         # the n of "nd" runs into the d's baseline stroke
    "n": {(184, 189)},                     # same join, seen from the n
    "t": {(219, 185), (219, 186)},         # the i of "it" runs into the t's crossbar
}

# The line: (glyph, empty columns between the previous glyph's ink box and this one's).
# Word gaps 4..7 as in the shipped lines (images.md 3.4); capitals spaced as in LOADING/CARGANDO.
LAYOUT = [
    ("L", None), ("A", 1), ("D", 2), ("D", 1), ("A", 0), ("R", 2), (":", 2),
    ("v", 6), ("a", 1), ("r", 1),
    ("g", 5), ("o", 1), ("d", 0),
    ("v", 5), ("ä", 1), ("n", 1), ("t", 0), ("a", 0), (".", 2), (".", 2), (".", 2),
]
# Joins come from spacing alone, as in the shipped lines: at ("t", 0) the n's right shoulder
# (n x+4, row 186) touches the start of the t's crossbar (row 185) diagonally, the way the i of
# en "wait" runs into its t and the n of fr "patienter" into its t. The other pairs keep the
# 1-px gaps of es "favor" / it "per favore" (a's exit stroke ends one pixel before the next
# letter), so the line has the shipped mix of separate and joined letters.
WORD_GAP_MIN = 4                      # a layout gap >= this starts a new word


def chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    out, i = [], 8
    while i < len(data):
        (n,) = struct.unpack(">I", data[i:i + 4])
        typ, body = data[i + 4:i + 8], data[i + 8:i + 8 + n]
        crc = struct.unpack(">I", data[i + 8 + n:i + 12 + n])[0]
        assert zlib.crc32(typ + body) == crc, f"bad CRC in {typ!r}"
        out.append((typ, body))
        i += 12 + n
    return out


def chunk(typ: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + typ + body + struct.pack(">I", zlib.crc32(typ + body))


def load_rgba(path: Path | io.BytesIO) -> list[list[tuple[int, int, int, int]]]:
    im = Image.open(path)
    assert im.size == (W, H), (path, im.size)
    px = im.convert("RGBA").load()
    return [[px[x, y] for x in range(W)] for y in range(H)]


def parse_rows(lines: list[str], where: str) -> tuple[int, list[str]]:
    """'y0 N' then lines '<image y> <pixels>' in order from y0. Returns (y0, rows)."""
    y0 = None
    rows: list[str] = []
    for raw in lines:
        parts = raw.split()
        if parts[0] == "y0":
            y0 = int(parts[1])
            continue
        assert y0 is not None and len(parts) == 2, f"bad line in {where}: {raw!r}"
        assert int(parts[0]) == y0 + len(rows), f"row label {parts[0]} out of order in {where}"
        assert set(parts[1]) <= {".", "#"}, f"unknown symbol in {where}: {raw!r}"
        rows.append(parts[1])
    assert y0 is not None and rows, f"{where} needs y0 and rows"
    assert len({len(r) for r in rows}) == 1, f"ragged rows in {where}"
    return y0, rows


def content_lines(path: Path) -> list[str]:
    """Lines of a glyph file without comments (lines starting with '#') and blank lines."""
    return [raw for raw in path.read_text(encoding="utf-8").splitlines()
            if raw.strip() and not raw.lstrip().startswith("#")]


def pieces(pix: set[tuple[int, int]]) -> int:
    """Number of 8-connected pieces in a pixel set."""
    seen: set[tuple[int, int]] = set()
    count = 0
    for p in sorted(pix):
        if p in seen:
            continue
        count += 1
        stack = [p]
        seen.add(p)
        while stack:
            x, y = stack.pop()
            for q in ((x + dx, y + dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                if q in pix and q not in seen:
                    seen.add(q)
                    stack.append(q)
    return count


def grid_pixels(y0: int, rows: list[str]) -> set[tuple[int, int]]:
    """Pixels of a grid relative to column 0, absolute rows."""
    return {(dx, y0 + dy) for dy, row in enumerate(rows) for dx, s in enumerate(row) if s == "#"}


def read_glyph(path: Path) -> set[tuple[int, int]]:
    y0, rows = parse_rows(content_lines(path), str(path))
    assert 0 <= y0 and y0 + len(rows) <= H, \
        f"{path}: rows {y0}..{y0 + len(rows) - 1} fall outside the image (0..{H - 1})"
    return grid_pixels(y0, rows)


def cut(images: dict, name: str) -> set[tuple[int, int]]:
    lang, x0, y0, x1, y1, n = CUT[name]
    img = images[lang]
    pix = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            p = img[y][x]
            if p[3]:
                assert p == INK, f"{name}: unexpected colour {p} at ({x},{y}) in {lang}"
                pix.add((x - x0, y))
    assert len(pix) == n, f"{name}: cut {len(pix)} pixels from {lang} box, expected {n}"
    xs = {x for x, _ in pix}
    assert min(xs) == 0 and max(xs) == x1 - x0, f"{name}: box is not tight in x"
    k = pieces(pix)
    assert k == PIECES.get(name, 1), f"{name}: {k} separate pieces of ink in the {lang} box, " \
        f"expected {PIECES.get(name, 1)} (a fragment of a neighbouring letter?)"
    # nothing touching the letter just outside its box, except known joins
    for (dx, y) in pix:
        x = x0 + dx
        for ny in (y - 1, y, y + 1):
            for nx in (x - 1, x, x + 1):
                if x0 <= nx <= x1 and y0 <= ny <= y1:
                    continue
                if img[ny][nx][3] and (nx, ny) not in TOUCH_OK.get(name, set()):
                    raise AssertionError(f"{name}: ink at ({nx},{ny}) in {lang} touches the cut box")
    return pix


def build(src_dir: Path, out_path: Path, quiet: bool) -> int:
    de_bytes = (RES / "de/intro/loading.png").read_bytes()
    assert de_bytes == (RES / "en/intro/loading.png").read_bytes(), "de loading.png should equal en"
    assert Image.open(RES / "de/intro/loading.png").mode == "RGBA"
    es_path = RES / "es/intro/loading.png"
    assert Image.open(es_path).mode == "RGBA"
    images = {lang: load_rgba(RES / lang / "intro/loading.png") for lang in ("es", "en", "it")}
    es = images["es"]

    # --- 1. base: es with rows 175..207 cleared
    errors: list[str] = []
    for y in range(H):
        for x in range(W):
            p = es[y][x]
            assert p[3] in (0, 255), f"es loading.png has partial alpha at ({x},{y})"
            if p[3] == 0:
                assert p == CLEAR, f"es transparent pixel at ({x},{y}) is {p}"
            elif LINE_ROWS[0] <= y <= LINE_ROWS[1]:
                assert p == INK and INK_ROWS[0] <= y <= INK_ROWS[1], f"es: unexpected pixel {p} at ({x},{y})"
    img = [row[:] for row in es]
    removed = 0
    for y in range(LINE_ROWS[0], LINE_ROWS[1] + 1):
        for x in range(W):
            if img[y][x][3]:
                img[y][x] = CLEAR
                removed += 1

    # --- 2. glyphs
    glyphs: dict[str, set[tuple[int, int]]] = {name: cut(images, name) for name in CUT}
    glyphs["g"] = read_glyph(src_dir / "g.txt")
    glyphs["ä"] = read_glyph(src_dir / "auml.txt")
    a_part = {(dx, y) for dx, y in glyphs["ä"] if y >= 184}
    assert a_part == glyphs["a"], "auml.txt rows 184..189 must be the en 'a' of 'wait' pixel for pixel"
    for name, pix in glyphs.items():
        xs = [x for x, _ in pix]
        assert min(xs) == 0, f"glyph {name} does not start at column 0"

    # --- 3. layout
    placed = []          # (glyph, x_left, word index)
    x, word = 0, 0
    for name, gap in LAYOUT:
        if gap is not None:
            prev = placed[-1]
            prev_right = prev[1] + max(px for px, _ in glyphs[prev[0]])
            x = prev_right + 1 + gap
            if gap >= WORD_GAP_MIN:
                word += 1
        placed.append((name, x, word))
    left = min(gx for _, gx, _ in placed)
    right = max(gx + max(px for px, _ in glyphs[n]) for n, gx, _ in placed)
    shift = MID - (left + right) // 2
    line: set[tuple[int, int]] = set()
    by_word: dict[int, set[int]] = {}
    for name, gx, w in placed:
        for dx, y in glyphs[name]:
            line.add((gx + shift + dx, y))
            by_word.setdefault(w, set()).add(gx + shift + dx)
    for (x, y) in line:
        assert 0 <= x < W and 0 <= y < H, f"line pixel ({x},{y}) falls outside the image"
        img[y][x] = INK

    # --- 4. checks
    for y in range(H):
        for x in range(W):
            p = img[y][x]
            if not LINE_ROWS[0] <= y <= LINE_ROWS[1] and p != es[y][x]:
                errors.append(f"pixel ({x},{y}) changed outside rows {LINE_ROWS}")
            if p[3] not in (0, 255):
                errors.append(f"partial alpha at ({x},{y})")
            if p[3] and LINE_ROWS[0] <= y <= LINE_ROWS[1] and (p != INK or not INK_ROWS[0] <= y <= INK_ROWS[1]):
                errors.append(f"bad line pixel {p} at ({x},{y})")
            if p[3] == 0 and p != CLEAR:
                errors.append(f"transparent pixel ({x},{y}) is {p}, es uses {CLEAR}")
            if p[3] and MOON[0] <= x <= MOON[2] and MOON[1] <= y <= MOON[3] and p != es[y][x]:
                errors.append(f"new ink in the moon window at ({x},{y})")
    xs = sorted({x for x, _ in line})
    ys = [y for _, y in line]
    mid = (xs[0] + xs[-1]) / 2
    if not 164 <= mid <= 167:
        errors.append(f"line midpoint {mid} outside 164..167")
    words = [sorted(by_word[w]) for w in sorted(by_word)]
    gaps = [words[k + 1][0] - words[k][-1] - 1 for k in range(len(words) - 1)]
    for k, g in enumerate(gaps):
        if not 4 <= g <= 7:
            errors.append(f"word gap {k} is {g} px (shipped: 4..7)")
    if errors:
        print("\n".join(errors[:40]), file=sys.stderr)
        print(f"FAILED: {len(errors)} errors", file=sys.stderr)
        return 2

    # --- 5. write: IHDR, one IDAT, IEND
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in img)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    # decode the bytes in memory and confirm before touching the output file
    assert load_rgba(io.BytesIO(png)) == img, "encoded PNG does not decode to the intended pixels"
    assert Image.open(io.BytesIO(png)).mode == "RGBA"
    assert [t for t, _ in chunks(png)] == [b"IHDR", b"IDAT", b"IEND"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(out_path.name + ".tmp")
    tmp.write_bytes(png)
    os.replace(tmp, out_path)
    assert out_path.read_bytes() == png, f"{out_path} does not hold the bytes just written"
    if not quiet:
        print(f"wrote {out_path} ({len(png)} B, sha256 {hashlib.sha256(png).hexdigest()})")
        print(f"  removed {removed} es line pixels; painted {len(line)} pixels "
              f"(g {len(glyphs['g'])}, ä {len(glyphs['ä'])})")
        print(f"  ink bbox x {xs[0]}..{xs[-1]} y {min(ys)}..{max(ys)}, midpoint {mid}, word gaps {gaps}")
        print("  glyph x: " + " ".join(f"{n}{gx + shift}" for n, gx, _ in placed))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, default=SRC_DIR)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    return build(a.src, a.out, a.quiet)


if __name__ == "__main__":
    sys.exit(main())

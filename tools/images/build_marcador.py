# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Build the Swedish HUD image res/de/marcador.png ("Dag" instead of "Day").

Deterministic. Inputs (read-only; RES = res/ of original/TheAbbeyOfCrimeExtensum.jar and GLYPHS = the
glyph inventory, both made from original/ by tools/images/inputs.py):
  - RES/de/marcador.png  (the shipped de file, byte-identical to en; asserted)
  - RES/en/marcador.png  (only to assert de == en)
  - GLYPHS/hud/BACKGROUND_reconstructed_x0-41_y0-21.png
        (Phase A majority-vote background of the word area; used to restore the pixels the
         en 'y' covered)
  - assets_sv/image_src/marcador/g.txt  (the hand-pixelled 'g', committed source pixels)
Output:
  - assets_sv/res/de/marcador.png

What it does:
  1. decodes the en/de marcador (indexed, 26-entry PLTE, 1-byte tRNS = index 0 transparent);
  2. removes the en 'y' (every font-colour pixel inside its box [30..38]x[4..18]) and puts back
     the reconstructed background under it;
  3. paints the 'g' from g.txt (only the colours of the en palette are allowed);
  4. checks: size, palette/tRNS unchanged, D and a (x <= 29) unchanged, everything outside the
     word area [0..39]x[0..20] unchanged, and the in-game black day-numeral box rule (no word ink
     at x >= 37 on rows 7..14, none at x >= 39 anywhere);
  5. writes the PNG chunk by chunk: IHDR, PLTE and tRNS copied verbatim from the original, one
     new IDAT (filter 0, zlib level 9), IEND. No gAMA/iCCP/pHYs/text chunks.

usage: uv run build_marcador.py [--glyph PATH] [--out PATH] [--quiet]
"""
from __future__ import annotations

import argparse
import hashlib
import struct
import sys
import zlib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True        # importing inputs must not write tools/images/__pycache__
sys.path.insert(0, str(ROOT / "tools/images"))
import inputs  # noqa: E402  (original/ jar res/ + glyph inventory, see tools/images/inputs.py)
SRC_DE = inputs.RES / "de/marcador.png"
SRC_EN = inputs.RES / "en/marcador.png"
BG = inputs.GLYPHS / "hud/BACKGROUND_reconstructed_x0-41_y0-21.png"
GLYPH = ROOT / "assets_sv/image_src/marcador/g.txt"
OUT = ROOT / "assets_sv/res/de/marcador.png"

W, H = 320, 32
WORD_BOX = (0, 0, 39, 20)          # inclusive; nothing outside may change
Y_BOX = (30, 4, 38, 18)            # inclusive box of the en 'y' (Phase A hud_index.json)
Y_PIXELS = 78                      # font pixels of the en 'y' (Phase A hud_index.json)
KEEP_X_MAX = 29                    # D (1..17) and a (18..29) are kept pixel for pixel
NUMERAL_BOX = (37, 7, 60, 14)      # v.b(int): fillRect(37,183,24,8) black, = image rows 7..14

# The hud font colours (FORMAT 6.2 / images.md 3.6). Anything else is ground or ivy.
FONT_RGB = {
    "W": (0xEC, 0xEB, 0xEC),
    "L": (0xD7, 0xD8, 0xD8),
    "M": (0xAB, 0xB2, 0xB3),
    "d": (0x9C, 0xA2, 0xA4),
    "R": (0x96, 0x02, 0x0A),
    "r": (0x6D, 0x02, 0x11),
    "q": (0x54, 0x02, 0x0C),
}
# extra symbols allowed in g.txt: explicit ground (black) and the three ivy greens
OTHER_RGB = {
    "k": (0x05, 0x02, 0x04),
    "2": (0x19, 0x4E, 0x0C),
    "5": (0x21, 0x62, 0x14),
    "3": (0x2A, 0x92, 0x14),
}


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


def load_indices(path: Path) -> list[list[int]]:
    im = Image.open(path)
    assert im.mode == "P" and im.size == (W, H), (path, im.mode, im.size)
    px = im.load()
    return [[px[x, y] for x in range(W)] for y in range(H)]


def read_glyph(path: Path) -> tuple[int, int, list[str]]:
    """g.txt: '#' comments; 'x0 N'; 'y0 N'; then lines '<image y> <pixels>' in order from y0."""
    x0 = y0 = None
    rows: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        parts = raw.split("#", 1)[0].split()
        if not parts:
            continue
        if parts[0] == "x0":
            x0 = int(parts[1])
        elif parts[0] == "y0":
            y0 = int(parts[1])
        else:
            assert y0 is not None and len(parts) == 2, f"bad line in {path}: {raw!r}"
            assert int(parts[0]) == y0 + len(rows), f"row label {parts[0]} out of order in {path}"
            rows.append(parts[1])
    assert x0 is not None and y0 is not None and rows, "g.txt needs x0, y0 and rows"
    widths = {len(r) for r in rows}
    assert len(widths) == 1, f"ragged rows in {path}: {widths}"
    return x0, y0, rows


def build(glyph_path: Path, out_path: Path, quiet: bool) -> int:
    de_bytes, en_bytes = SRC_DE.read_bytes(), SRC_EN.read_bytes()
    assert de_bytes == en_bytes, "the original res/de/marcador.png is expected to be byte-identical to en"
    src_chunks = chunks(de_bytes)
    types = [t for t, _ in src_chunks]
    assert types == [b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND"], types
    ihdr, plte, trns = src_chunks[0][1], src_chunks[1][1], src_chunks[2][1]
    w, h, depth, ctype, comp, filt, lace = struct.unpack(">IIBBBBB", ihdr)
    assert (w, h, depth, ctype, comp, filt, lace) == (W, H, 8, 3, 0, 0, 0), (w, h, depth, ctype, lace)
    assert trns == b"\x00", trns.hex()
    palette = [tuple(plte[i:i + 3]) for i in range(0, len(plte), 3)]
    assert len(palette) == 26, len(palette)
    rgb_to_idx = {}
    for i, rgb in enumerate(palette):
        rgb_to_idx.setdefault(rgb, i)
    font_idx = {rgb_to_idx[rgb] for rgb in FONT_RGB.values()}
    sym_idx = {s: rgb_to_idx[rgb] for s, rgb in {**FONT_RGB, **OTHER_RGB}.items()}

    en = load_indices(SRC_EN)
    img = [row[:] for row in en]

    # --- 2. remove the en 'y', restore the reconstructed background under it
    bg = Image.open(BG).convert("RGBA")
    assert bg.size == (42, 22), bg.size
    bgp = bg.load()
    x0, y0, x1, y1 = Y_BOX
    removed = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if en[y][x] in font_idx:
                r, g, b, a = bgp[x, y]
                assert a == 255, (x, y, a)
                assert (r, g, b) in rgb_to_idx and rgb_to_idx[(r, g, b)] not in font_idx, (x, y, (r, g, b))
                img[y][x] = rgb_to_idx[(r, g, b)]
                removed += 1
    assert removed == Y_PIXELS, f"removed {removed} 'y' pixels, expected {Y_PIXELS}"

    # --- 3. paint the g
    gx0, gy0, rows = read_glyph(glyph_path)
    painted = 0
    for dy, row in enumerate(rows):
        for dx, s in enumerate(row):
            if s == ".":
                continue
            assert s in sym_idx, f"unknown symbol {s!r} in {glyph_path} at row {dy} col {dx}"
            x, y = gx0 + dx, gy0 + dy
            assert 0 <= x < W and 0 <= y < H
            img[y][x] = sym_idx[s]
            painted += 1

    # --- 4. checks
    errors = []
    for y in range(H):
        for x in range(W):
            inside = WORD_BOX[0] <= x <= WORD_BOX[2] and WORD_BOX[1] <= y <= WORD_BOX[3]
            if (not inside or x <= KEEP_X_MAX) and img[y][x] != en[y][x]:
                errors.append(f"pixel ({x},{y}) changed outside the allowed area")
            if inside and x > KEEP_X_MAX and img[y][x] in font_idx:
                if x >= 39:
                    errors.append(f"word ink at ({x},{y}): x >= 39 is the numeral frame")
                if NUMERAL_BOX[1] <= y <= NUMERAL_BOX[3] and x >= NUMERAL_BOX[0]:
                    errors.append(f"word ink at ({x},{y}) would be painted black by v.b(int)")
            if not 0 <= img[y][x] < len(palette):
                errors.append(f"index {img[y][x]} at ({x},{y}) out of palette")
    if errors:
        print("\n".join(errors[:40]), file=sys.stderr)
        print(f"FAILED: {len(errors)} errors", file=sys.stderr)
        return 2

    # --- 5. write: IHDR/PLTE/tRNS verbatim, one IDAT, IEND
    raw = b"".join(b"\x00" + bytes(row) for row in img)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"PLTE", plte) + chunk(b"tRNS", trns)
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(png)

    # re-read and confirm
    back = load_indices(out_path)
    assert back == img, "written PNG does not decode to the intended indices"
    assert [t for t, _ in chunks(out_path.read_bytes())] == [b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND"]
    rgba_new, rgba_en = Image.open(out_path).convert("RGBA"), Image.open(SRC_EN).convert("RGBA")
    changed = [(x, y) for y in range(H) for x in range(W) if rgba_new.getpixel((x, y)) != rgba_en.getpixel((x, y))]
    if not quiet:
        xs = [p[0] for p in changed]
        ys = [p[1] for p in changed]
        print(f"wrote {out_path} ({len(png)} B, md5 {hashlib.md5(png).hexdigest()})")
        print(f"  removed {removed} 'y' pixels, painted {painted} 'g' pixels from {glyph_path}")
        print(f"  {len(changed)} pixels differ from en, bbox x {min(xs)}..{max(xs)} y {min(ys)}..{max(ys)}")
        ink = [(x, y) for y in range(H) for x in range(KEEP_X_MAX + 1, 40) if img[y][x] in font_idx]
        print(f"  g ink bbox x {min(p[0] for p in ink)}..{max(p[0] for p in ink)}"
              f" y {min(p[1] for p in ink)}..{max(p[1] for p in ink)}; rows 7..14 max x "
              f"{max(p[0] for p in ink if 7 <= p[1] <= 14)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--glyph", type=Path, default=GLYPH)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    return build(a.glyph, a.out, a.quiet)


if __name__ == "__main__":
    sys.exit(main())

# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Parchment ("pergamino") codec for the Swedish build: res/letras font, text bytes, layout,
measurement and page rendering. A faithful port of work/phaseA/scripts/letras_render.py, which is
pixel-identical to the real abadia.y code on all 93 shipped pages and the Swedish prototype
(FORMAT §4, §8). Importable (build.py, render_strings.py, regress.py) and a CLI:

  uv run tools/letras.py encode TEXT.txt OUT.bin           Swedish UTF-8 text -> game bytes (FORMAT §4.7)
  uv run tools/letras.py check FILE [--letras L] [--text]  decode + measure every line (ink edge <= 244)
  uv run tools/letras.py width "LINE" [--letras L]         pen advance and ink right edge of one line
  uv run tools/letras.py pages FILE OUTDIR [--letras L] [--text] [--res RES] [--scale K]
                                                          render every page the game shows (1x + Kx)
  uv run tools/letras.py dump [--letras L]                 every glyph: address, pixels, advance

FILE is raw game bytes unless --text (then a UTF-8 text file in the translation format). --letras
takes a letras file or a jar (its res/letras: e.g. the built game/TheAbbeyOfCrimeExtensum.jar) and
defaults to the original res/letras (work/jar/res/letras). Only `pages` needs Pillow.

Format (VERIFIED, FORMAT §4.2-4.3): letras is a Z80 memory image based at 0xA6D7. Bytes 0..161 are
the LE16 table, entry k = code 44+k (81 entries, codes 44..124); glyph data = one byte per pixel
(dx = low nibble, dy = high nibble 0..14) in handwriting order, ended by 0xF? whose low nibble is the
advance. Pen origin (76,18), 16 px per line, 11 lines per page; capitals (code & 0x60 == 0x40) red.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import struct
import sys
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_RES = ROOT / "work" / "jar" / "res"

BASE = 42711           # 0xA6D7, y.class: ldc 42711
FIRST_CODE = 44        # (f - 32 - 12) << 1
N_TABLE = 81           # codes 44..124
ORIG_SIZE = 5564
MAX_START = 0xFFFF - BASE   # 22824: largest glyph start offset a u16 address can hold

X0, Y0 = 76, 18
LINE_H = 16
PAGE_LAST_Y = 178
LINES_PER_PAGE = 11
SPACE_W = 8
PARCH_W = PARCH_H = 190
PARCH_X, PARCH_Y = (320 - PARCH_W) >> 1, (208 - PARCH_H) >> 1
INK_ALPHA = 0xC0
RED = 0xD00000
INK_LIMIT = 244        # FORMAT §4.5: ink right edge <= 244 on every line

OVERLAYS: dict[str, list[tuple[int, int, int]]] = {
    "acute": [(3, 0, 1), (4, 0, 2), (5, 0, 1), (2, 1, 1), (3, 1, 1)],
    "grave": [(2, 0, 1), (3, 0, 2), (4, 0, 1), (4, 1, 1), (5, 1, 1)],
    "circumflex": [(1, 0, 1), (2, 0, 3), (3, 0, 2), (0, 1, 1), (1, 1, 2), (2, 1, 1), (3, 1, 1), (4, 1, 1),
                   (0, 2, 1), (1, 2, 1), (4, 2, 1), (5, 2, 1)],
    "apostrophe": [(1, 1, 1), (2, 1, 1), (0, 2, 1), (1, 2, 1), (0, 3, 1), (1, 3, 1)],
    "cedilla": [(2, 13, 2), (3, 13, 2), (0, 14, 1), (1, 14, 2), (2, 14, 1), (0, 15, 1), (1, 15, 1)],
    "ogonek": [(3, 13, 1), (4, 13, 1), (3, 14, 1), (4, 14, 1), (5, 14, 1)],
    "dot": [(3, 1, 1), (4, 1, 1), (3, 2, 1), (4, 2, 1)],
    "stroke": [(3, 6, 1), (4, 6, 2), (5, 6, 1), (1, 7, 1), (2, 7, 2), (3, 7, 1), (0, 8, 1), (1, 8, 1)],
}
SINGLE = {192: (65, "grave"), 224: (97, "grave"), 225: (97, "acute"), 231: (99, "cedilla"),
          232: (101, "grave"), 233: (101, "acute"), 236: (105, "grave"), 237: (105, "acute"),
          241: (47, None), 242: (111, "grave"), 243: (111, "acute"), 249: (117, "grave"),
          250: (117, "acute")}
APOSTROPHES = {39, 146, 180}
LEADS = {195, 196, 197}
TRAIL = {130: (108, "stroke"), 132: (110, "acute"), 133: (97, "ogonek"), 135: (99, "acute"),
         153: (101, "ogonek"), 155: (115, "acute"), 161: (97, "acute"), 169: (101, "acute"),
         173: (105, "acute"), 177: (47, None), 179: (111, "acute"), 186: (122, "acute"),
         188: (122, "dot")}
CIRC = {226: 97, 234: 101, 238: 105, 244: 111, 251: 117}

# ---------------------------------------------------------------- Swedish byte map (FORMAT §4.7)
SV_SLOTS = {"Ä": 0x5B, "Ö": 0x5C, "Å": 0x5D, "å": 0x60, "ä": 0x7B, "ö": 0x7C}
SLOT_CHARS = {v: k for k, v in SV_SLOTS.items()}
TEXT_MAP: dict[str, bytes] = {}
for _c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1237,-.:; ":
    TEXT_MAP[_c] = _c.encode("ascii")
for _c, _b in SV_SLOTS.items():
    TEXT_MAP[_c] = bytes([_b])
for _c, _b in {"À": 0xC0, "à": 0xE0, "á": 0xE1, "â": 0xE2, "ç": 0xE7, "è": 0xE8, "é": 0xE9, "ê": 0xEA,
               "ì": 0xEC, "í": 0xED, "î": 0xEE, "ñ": 0xF1, "ò": 0xF2, "ó": 0xF3, "ô": 0xF4, "ù": 0xF9,
               "ú": 0xFA, "û": 0xFB}.items():
    TEXT_MAP[_c] = bytes([_b])
# Polish letters through the lead-byte + trail table (the lead byte is ignored by y.a()).
for _c in "łńąćęśźż":
    TEXT_MAP[_c] = _c.encode("utf-8")


class GameHang(Exception):
    pass


class Letras:
    def __init__(self, data: bytes):
        self.data = bytes(data)
        self.table: dict[int, int] = {}
        for k in range(N_TABLE):
            self.table[FIRST_CODE + k] = struct.unpack_from("<H", self.data, 2 * k)[0]
        self.glyphs: dict[int, dict] = {}
        for code in range(FIRST_CODE, FIRST_CODE + N_TABLE):
            g = self.glyph(code)
            if g is not None:
                self.glyphs[code] = g

    def glyph(self, code: int):
        idx = (code - FIRST_CODE) * 2
        if idx < 0 or idx + 1 >= len(self.data):
            return None
        addr = self.data[idx] | (self.data[idx + 1] << 8)
        off = addr - BASE
        if not (0 <= off < len(self.data)):
            return None
        pix = []
        o = off
        while o < len(self.data):
            b = self.data[o]
            if b & 0xF0 == 0xF0:
                return {"code": code, "addr": addr, "off": off, "end": o, "pixels": pix, "adv": b & 0x0F}
            pix.append((b & 0x0F, b >> 4))
            o += 1
        return None


def load_letras(path=None) -> Letras:
    """A letras file, or a jar (then its res/letras entry, e.g. game/TheAbbeyOfCrimeExtensum.jar)."""
    path = pathlib.Path(path or DEFAULT_RES / "letras")
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            return Letras(zf.read("res/letras"))
    return Letras(path.read_bytes())


# ---------------------------------------------------------------- decoding (exact port)
def decode(text: bytes, letras: Letras):
    """Yield tokens exactly as y.a state 1 consumes them:
    ("glyph", code, overlay, color, src_pos) | ("space",) | ("cr",) | ("lf",) | ("end",)"""
    m = 0
    while True:
        if m >= len(text):
            raise GameHang(f"ran past the end of the text without 0x1A (offset {m})")
        f = text[m]
        start = m
        if f == 10:
            yield ("lf",)
        elif f == 13:
            yield ("cr",)
        elif f == 26:
            yield ("end",)
            return
        elif f == 32:
            yield ("space",)
        else:
            ov = None
            if f in APOSTROPHES:
                m += 1
                if m >= len(text):
                    raise GameHang(f"prefix byte {f:#x} at {start} is the last byte")
                f = text[m]
                ov = "apostrophe"
                if f in (10, 13, 26, 32):
                    raise GameHang(f"prefix byte at {start} followed by control/space byte {f:#x} (AIOOBE)")
            elif f in LEADS:
                m += 1
                if m >= len(text):
                    raise GameHang(f"lead byte {f:#x} at {start} is the last byte")
                f = text[m]
                if f in (10, 13, 26, 32):
                    raise GameHang(f"lead byte at {start} followed by control/space byte {f:#x} (AIOOBE)")
                if f in TRAIL:
                    f, ov = TRAIL[f]
            elif f in SINGLE:
                f, ov = SINGLE[f]
            if f in CIRC:
                f = CIRC[f]
                ov = ov if ov in ("acute", "grave") else "circumflex"
            color = RED if (f & 96) == 64 else 0
            idx = (f - FIRST_CODE) * 2
            if idx < 0:
                raise GameHang(f"byte {f} at {start}: < 44, negative table index (uncaught AIOOBE, the parchment freezes)")
            if f > FIRST_CODE + N_TABLE - 1:
                raise GameHang(f"byte {f} at {start}: > 124, outside the glyph table (garbage glyph or hang)")
            g = letras.glyph(f)
            if g is None:
                raise GameHang(f"byte {f} ({chr(f)!r}) at {start}: empty table entry, prints 'Caracter: {f}' forever")
            yield ("glyph", f, ov, color, start)
        m += 1


def layout(text: bytes, letras: Letras):
    """Pages as the game shows them; page = list of lines; line = dict(y, ops=[(x, code, ov, color)], pen_end)."""
    pages = [[]]
    i, j = X0, Y0
    line = {"y": j, "ops": [], "pen_end": X0}
    pages[-1].append(line)

    def newline():
        nonlocal line
        line = {"y": j, "ops": [], "pen_end": i}
        pages[-1].append(line)

    for tok in decode(text, letras):
        kind = tok[0]
        if kind == "end":
            break
        if kind == "space":
            i += SPACE_W
            line["pen_end"] = i
        elif kind == "cr":
            i = X0
            j += LINE_H
            if j > PAGE_LAST_Y:
                j = Y0
                pages.append([])
            newline()
        elif kind == "lf":
            i, j = X0, Y0
            pages.append([])
            newline()
        else:
            _, code, ov, color, _src = tok
            line["ops"].append((i, code, ov, color))
            i += letras.glyphs[code]["adv"]
            line["pen_end"] = i
    return pages


def line_pixels(line, letras: Letras):
    """Absolute (x, y) of every ink pixel of a line (glyph pixels and overlays)."""
    out = []
    for (x, code, ov, color) in line["ops"]:
        for (dx, dy) in letras.glyphs[code]["pixels"]:
            out.append((x + dx, line["y"] + dy))
        if ov:
            for (dx, dy, _n) in OVERLAYS[ov]:
                out.append((x + dx, line["y"] + dy))
    return out


def ink_extent(line, letras: Letras):
    xs = [x for x, _ in line_pixels(line, letras)]
    return (min(xs), max(xs)) if xs else (None, None)


# ---------------------------------------------------------------- Swedish text <-> bytes
def encode_text(text: str, where: str = "text") -> tuple[bytes, list[str]]:
    """Translation text (UTF-8 str, LF lines) -> game bytes. Returns (bytes, errors)."""
    errors = []
    if text.startswith("﻿"):
        errors.append(f"{where}: starts with a BOM")
        text = text[1:]
    if "\r" in text:
        errors.append(f"{where}: contains CR characters (use LF line endings)")
        text = text.replace("\r", "")
    text = text.rstrip("\n")
    if not text.strip():
        errors.append(f"{where}: no text")
    lines = text.split("\n")
    trailing = 0
    while len(lines) - trailing > 1 and not lines[len(lines) - 1 - trailing].strip():
        trailing += 1
    if trailing and text.strip():
        errors.append(f"{where} line {len(lines) - trailing + 1}: the text ends with {trailing} line(s) holding only "
                      f"whitespace; delete them (each adds a CR before the end and can turn the page to a blank "
                      f"parchment, FORMAT §4.5)")
    out = bytearray()
    for ln, line in enumerate(lines, 1):
        if ln > 1:
            out.append(0x0D)
        for col, ch in enumerate(line, 1):
            b = TEXT_MAP.get(ch)
            if b is None:
                errors.append(f"{where} line {ln} col {col}: character {ch!r} (U+{ord(ch):04X}) is not allowed "
                              f"on the parchment (FORMAT §4.7)")
                continue
            out += b
    out.append(0x1A)
    return bytes(out), errors


def load_text_file(path, where: str | None = None) -> tuple[bytes | None, list[str], list[str]]:
    """Read a translation parchment file exactly as tools/build.py does: raw bytes, strict UTF-8
    (CR, BOM and every non-whitelisted character are errors), then encode_text.
    Returns (game bytes or None, errors, source lines for messages)."""
    path = pathlib.Path(path)
    where = where or str(path)
    try:
        raw = path.read_bytes()
    except OSError as ex:
        return None, [f"{where}: cannot read: {ex}"], []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as ex:
        return None, [f"{where}: not UTF-8 ({ex})"], []
    data, errors = encode_text(text, where)
    return (None if errors else data), errors, text.rstrip("\n").split("\n")


def glyph_text(line) -> str:
    """Readable text of a laid-out line (spaces from pen gaps are not shown; slots as åäöÅÄÖ)."""
    return "".join(SLOT_CHARS.get(c, "ñ" if c == 47 else chr(c)) for (_, c, _, _) in line["ops"])


def check_bytes(data: bytes, letras: Letras, where: str = "parchment", src_lines=None) -> dict:
    """Decode and measure. Returns {errors, warnings, pages, lines, max_ink, line_info}.
    src_lines: the source text lines (for messages), when the bytes contain no LF."""
    errors: list[str] = []
    warnings: list[str] = []
    res = {"errors": errors, "warnings": warnings, "pages": 0, "lines": 0, "max_ink": 0, "line_info": []}
    if not data.endswith(b"\x1a"):
        errors.append(f"{where}: does not end with 0x1A")
    n1a = data.count(0x1A)
    if n1a != 1:
        errors.append(f"{where}: {n1a} 0x1A bytes (exactly one, at the end, expected)")
    for pos, b in enumerate(data):
        if b < 44 and b not in (0x0D, 0x1A, 0x20):
            errors.append(f"{where}: byte {b:#04x} at offset {pos} (< 44 and not CR/space/1A: the parchment freezes)")
    if data.endswith(b"\r\x1a"):
        warnings.append(f"{where}: a CR right before 0x1A (can end on a blank page)")
    try:
        pages = layout(data, letras)
    except GameHang as ex:
        errors.append(f"{where}: {ex}")
        return res
    res["pages"] = len(pages)
    n = 0
    for pi, page in enumerate(pages, 1):
        if not any(line["ops"] for line in page):
            last = " (the last page: the ending waits for Space on an empty parchment)" if pi == len(pages) else ""
            errors.append(f"{where} page {pi}: no ink at all, a blank parchment page{last}; remove the "
                          f"blank/space-only lines that fill it (FORMAT §4.5)")
        for li, line in enumerate(page, 1):
            res["lines"] += 1
            pix = line_pixels(line, letras)
            hi = max((x for x, _ in pix), default=None)
            text = src_lines[n] if src_lines and n < len(src_lines) else glyph_text(line)
            n += 1
            res["line_info"].append({"page": pi, "line": li, "ink_right": hi, "pen_end": line["pen_end"], "glyphs": text})
            if hi is not None:
                res["max_ink"] = max(res["max_ink"], hi)
                if hi > INK_LIMIT:
                    errors.append(f"{where} page {pi} line {li} (text line {n}): ink right edge x={hi} > {INK_LIMIT}, "
                                  f"{hi - INK_LIMIT} px too wide: {text!r}")
            if li == LINES_PER_PAGE:
                low = [(x, y) for (x, y) in pix if y >= line["y"] + 13 and not (110 <= x <= 206)]
                if low:
                    warnings.append(f"{where} page {pi} line 11 (text line {n}): descender pixels at x="
                                    f"{sorted(set(x for x, _ in low))} on the curved bottom edge (keep them within "
                                    f"110..206): {text!r}")
    return res


# ---------------------------------------------------------------- letras_add.json
def apply_add(orig: bytes, add: dict) -> tuple[bytes, list[str]]:
    """Append the glyphs of letras_add.json. Returns (new letras, problems). The streams go at EOF in
    ascending slot order, each followed by 0xF0|advance; the slot gets LE16 0xA6D7 + offset."""
    problems: list[str] = []
    data = bytearray(orig)
    if set(add) - {"glyphs"}:
        problems.append(f"letras_add: unknown top-level keys {sorted(set(add) - {'glyphs'})}")
    glyphs = add.get("glyphs")
    if not isinstance(glyphs, dict) or not glyphs:
        problems.append("letras_add: 'glyphs' must be a non-empty object")
        return bytes(data), problems
    parsed = {}
    for key, g in glyphs.items():
        if not re.fullmatch(r"[0-9A-F]{2}", key):
            problems.append(f"letras_add: slot key {key!r} must be exactly 2 uppercase hex digits "
                            f"({[f'{s:02X}' for s in sorted(SLOT_CHARS)]})")
            continue
        slot = int(key, 16)
        if slot not in SLOT_CHARS:
            problems.append(f"letras_add: slot {key!r} is not one of {[f'{s:02X}' for s in sorted(SLOT_CHARS)]}")
            continue
        if not isinstance(g, dict):
            problems.append(f"letras_add {key}: not an object")
            continue
        if g.get("char") != SLOT_CHARS[slot]:
            problems.append(f"letras_add {key}: char {g.get('char')!r}, expected {SLOT_CHARS[slot]!r}")
        adv = g.get("advance")
        if not isinstance(adv, int) or isinstance(adv, bool) or not 0 <= adv <= 15:
            problems.append(f"letras_add {key}: advance {adv!r} not an int 0..15")
            continue
        pix = g.get("pixels")
        if not isinstance(pix, list) or not pix:
            problems.append(f"letras_add {key}: pixels must be a non-empty list (an empty glyph inherits the previous colour)")
            continue
        ok = True
        for p in pix:
            if (not isinstance(p, list) or len(p) != 2 or not all(isinstance(v, int) and not isinstance(v, bool) for v in p)
                    or not 0 <= p[0] <= 15 or not 0 <= p[1] <= 14):
                problems.append(f"letras_add {key}: bad pixel {p!r} (need [dx 0..15, dy 0..14])")
                ok = False
        if not ok:
            continue
        idx = (slot - FIRST_CODE) * 2
        if orig[idx] != 0 or orig[idx + 1] != 0:
            problems.append(f"letras_add {key}: table entry is {orig[idx]:02x}{orig[idx + 1]:02x}, not empty")
            continue
        parsed[slot] = (adv, [tuple(p) for p in pix])
    for slot in sorted(parsed):
        adv, pix = parsed[slot]
        off = len(data)
        if off > MAX_START:
            problems.append(f"letras_add {slot:02X}: start offset {off} > {MAX_START} (u16 address overflow)")
            continue
        struct.pack_into("<H", data, (slot - FIRST_CODE) * 2, BASE + off)
        data += bytes((dy << 4) | dx for dx, dy in pix) + bytes([0xF0 | adv])
    return bytes(data), problems


def verify_add(orig: bytes, new: bytes, add: dict) -> tuple[list[str], list[str]]:
    """Errors/warnings: original bytes 0..len-1 unchanged except the added slots' pointers (which
    were 0x0000); every added glyph decodes exactly; every other glyph decodes as before."""
    errors, warnings = [], []
    added = {int(k, 16): v for k, v in add.get("glyphs", {}).items()}
    allowed = set()
    for slot in added:
        idx = (slot - FIRST_CODE) * 2
        allowed |= {idx, idx + 1}
        if orig[idx] or orig[idx + 1]:
            errors.append(f"letras slot {slot:02X} was not 0x0000 in the original")
    if len(new) < len(orig):
        errors.append("letras shrank")
    changed = [k for k in range(len(orig)) if orig[k] != new[k]]
    bad = [k for k in changed if k not in allowed]
    if bad:
        errors.append(f"letras: original bytes changed outside the slot pointers: offsets {bad[:20]}")
    lo, ln = Letras(orig), Letras(new)
    for code in range(FIRST_CODE, FIRST_CODE + N_TABLE):
        if code in added:
            g = ln.glyphs.get(code)
            want = [tuple(p) for p in added[code]["pixels"]]
            if g is None or g["pixels"] != want or g["adv"] != added[code]["advance"]:
                errors.append(f"letras slot {code:02X}: decodes to {g and (g['pixels'], g['adv'])}, expected {(want, added[code]['advance'])}")
            # repeated pixels draw darker (stroke overlaps); 23 of the 62 original glyphs have them: not a problem
        else:
            a, b = lo.glyphs.get(code), ln.glyphs.get(code)
            if (a is None) != (b is None) or (a and (a["pixels"] != b["pixels"] or a["adv"] != b["adv"])):
                errors.append(f"letras code {code}: glyph changed")
    return errors, warnings


# ---------------------------------------------------------------- drawing (Pillow, lazy)
def _mul8(a: int, b: int) -> int:
    return (a * b + 127) // 255


def _blend(px, color: int, times: int = 1):
    r, g, b = px[:3]
    sr, sg, sb = (color >> 16) & 255, (color >> 8) & 255, color & 255
    for _ in range(times):
        r = _mul8(INK_ALPHA, sr) + _mul8(255 - INK_ALPHA, r)
        g = _mul8(INK_ALPHA, sg) + _mul8(255 - INK_ALPHA, g)
        b = _mul8(INK_ALPHA, sb) + _mul8(255 - INK_ALPHA, b)
    return (r, g, b)


def render_pages(text: bytes, letras: Letras, pergamino_png):
    """List of 320x208 RGB PIL images, one per page, as Abadia.ac looks when the page is complete.
    pergamino_png: path or bytes of res/pergamino.png."""
    import io
    from PIL import Image
    src = pergamino_png if isinstance(pergamino_png, (bytes, bytearray)) else pathlib.Path(pergamino_png).read_bytes()
    perg = Image.open(io.BytesIO(src)).convert("RGBA")
    imgs = []
    for page in layout(text, letras):
        img = Image.new("RGB", (320, 208), (0, 0, 0))
        img.paste(perg, (PARCH_X, PARCH_Y), perg)
        px = img.load()
        for line in page:
            for (x, code, ov, color) in line["ops"]:
                for (dx, dy) in letras.glyphs[code]["pixels"]:
                    X, Y = x + dx, line["y"] + dy
                    if 0 <= X < 320 and 0 <= Y < 208:
                        px[X, Y] = _blend(px[X, Y], color)
                if ov:
                    for (dx, dy, n) in OVERLAYS[ov]:
                        X, Y = x + dx, line["y"] + dy
                        if 0 <= X < 320 and 0 <= Y < 208:
                            px[X, Y] = _blend(px[X, Y], color, n)
        imgs.append(img)
    return imgs


# ---------------------------------------------------------------- CLI
def _read_input(path: str, as_text: bool) -> tuple[bytes, list[str] | None]:
    """(game bytes, source lines or None). --text files are read exactly as the build reads them."""
    if as_text:
        data, errs, src_lines = load_text_file(path)
        for e in errs:
            print("ERROR", e)
        if errs:
            sys.exit(1)
        return data, src_lines
    try:
        return pathlib.Path(path).read_bytes(), None
    except OSError as ex:
        print("ERROR", ex)
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--letras", default=None, help="letras file (default: original)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("encode")
    e.add_argument("text")
    e.add_argument("out")
    c = sub.add_parser("check")
    c.add_argument("file")
    c.add_argument("--text", action="store_true")
    w = sub.add_parser("width")
    w.add_argument("line")
    p = sub.add_parser("pages")
    p.add_argument("file")
    p.add_argument("outdir")
    p.add_argument("--text", action="store_true")
    p.add_argument("--res", default=str(DEFAULT_RES))
    p.add_argument("--scale", type=int, default=3)
    sub.add_parser("dump")
    for sp in (e, c, w, p, sub.choices["dump"]):
        sp.add_argument("--letras", default=argparse.SUPPRESS)
    a = ap.parse_args()
    try:
        letras = load_letras(a.letras)
    except (OSError, KeyError, zipfile.BadZipFile, struct.error, IndexError, ValueError) as ex:
        print(f"ERROR cannot read letras {a.letras or DEFAULT_RES / 'letras'}: {ex}"
              + ("" if a.letras is None else " (after a failed build work/build/ is gone; pass the built jar, "
                 "e.g. --letras game/TheAbbeyOfCrimeExtensum.jar)"))
        sys.exit(1)
    if a.cmd == "encode":
        data, _ = _read_input(a.text, True)
        pathlib.Path(a.out).write_bytes(data)
        print(f"wrote {a.out} ({len(data)} bytes)")
    elif a.cmd == "check":
        data, src_lines = _read_input(a.file, a.text)
        r = check_bytes(data, letras, a.file, src_lines)
        for li in r["line_info"]:
            print(f"p{li['page']} l{li['line']:2d} ink_right={li['ink_right']} pen_end={li['pen_end']} {li['glyphs']!r}")
        for x in r["warnings"]:
            print("WARNING", x)
        for x in r["errors"]:
            print("ERROR", x)
        print(f"pages={r['pages']} lines={r['lines']} max_ink_right={r['max_ink']} errors={len(r['errors'])}")
        sys.exit(1 if r["errors"] else 0)
    elif a.cmd == "width":
        data, errs = encode_text(a.line, "line")
        if errs:
            print("\n".join(errs))
            sys.exit(1)
        line = layout(data, letras)[0][0]
        lo, hi = ink_extent(line, letras)
        print(f"pen advance={line['pen_end'] - X0}px  ink right edge x={hi}  (limit {INK_LIMIT})")
    elif a.cmd == "pages":
        from PIL import Image
        try:
            imgs = render_pages(_read_input(a.file, a.text)[0], letras, pathlib.Path(a.res) / "pergamino.png")
        except GameHang as ex:
            print("ERROR", ex)
            sys.exit(1)
        out = pathlib.Path(a.outdir)
        out.mkdir(parents=True, exist_ok=True)
        for k, im in enumerate(imgs, 1):
            im.save(out / f"page{k:02d}.png")
            if a.scale > 1:
                im.resize((320 * a.scale, 208 * a.scale), Image.NEAREST).save(out / f"page{k:02d}_x{a.scale}.png")
        print(f"{len(imgs)} pages -> {out}")
    elif a.cmd == "dump":
        for code in range(FIRST_CODE, FIRST_CODE + N_TABLE):
            g = letras.glyphs.get(code)
            if g:
                xs = [q[0] for q in g["pixels"]] or [0]
                ys = [q[1] for q in g["pixels"]] or [0]
                print(f"{code:3d} {chr(code)!r:5} addr=0x{g['addr']:04X} off={g['off']:5d} px={len(g['pixels']):3d} "
                      f"adv={g['adv']:2d} x={min(xs)}..{max(xs)} y={min(ys)}..{max(ys)}"
                      + (f"  [{SLOT_CHARS[code]}]" if code in SLOT_CHARS else ""))
            else:
                print(f"{code:3d} {chr(code)!r:5} addr=0x{letras.table[code]:04X} -> no glyph")


if __name__ == "__main__":
    main()

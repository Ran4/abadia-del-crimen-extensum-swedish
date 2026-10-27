# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""The Swedish conjunction "och" in the credit screens' script font (images.md §3.5, FORMAT §6.2).

The script font exists only as the conjunctions a d e i n t y (es "y", en "and", it "e", fr "et",
pl "i"). It is cream (253,246,231) with 16 alpha levels (multiples of 17) and has no glow. None of
o, c, h exists, so each is composed from shipped pixels plus hand corrections:

  o  the bowl of the en "and"'s d, with the d's stem foot and exit stroke taken away;
  c  the it/fr open e (identical in both), with the loop's inner stroke taken away, leaving the
     top arc as the c's beak;
  h  the en d's ascender (rows 143..148) set on the en n, whose stem continues it down.

Sources (read-only data, alpha taken only where RGB == cream, so a neighbouring Fraktur glow is
never picked up):
  work/jar/res/en/intro/manuydani.png   en "and" [49,143,82,158] (alpha>0 box); checked pixel-
                                        identical to the "and" in en pacoyjuan and en pelicula
  work/jar/res/it/intro/manuydani.png   it "e" [76,144,83,154]
Recipes and hand corrections: assets_sv/image_src/script/och_{o,c,h}.txt (format in each file).

Coordinates. Everything is composed in en manuydani screen coordinates, so "och" sits on the
"and"'s baseline (row 157), with the same x-height top (row 149) and ascender top (row 143). The
layer returned by och_layer() is the alpha>0 bounding box of the word (32x16). Its inclusive box
in those coordinates is och_metrics()["box_in_manuydani"] = (50,143,81,158), one column inside
the "and"'s alpha box (49..82) at each end: o starts on the a's strong left edge, and the h's
final AA column is one short of the d's.

Placing it. och_position(image, align) gives the top-left paste position in en/de `image`
(manuydani, pacoyjuan or pelicula), always on the "and"'s baseline:
  align="right"    (default) the layer's right edge on the "and"'s right alpha edge; in
                   manuydani that is x=51, one column right of box_in_manuydani
  align="left"     the layer's left edge on the "and"'s left alpha edge (x=49 in manuydani)
  align="compose"  exactly box_in_manuydani, carried over to `image` (x=50 in manuydani)
The builders may shift it horizontally (place_och's dx).

Use from a builder (uv inline script with pillow==11.3.0; img = the de image as RGBA):
    sys.path.insert(0, str(ROOT / "tools/images"))
    from script_och import erase_and, place_och
    erase_and(img, "pacoyjuan")              # the "and": cream ink in AND_BOX -> alpha 0
    place_och(img, "pacoyjuan")              # "och" on the same baseline, right-aligned
erase_and clears only pixels whose RGB is cream (to cream with alpha 0, which is what every
transparent pixel around the "and" already holds); anything else in the box is kept, e.g. in en
pacoyjuan the J's glow, RGB (29,8,27), at x=79 on rows 158..166. It first checks that the box
holds exactly the en "and". place_och refuses to put ink on a pixel that is not fully
transparent unless allow_overlap=True, so a shifted "och" cannot silently blend into a glow.

API (no side effects on import; everything is computed on call and cached):
  och_layer()            -> PIL RGBA image (RGB cream everywhere, alpha 0 outside the ink)
  och_metrics()          -> dict: size, box_in_manuydani (inclusive box of the layer in en
                            manuydani coordinates), baseline_row / xheight_top_row /
                            ascender_top_row (rows inside the layer)
  AND_BOX[image]            inclusive alpha>0 box of the en "and" in manuydani/pacoyjuan/pelicula
  och_position(image, align="right") -> (x, y) top-left paste position in that image
  erase_and(img, image)  -> number of "and" pixels cleared (img is changed in place)
  place_och(img, image, align="right", dx=0, allow_overlap=False) -> (x, y) used
  layer_png_bytes()      -> the layer as a deterministic PNG (IHDR, IDAT, IEND; zlib level 9)

CLI: uv run tools/images/script_och.py [--out DIR] [--quiet] [--show]
  writes into DIR (default work/phaseD/och/; inside the project only there or below it):
    och_layer.png            the layer itself (RGBA, 1x)
    och_6x.png, och_4x.png   the layer on black next to en "and", es "y", it "e", fr "et"
                             (cut from the shipped images), scaled 6x and 4x, nearest neighbour
    context_4x.png           en manuydani, pacoyjuan and pelicula, each shipped and then with the
                             "and" replaced through erase_and + place_och (on black), 4x
  and prints the layer's sha256 and metrics; --show also prints each composed letter as a hex
  alpha map (alpha/17; '.' = 0) next to a map of the hand corrections, and the whole word.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import struct
import sys
import zlib
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "work/jar/res"
SRC_DIR = ROOT / "assets_sv/image_src/script"
OUT_DIR = ROOT / "work/phaseD/och"      # the only place inside the project the CLI writes to
LETTERS = ("o", "c", "h")

CREAM = (253, 246, 231)
W, H = 320, 208
HEX = "0123456789abcdef"

# Inclusive alpha>0 boxes of the en "and" (cream pixels only). The three are the same 34x16 pixels.
AND_BOX = {
    "manuydani": (49, 143, 82, 158),
    "pacoyjuan": (46, 158, 79, 173),
    "pelicula": (26, 78, 59, 93),
}
AND_BASELINE_MANUYDANI = 157     # last core row of a, n, d (row 158 holds only AA)
AND_XTOP_MANUYDANI = 149         # x-height top (a has a faint row 148 above it, as e does)
AND_ASC_TOP_MANUYDANI = 143      # top of the d's ascender


# ---------------------------------------------------------------------------------------- sources
def _open_rgba(path: Path) -> Image.Image:
    with Image.open(path) as im:
        return im.convert("RGBA")


def _cream_alpha(im: Image.Image) -> tuple[tuple[int, ...], ...]:
    """Alpha of the cream pixels of an RGBA image (0 where RGB != cream)."""
    w, h = im.size
    data = im.tobytes()
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            i = 4 * (y * w + x)
            row.append(data[i + 3] if tuple(data[i:i + 3]) == CREAM else 0)
        rows.append(tuple(row))
    return tuple(rows)


@functools.lru_cache(maxsize=None)
def _alpha(lang: str, name: str) -> tuple[tuple[int, ...], ...]:
    """Alpha of the cream pixels of a shipped intro image (0 where RGB != cream)."""
    path = RES / lang / "intro" / f"{name}.png"
    im = _open_rgba(path)
    if im.size != (W, H):
        raise ValueError(f"{path}: size {im.size}, expected {(W, H)}")
    return _cream_alpha(im)


def _crop(alpha, box):
    x0, y0, x1, y1 = box
    return [list(alpha[y][x0:x1 + 1]) for y in range(y0, y1 + 1)]


@functools.lru_cache(maxsize=None)
def _and_reference() -> tuple[tuple[int, ...], ...]:
    """Cream alpha of the en "and" (its AND_BOX in en manuydani)."""
    return tuple(tuple(r) for r in _crop(_alpha("en", "manuydani"), AND_BOX["manuydani"]))


@functools.lru_cache(maxsize=None)
def check_sources() -> None:
    """The en "and" must be the same pixels in all three images, with nothing else around it,
    and the it "e" must be the same drawing as the e of fr "et". Raises ValueError."""
    ref = None
    for name, (x0, y0, x1, y1) in AND_BOX.items():
        c = _crop(_alpha("en", name), (x0 - 1, y0 - 1, x1 + 1, y1 + 1))
        if not all(v == 0 for v in c[0] + c[-1] + [r[0] for r in c] + [r[-1] for r in c]):
            raise ValueError(f"en {name}: the 'and' box {AND_BOX[name]} is not tight / not isolated")
        if ref is None:
            ref = c
        if c != ref:
            raise ValueError(f"en {name}: 'and' differs from en manuydani")
        if not all(v % 17 == 0 for r in c for v in r):
            raise ValueError(f"en {name}: 'and' alpha not a multiple of 17")
    # (box = the e's box [76,144,83,154] plus a 1-px margin, except on the right, where the fr t's
    # crossbar starts at x=66)
    if _crop(_alpha("it", "manuydani"), (75, 143, 83, 155)) != \
            _crop(_alpha("fr", "manuydani"), (57, 153, 65, 165)):
        raise ValueError("it 'e' (manuydani) and the e of fr 'et' differ")


# ----------------------------------------------------------------------------------- recipe files
def read_recipe(path: Path):
    """och_<l>.txt: '#' comments; 'piece LANG IMAGE x0 y0 x1 y1 at X Y' (any number);
    'x0 N', 'y0 N', then grid rows '<y> <chars>' in order from y0.
    Grid chars: '.' keeps the composed pixel; a hex digit n sets alpha = 17*n ('0' erases).
    Raises ValueError on any malformed line."""
    pieces, rows = [], []
    gx = gy = None
    for ln, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        parts = raw.split("#", 1)[0].split()
        if not parts:
            continue
        where = f"{path}:{ln}"
        if parts[0] == "piece":
            if len(parts) != 10 or parts[7] != "at":
                raise ValueError(f"{where}: bad piece line {raw!r}")
            lang, name = parts[1], parts[2]
            try:
                x0, y0, x1, y1, X, Y = map(int, parts[3:7] + parts[8:10])
            except ValueError:
                raise ValueError(f"{where}: piece coordinates must be integers") from None
            if lang not in ("en", "it", "fr", "es", "pl") or name not in AND_BOX:
                raise ValueError(f"{where}: unknown source {lang} {name}")
            if not (0 <= x0 <= x1 < W and 0 <= y0 <= y1 < H):
                raise ValueError(f"{where}: box off the image")
            pieces.append((lang, name, (x0, y0, x1, y1), (X, Y)))
        elif parts[0] in ("x0", "y0"):
            if len(parts) != 2 or not parts[1].lstrip("-").isdigit():
                raise ValueError(f"{where}: bad {parts[0]} line {raw!r}")
            if parts[0] == "x0":
                gx = int(parts[1])
            else:
                gy = int(parts[1])
        else:
            if gy is None or gx is None or len(parts) != 2 or not parts[0].isdigit():
                raise ValueError(f"{where}: unexpected line {raw!r}")
            if int(parts[0]) != gy + len(rows):
                raise ValueError(f"{where}: row label {parts[0]} out of order")
            if not all(ch == "." or ch in HEX for ch in parts[1]):
                raise ValueError(f"{where}: bad symbol in {parts[1]!r}")
            rows.append(parts[1])
    if not pieces or not rows:
        raise ValueError(f"{path}: needs pieces and a grid")
    if len({len(r) for r in rows}) != 1:
        raise ValueError(f"{path}: ragged grid rows")
    return pieces, (gx, gy, rows)


def _source_canvas(pieces) -> dict[tuple[int, int], int]:
    canvas: dict[tuple[int, int], int] = {}
    for lang, name, (x0, y0, x1, y1), (X, Y) in pieces:
        al = _alpha(lang, name)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                a = al[y][x]
                if a:
                    p = (X + x - x0, Y + y - y0)
                    canvas[p] = max(canvas.get(p, 0), a)
    return canvas


def compose_letter(letter: str, src_dir: Path = SRC_DIR):
    """Return (canvas, n_source_pixels, n_hand_set, n_erased) for one letter: canvas is
    {(x, y): alpha} in en manuydani coordinates; n_hand_set counts the pixels whose alpha the grid
    set to a non-zero value different from the source, n_erased the source pixels it cleared."""
    pieces, (gx, gy, rows) = read_recipe(src_dir / f"och_{letter}.txt")
    from_source = _source_canvas(pieces)
    canvas = dict(from_source)
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            p = (gx + dx, gy + dy)
            a = 17 * HEX.index(ch)
            if a:
                canvas[p] = a
            else:
                canvas.pop(p, None)
    hand = sum(1 for p, a in canvas.items() if from_source.get(p) != a)
    erased = sum(1 for p in from_source if p not in canvas)
    return canvas, len(from_source), hand, erased


# ------------------------------------------------------------------------------------------ layer
@functools.lru_cache(maxsize=None)
def _word() -> tuple[tuple[int, int, int, int], tuple[tuple[int, ...], ...]]:
    check_sources()
    word: dict[tuple[int, int], int] = {}
    for letter in LETTERS:
        canvas = compose_letter(letter)[0]
        for p, a in canvas.items():
            word[p] = max(word.get(p, 0), a)
    xs = [p[0] for p in word]
    ys = [p[1] for p in word]
    box = (min(xs), min(ys), max(xs), max(ys))
    rows = tuple(tuple(word.get((x, y), 0) for x in range(box[0], box[2] + 1))
                 for y in range(box[1], box[3] + 1))
    if not all(a % 17 == 0 for r in rows for a in r):
        raise ValueError("composed alpha is not a multiple of 17")
    return box, rows


def och_layer() -> Image.Image:
    """RGBA layer of "och": RGB cream everywhere, alpha from the composition (16 levels)."""
    _, rows = _word()
    im = Image.new("RGBA", (len(rows[0]), len(rows)), CREAM + (0,))
    im.putdata([CREAM + (a,) for r in rows for a in r])
    return im


def och_metrics() -> dict:
    box, rows = _word()
    return {
        "size": (len(rows[0]), len(rows)),
        "box_in_manuydani": box,
        "baseline_row": AND_BASELINE_MANUYDANI - box[1],
        "xheight_top_row": AND_XTOP_MANUYDANI - box[1],
        "ascender_top_row": AND_ASC_TOP_MANUYDANI - box[1],
    }


def _and_box(image: str) -> tuple[int, int, int, int]:
    try:
        return AND_BOX[image]
    except KeyError:
        raise ValueError(f"unknown image {image!r}; one of {sorted(AND_BOX)}") from None


def och_position(image: str, align: str = "right") -> tuple[int, int]:
    """Top-left paste position of och_layer() in en/de `image` that puts "och" on the "and"'s
    baseline. align="right": the layer's right edge on the "and"'s right alpha edge (in manuydani
    x=51, 1 px right of box_in_manuydani); "left": the layer's left edge on the "and"'s left alpha
    edge (x=49); "compose": box_in_manuydani itself, moved with the "and" (x=50)."""
    ix0, iy0, ix1, _ = _and_box(image)
    box, _ = _word()
    mx0, my0, _, _ = AND_BOX["manuydani"]
    y = box[1] + (iy0 - my0)
    if align == "right":
        x = ix1 - (box[2] - box[0])
    elif align == "left":
        x = ix0
    elif align == "compose":
        x = box[0] + (ix0 - mx0)
    else:
        raise ValueError(f"unknown align {align!r}; one of 'right', 'left', 'compose'")
    return x, y


def _check_screen(img: Image.Image) -> None:
    if img.mode != "RGBA" or img.size != (W, H):
        raise ValueError(f"expected an RGBA {W}x{H} image, got {img.mode} {img.size}")


def erase_and(img: Image.Image, image: str) -> int:
    """Remove the en "and" from `img` (an RGBA 320x208 copy of en/de `image`), in place.

    Only pixels whose RGB is cream inside AND_BOX[image] are touched: their alpha becomes 0 and
    their RGB stays cream, which is what every transparent pixel around the "and" holds. Anything
    else in the box (in pacoyjuan the J's glow, RGB (29,8,27), at x=79) is kept. Raises
    ValueError unless the box holds exactly the en "and". Returns the number of pixels cleared."""
    x0, y0, x1, y1 = _and_box(image)
    _check_screen(img)
    check_sources()
    box_img = img.crop((x0, y0, x1 + 1, y1 + 1))
    if _cream_alpha(box_img) != _and_reference():
        raise ValueError(f"{image}: AND_BOX {AND_BOX[image]} does not hold the en 'and' "
                         "(wrong image, or already erased?)")
    px = img.load()
    n = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            r, g, b, a = px[x, y]
            if (r, g, b) == CREAM and a:
                px[x, y] = CREAM + (0,)
                n += 1
    return n


def place_och(img: Image.Image, image: str, align: str = "right", dx: int = 0,
              allow_overlap: bool = False) -> tuple[int, int]:
    """Composite och_layer() onto `img` (RGBA 320x208, in place) at och_position(image, align)
    shifted dx columns. On fully transparent pixels this writes exactly cream + the layer's alpha.
    Raises ValueError if ink would land on a pixel with alpha > 0 (e.g. a Fraktur glow), unless
    allow_overlap=True, or if any ink would fall off the screen. Returns the (x, y) used."""
    _check_screen(img)
    x, y = och_position(image, align)
    x += dx
    layer = och_layer()
    if x < 0 or y < 0 or x + layer.width > W or y + layer.height > H:
        raise ValueError(f"och at {(x, y)} does not fit on the {W}x{H} screen")
    if not allow_overlap:
        under = img.crop((x, y, x + layer.width, y + layer.height)).getchannel("A").tobytes()
        ink = layer.getchannel("A").tobytes()
        hits = [(x + i % layer.width, y + i // layer.width)
                for i, (a, u) in enumerate(zip(ink, under)) if a and u]
        if hits:
            raise ValueError(f"och at {(x, y)} would overlap {len(hits)} non-transparent pixel(s), "
                             f"first {hits[0]}; erase_and first, or pass allow_overlap=True")
    img.alpha_composite(layer, (x, y))
    return x, y


# -------------------------------------------------------------------------------------- PNG write
def _chunk(typ: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + typ + body + struct.pack(">I", zlib.crc32(typ + body))


def png_rgba_bytes(im: Image.Image) -> bytes:
    """Deterministic RGBA8 PNG: IHDR, one IDAT (filter 0, zlib level 9), IEND. No other chunks."""
    if im.mode != "RGBA":
        raise ValueError(f"expected RGBA, got {im.mode}")
    w, h = im.size
    raw = im.tobytes()
    data = b"".join(b"\x00" + raw[y * w * 4:(y + 1) * w * 4] for y in range(h))
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(data, 9)) + _chunk(b"IEND", b""))


def layer_png_bytes() -> bytes:
    return png_rgba_bytes(och_layer())


# ---------------------------------------------------------------------------------------- preview
def _on_black(im: Image.Image, pad: int = 2) -> Image.Image:
    bg = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 255))
    bg.alpha_composite(im, (pad, pad))
    return bg.convert("RGB")


def _shipped(lang: str, name: str, box=None) -> Image.Image:
    im = _open_rgba(RES / lang / "intro" / f"{name}.png")
    if box is None:
        return im
    x0, y0, x1, y1 = box
    return im.crop((x0, y0, x1 + 1, y1 + 1))


def _sheet(tiles: list[tuple[str, Image.Image]], scale: int, base_row: list[int]) -> Image.Image:
    """Tiles side by side, scaled, bottom-aligned on a common baseline (base_row = baseline row
    inside each tile), labelled."""
    asc = max(b for b in base_row)
    desc = max(t.height - b for (_, t), b in zip(tiles, base_row))
    gap, lab = 6 * scale, 14
    width = sum(t.width * scale for _, t in tiles) + gap * (len(tiles) + 1)
    height = (asc + desc) * scale + lab + 2 * gap
    sheet = Image.new("RGB", (width, height), (48, 48, 48))
    d = ImageDraw.Draw(sheet)
    x = gap
    for (label, t), b in zip(tiles, base_row):
        y = lab + gap + (asc - b) * scale
        sheet.paste(t.resize((t.width * scale, t.height * scale), Image.NEAREST), (x, y))
        d.text((x, 2), label, fill=(255, 255, 0))
        x += t.width * scale + gap
    return sheet


def write_previews(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    layer = och_layer()
    met = och_metrics()
    png = layer_png_bytes()
    (out / "och_layer.png").write_bytes(png)
    pad = 2
    tiles = [
        ("sv:och", _on_black(layer, pad), met["baseline_row"] + pad),
        ("en:and", _on_black(_shipped("en", "manuydani", AND_BOX["manuydani"]), pad), 157 - 143 + pad),
        ("es:y", _on_black(_shipped("es", "manuydani", (74, 149, 83, 164)), pad), 157 - 149 + pad),
        ("it:e", _on_black(_shipped("it", "manuydani", (76, 144, 83, 154)), pad), 153 - 144 + pad),
        ("fr:et", _on_black(_shipped("fr", "manuydani", (58, 151, 74, 164)), pad), 163 - 151 + pad),
    ]
    for s in (6, 4):
        _sheet([(l, t) for l, t, _ in tiles], s, [b for _, _, b in tiles]).save(out / f"och_{s}x.png")
    # in-context mock-ups: the en screens, shipped and with the "and" replaced by "och" through
    # the same erase_and + place_och the builders use
    ctx = []
    for name, view in (("manuydani", (20, 100, 250, 166)), ("pacoyjuan", (20, 120, 220, 182)),
                       ("pelicula", (20, 70, 300, 165))):
        shipped = _shipped("en", name)
        im = shipped.copy()
        erase_and(im, name)
        place_och(im, name)
        for screen in (shipped, im):
            scr = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            scr.alpha_composite(screen)
            ctx.append(scr.crop(view).convert("RGB"))
    s = 4
    wmax = max(c.width for c in ctx) * s
    sheet = Image.new("RGB", (wmax, sum(c.height * s + 4 for c in ctx)), (48, 48, 48))
    y = 0
    for c in ctx:
        sheet.paste(c.resize((c.width * s, c.height * s), Image.NEAREST), (0, y))
        y += c.height * s + 4
    sheet.save(out / "context_4x.png")
    return {"png": png, "metrics": met}


def _hexmap(canvas: dict, box) -> list[str]:
    x0, y0, x1, y1 = box
    out = []
    for y in range(y0, y1 + 1):
        out.append("".join("." if canvas.get((x, y), 0) == 0 else HEX[canvas[(x, y)] // 17]
                           for x in range(x0, x1 + 1)))
    return out


def show() -> None:
    """Print each composed letter as a hex alpha map (alpha/17, '.' = 0) next to a map of the
    hand corrections ('#' alpha set by hand, 'x' source pixel erased, '.' source kept)."""
    word: dict[tuple[int, int], int] = {}
    for letter in LETTERS:
        pieces, _ = read_recipe(SRC_DIR / f"och_{letter}.txt")
        canvas = compose_letter(letter)[0]
        src = _source_canvas(pieces)
        ps = list(canvas) + list(src)
        box = (min(p[0] for p in ps), 143, max(p[0] for p in ps), 158)
        marks = {p: "#" for p, a in canvas.items() if src.get(p) != a}
        marks.update({p: "x" for p in src if p not in canvas})
        left = _hexmap(canvas, box)
        right = ["".join(marks.get((x, y), ".") for x in range(box[0], box[2] + 1))
                 for y in range(box[1], box[3] + 1)]
        print(f"\n{letter}: x {box[0]}..{box[2]}   composed | corrections")
        for y, l, r in zip(range(box[1], box[3] + 1), left, right):
            print(f"{y} {l}   {r}")
        for p, a in canvas.items():
            word[p] = max(word.get(p, 0), a)
    box, _ = _word()
    print(f"\nword: x {box[0]}..{box[2]}")
    for y, l in zip(range(box[1], box[3] + 1), _hexmap(word, box)):
        print(f"{y} {l}")


def _safe_out(out: Path) -> Path:
    """Inside the project, previews may only go to work/phaseD/och/ or a directory under it (never
    into assets_sv/, work/jar/, original/, tools/ or another track's work/phaseD/<dir>/). The path
    is resolved first, so a symlink cannot lead out of there. Outside the project any directory
    is accepted."""
    out = out.resolve()
    if (out == ROOT or ROOT in out.parents) and not (out == OUT_DIR or OUT_DIR in out.parents):
        sys.exit(f"refusing --out {out}: inside the project it must be {OUT_DIR}/ or lie under it")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--show", action="store_true", help="print the composed letters as hex maps")
    a = ap.parse_args()
    out = _safe_out(a.out)
    res = write_previews(out)
    png, met = res["png"], res["metrics"]
    layer = och_layer()
    print(f"och_layer.png sha256 {hashlib.sha256(png).hexdigest()}  ({len(png)} B)")
    print(f"rgba sha256 {hashlib.sha256(layer.tobytes()).hexdigest()}")
    if not a.quiet:
        print(f"metrics {met}")
        for letter in LETTERS:
            canvas, n_src, hand, erased = compose_letter(letter)
            xs = [p[0] for p in canvas]
            ys = [p[1] for p in canvas]
            print(f"  {letter}: x {min(xs)}..{max(xs)} y {min(ys)}..{max(ys)}; {n_src} source px, "
                  f"{hand} set by hand, {erased} erased")
        for name in AND_BOX:
            print(f"  och_position({name!r}) = {och_position(name)}  "
                  f"(compose {och_position(name, 'compose')}, left {och_position(name, 'left')})")
        print(f"previews in {out}")
    if a.show:
        show()
    return 0


if __name__ == "__main__":
    sys.exit(main())

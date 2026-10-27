# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0", "numpy==2.3.2", "scipy==1.16.1"]
# ///
"""Build the Swedish "press to start" image res/de/intro/pulsa.png: "Tryck för att starta".

Deterministic. Inputs (read-only; RES = res/ of original/TheAbbeyOfCrimeExtensum.jar and GLYPHS = the
glyph inventory, both made from original/ by tools/images/inputs.py):
  - RES/de/intro/pulsa.png   the shipped de file (byte-identical to en; checked) = base
  - RES/en/intro/pulsa.png   glyph source (r, o, a, t, "start")
  - RES/pl/intro/pulsa.png   glyph source (c)
  - RES/es/intro/pulsa.png   read on every build, to check the outline rules below on
                                      its line (with en and pl), and by --fit
  - assets_sv/image_src/pulsa/layout.txt   which glyph goes where (see that file)
  - assets_sv/image_src/pulsa/*.txt        hand-drawn glyphs T, y, k, f and the two dots of ö
Output:
  - assets_sv/res/de/intro/pulsa.png  (--out may redirect it, never into work/inputs/, work/jar/ or original/)

The pulsa font (images.md §3.3, FORMAT §6.2) is an anti-aliased blackletter: every opaque pixel is
the fill (253,246,231) scaled by k/15 (k = 0..15; k = 0 is the opaque black outline), every partial
pixel is black with alpha (the fringe). The en palette holds exactly that: index 36+k = k-th shade
(opaque), indices 3..35 = black at 33 alpha levels, 0..2 = transparent. So a pixel is fully
described by (k, alpha), with k > 0 only where alpha = 255.

How a glyph is turned into pixels:
  - ink (k > 0) comes from the source: the shipped image's pixels in the glyph's columns (layout.txt
    may re-shade some of them, or drop them from the glyph with shade 0), or the hand-drawn grid;
  - outline + fringe of a REUSED glyph: the shipped alpha of every non-ink pixel whose nearest ink
    pixel (Euclidean) in the shipped line belongs to this glyph ("territory"); elsewhere the model
    below, computed from this glyph's ink alone (fills the parts the old neighbour had claimed);
  - outline + fringe of a HAND-DRAWN glyph: the model: upsample k/15 bilinearly 8x, threshold at
    0.35, dilate by a disc of radius 1.8 px, alpha = 255 x the coverage of each pixel by the
    dilated shape. Radius and threshold come from a grid search on the shipped es, en and pl lines
    (mean |alpha error| over their fringe pixels); re-run it with --fit. On the shipped lines it is
    off by a mean of 6.5 (en) and 8.7 (pl) alpha levels; the builder prints this check.
  - the line = per pixel max of k and max of alpha over all glyphs (ink is drawn over outlines, and
    overlapping outlines unite); at junctions between a hand-drawn glyph and another glyph the
    model of the whole line is used where it is higher (the union of two outlines covers more than
    either).
  - four rules every shipped line (es, en, pl) obeys without exception (checked on them), enforced
    on the whole line because the model's threshold (k > 5.25) leaves faint edge pixels without an
    outline of their own: a non-ink pixel 4-adjacent to ink is opaque black (the 1 px outline is
    closed); one only diagonally adjacent to ink has alpha >= 167 (DIAG_MIN); one 2 steps from ink
    has alpha >= 18 (RING2_MIN: the fringe outside the outline). Where the last one fails, the
    pixel takes the model of the line with every ink pixel counted as at least k 6 (FAINT_AS, just
    over the threshold), i.e. faint ink gets the fringe it would have as a shape of its own. The
    fourth is only checked: no pixel with alpha > 0 lies further than sqrt(8) (two steps
    diagonally) from ink (REACH), so no stray outline or leftover of the old text survives.
  - alpha is then snapped to the nearest of the palette's 33 black levels, or to 0. The levels are
    up to 17 apart (59..76), so |error| <= 8.5.
The line is centred on x = 160 (ink columns, k >= 8, like the Phase A ink boxes).

Then: everything in the shipped text area (the base's alpha > 0 box, measured, not assumed) and the
new one is cleared to index 0 and the new line painted; a pixel that ends fully transparent and was
fully transparent in the base gets its base index back (the de file's background is index 2,
(255,255,255) at alpha 0), so the index diff against the base is exactly the visible diff;
everything else keeps its index. Checks: size, chunk list, palette and tRNS unchanged (no new shade
is needed), nothing changed outside the two text boxes, ink rows (caps from 166, x-height 171..182,
descenders to 185), the moon window (x >= 250, y < 100) empty, centring, and the four outline rules
above on the written pixels. The PNG is assembled in memory chunk by chunk (IHDR, PLTE, tRNS copied
verbatim, one IDAT of filter-0 rows at zlib level 9, IEND), decoded again and checked, and only
then written. Every check is an explicit test (SystemExit with a message), not an assert, so
python -O does not skip any.

usage: uv run tools/images/build_pulsa.py [--out PATH] [--src-dir DIR] [--quiet]
       uv run tools/images/build_pulsa.py --fit     re-run the outline model's grid search
"""
from __future__ import annotations

import argparse
import hashlib
import io
import struct
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True        # importing inputs must not write tools/images/__pycache__
sys.path.insert(0, str(ROOT / "tools/images"))
import inputs  # noqa: E402  (original/ jar res/ + glyph inventory, see tools/images/inputs.py)
SRC = {lang: inputs.RES / f"{lang}/intro/pulsa.png" for lang in ("de", "en", "es", "pl")}
SRC_DIR = ROOT / "assets_sv/image_src/pulsa"
OUT = ROOT / "assets_sv/res/de/intro/pulsa.png"
READ_ONLY = (inputs.BASE, ROOT / "work/jar", ROOT / "original")   # game data: never written

W, H = 320, 208
FILL_R = {"en": 253, "es": 253, "pl": 255}   # pl draws the same font with fill (255,246,231)
DIAG_MIN = 167                         # lowest alpha of a fringe pixel diagonal to ink (es, en, pl)
RING2_MIN = 18                         # lowest alpha 2 steps (4-distance) from ink (es, en, pl)
REACH = np.sqrt(8.0)                   # furthest any alpha > 0 pixel lies from ink (es, en, pl)
FAINT_AS = 6                           # faint ink counted as this shade for its own fringe (> 15 x 0.35)
BAND = (158, 192)                      # rows of the text line in every language (ink 164..187)
EN_TEXT_BOX = (98, 164, 221, 187)      # alpha > 0 box of "Press to start" (inclusive); measured
                                       # from the base on every build and checked against this
CHUNKS = [b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND"]
CENTRE_X = 160
INK_K = 8                              # k >= 8 (luminance >= ~128) counts as ink for boxes and gaps
OUTLINE_R, OUTLINE_T, SS = 1.8, 0.35, 8
MOON = (250, 0, 319, 99)
K_BLACK = 36                           # palette index of opaque black; 36 + k = shade k


def need(cond, msg: str) -> None:
    """An input or output check that python -O cannot strip."""
    if not cond:
        raise SystemExit(f"build_pulsa: {msg}")


# ---------------------------------------------------------------- PNG plumbing
def chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    need(data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG")
    out, i = [], 8
    while i < len(data):
        (n,) = struct.unpack(">I", data[i:i + 4])
        typ, body = data[i + 4:i + 8], data[i + 8:i + 8 + n]
        crc = struct.unpack(">I", data[i + 8 + n:i + 12 + n])[0]
        need(zlib.crc32(typ + body) == crc, f"bad CRC in {typ!r}")
        out.append((typ, body))
        i += 12 + n
    return out


def chunk(typ: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + typ + body + struct.pack(">I", zlib.crc32(typ + body))


# ---------------------------------------------------------------- sources
def k_alpha(lang: str) -> tuple[np.ndarray, np.ndarray]:
    """(k, alpha) arrays of a shipped pulsa image; checks the font's colour model."""
    a = np.asarray(Image.open(SRC[lang]).convert("RGBA")).astype(np.int32)
    alpha = a[..., 3]
    opaque = alpha == 255
    k = np.where(opaque, np.rint(a[..., 0] * 15 / FILL_R[lang]).astype(np.int32), 0)
    need(np.all(a[..., :3][(alpha > 0) & ~opaque] == 0), f"{lang}: a partial pixel is not black")
    return k, alpha


def read_grid(path: Path) -> tuple[int, np.ndarray]:
    """Glyph grid: '#' comments, 'char C', then '<image row> <cells>' rows in order.
    Cells: '.' = no ink, '1'..'9' 'A'..'F' = shade k (hex). Returns (top row, k array)."""
    y0, rows = None, []
    for raw in path.read_text(encoding="utf-8").splitlines():
        parts = raw.split("#", 1)[0].split()
        if not parts or parts[0] == "char":
            continue
        need(len(parts) == 2, f"bad line in {path}: {raw!r}")
        y = int(parts[0])
        if y0 is None:
            y0 = y
        need(y == y0 + len(rows), f"row {y} out of order in {path}")
        need(all(c == "." or c in "123456789ABCDEF" for c in parts[1]), f"bad cell in {path}: {raw!r}")
        rows.append(parts[1])
    need(rows, f"{path}: no rows")
    widths = {len(r) for r in rows}
    need(len(widths) == 1, f"ragged rows in {path}: {widths}")
    k = np.array([[0 if c == "." else int(c, 16) for c in r] for r in rows], dtype=np.int32)
    return y0, k


def model_alpha(k: np.ndarray, radius: float = OUTLINE_R, thresh: float = OUTLINE_T) -> np.ndarray:
    """Outline + fringe alpha (0..255 float) of ink k (full-image array): the fitted model."""
    out = np.zeros(k.shape, float)
    ys, xs = np.where(k > 0)
    if ys.size == 0:
        return out
    y0, y1 = max(ys.min() - 4, 0), min(ys.max() + 5, k.shape[0])
    x0, x1 = max(xs.min() - 4, 0), min(xs.max() + 5, k.shape[1])
    win = k[y0:y1, x0:x1] / 15.0
    up = ndimage.zoom(win, SS, order=1, mode="nearest", grid_mode=True)
    # dilation by a disc of radius R = every subpixel within R of the thresholded shape
    dil = ndimage.distance_transform_edt(up < thresh) <= radius * SS
    h, w = win.shape
    out[y0:y1, x0:x1] = dil.reshape(h, SS, w, SS).mean(axis=(1, 3)) * 255.0
    return out


def outline_rules(k: np.ndarray, alpha: np.ndarray) -> list[tuple[str, np.ndarray]]:
    """Pixels breaking the shipped outline rules, as (rule, mask): partial pixels 4-adjacent to
    ink, non-ink pixels only diagonally adjacent to ink with alpha < DIAG_MIN, pixels 2 steps from
    ink with alpha < RING2_MIN, and pixels with alpha > 0 further than REACH from ink."""
    ink = k > 0
    n4 = ndimage.binary_dilation(ink)
    n8 = ndimage.binary_dilation(ink, np.ones((3, 3), bool))
    ring2 = ndimage.binary_dilation(ink, iterations=2) & ~n4
    far = (alpha > 0) & (ndimage.distance_transform_edt(~ink) > REACH + 1e-6)
    return [("partial pixel 4-adjacent to ink (outline not closed)", ~ink & n4 & (alpha < 255)),
            (f"fringe pixel diagonal to ink with alpha < {DIAG_MIN}", ~ink & n8 & ~n4 & (alpha < DIAG_MIN)),
            (f"pixel 2 steps from ink with alpha < {RING2_MIN} (no fringe)", ring2 & ~n8 & (alpha < RING2_MIN)),
            ("pixel with alpha > 0 more than sqrt(8) from ink (stray outline or old text)", far)]


def fit(quiet: bool) -> int:
    """Grid search of the outline model on the shipped es, en and pl lines (provenance of
    OUTLINE_R and OUTLINE_T): mean |alpha error| over the non-ink pixels either side marks."""
    lines = {lang: k_alpha(lang) for lang in ("es", "en", "pl")}
    res = []
    for thresh in (0.2, 0.25, 0.3, 0.35, 0.4, 0.5):
        for radius in np.round(np.arange(1.4, 2.25, 0.05), 2):
            errs = []
            for k, a in lines.values():
                kb = np.zeros_like(k)
                kb[BAND[0]:BAND[1] + 1] = k[BAND[0]:BAND[1] + 1]
                m = model_alpha(kb, float(radius), thresh)
                sel = (kb == 0) & ((a > 0) | (m > 0))
                errs.append(np.abs(m[sel] - a[sel]))
            e = np.concatenate(errs)
            res.append((round(float(e.mean()), 2), float(radius), thresh, float(np.percentile(e, 90))))
    res.sort()
    for mean, radius, thresh, p90 in res[: 3 if quiet else 8]:
        print(f"radius {radius:.2f} threshold {thresh:.2f}: mean |d alpha| {mean:.2f}, p90 {p90:.0f}")
    print(f"in use: radius {OUTLINE_R} threshold {OUTLINE_T}")
    return 0


class Glyph:
    """A glyph (or block of glyphs) as full-image layers k, alpha at its source position."""

    def __init__(self, name: str, k: np.ndarray, alpha: np.ndarray, drawn: bool, mark: bool = False):
        self.name, self.k, self.alpha, self.drawn, self.mark = name, k, alpha, drawn, mark
        cols = np.where((k >= INK_K).any(axis=0))[0]
        need(cols.size, f"{name}: no ink")
        self.left, self.right = int(cols[0]), int(cols[-1])


def reused(name: str, lang: str, x0: int, x1: int, shipped: dict,
           shades: list[tuple[int, int, int]] = ()) -> Glyph:
    """Ink = shipped pixels with k > 0 in columns x0..x1 of the text band; outline as documented.
    shades: (x, y, k) re-shadings of the glyph's own ink pixels (source coordinates): k 1..15 for
    anti-aliasing that only made sense next to the source's neighbour; k 0 drops the pixel from the
    glyph (a neighbour's pixel at the column edge), so it becomes outline (its shipped alpha, 255)."""
    k_src, a_src = shipped[lang]
    if shades:
        k_src = k_src.copy()
        for x, y, kk in shades:
            need(x0 <= x <= x1 and BAND[0] <= y <= BAND[1], f"{name}: shade ({x},{y}) outside the glyph")
            need(k_src[y, x] > 0 and 0 <= kk <= 15, f"{name}: shade ({x},{y}) must re-shade ink to 0..15")
            k_src[y, x] = kk
    band = np.zeros((H, W), bool)
    band[BAND[0]:BAND[1] + 1, :] = True
    ink_all = (k_src > 0) & band
    own = ink_all.copy()
    own[:, :x0] = False
    own[:, x1 + 1:] = False
    other = ink_all & ~own
    k = np.where(own, k_src, 0)
    # territory: non-ink pixels nearer (or as near) to own ink than to any other ink of the line
    d_own = ndimage.distance_transform_edt(~own)
    d_other = ndimage.distance_transform_edt(~other) if other.any() else np.full((H, W), 1e9)
    territory = band & ~own & (d_own <= d_other) & (d_own <= 4.0)
    alpha = np.where(own, 255.0, 0.0)
    alpha = np.where(territory, a_src.astype(float), alpha)
    model = model_alpha(k)
    alpha = np.where(band & ~own & ~territory, np.maximum(alpha, model), alpha)
    return Glyph(name, k, alpha, False)


def drawn(name: str, path: Path) -> Glyph:
    y0, g = read_grid(path)
    h, w = g.shape
    need(BAND[0] <= y0 - 3 and y0 + h + 3 <= BAND[1] + 1, f"{path}: rows outside the band")
    k = np.zeros((H, W), np.int32)
    k[y0:y0 + h, 8:8 + w] = g                     # parked at x 8; the layout moves it
    alpha = np.where(k > 0, 255.0, model_alpha(k))
    return Glyph(name, k, alpha, True)


def shift(g: Glyph, dx: int) -> Glyph:
    """The glyph moved dx columns. No wrap-around: every pixel with ink or alpha > 0 must stay
    inside the image, or the build stops."""
    k, alpha = np.zeros_like(g.k), np.zeros_like(g.alpha)
    if dx >= 0:
        k[:, dx:], alpha[:, dx:] = g.k[:, :W - dx], g.alpha[:, :W - dx]
    else:
        k[:, :W + dx], alpha[:, :W + dx] = g.k[:, -dx:], g.alpha[:, -dx:]
    need(np.count_nonzero(k) == np.count_nonzero(g.k)
         and np.count_nonzero(alpha > 0) == np.count_nonzero(g.alpha > 0), f"{g.name}: shifted off the image")
    return Glyph(g.name, k, alpha, g.drawn, g.mark)


# ---------------------------------------------------------------- layout
def read_layout(src_dir: Path, shipped: dict) -> list[tuple[Glyph, int]]:
    """layout.txt lines (after '#' comments):
         <name> en|pl <x0> <x1> gap <n> [shade <x>,<y>=<k> ...]
                                             reuse shipped ink columns x0..x1, optionally re-shading
                                             some of its ink pixels (source coordinates, hex k;
                                             k 0 drops the pixel from the glyph)
         <name> grid <file> gap <n>          hand-drawn grid
         <name> grid <file> on <dx>          mark: its ink-left at the previous glyph's ink-left + dx
       gap = empty ink columns between the previous glyph's ink-right and this one's ink-left
       (ink-left = previous ink-right + 1 + gap; a negative gap overlaps the boxes; the first
       glyph's gap is ignored). Returns each glyph at its source position with the column offset
       that lays it out; the first glyph's offset is 0, and build() centres the whole line and
       moves every glyph once, so nothing is moved off the image on the way."""
    placed: list[tuple[Glyph, int]] = []
    pen_right = prev_left = None
    for raw in (src_dir / "layout.txt").read_text(encoding="utf-8").splitlines():
        parts = raw.split("#", 1)[0].split()
        if not parts:
            continue
        need(len(parts) >= 5, f"layout: short line {raw!r}")
        name, kind = parts[0], parts[1]
        if kind in ("en", "pl"):
            need(len(parts) >= 6, f"layout: short line {raw!r}")
            shades = []
            if len(parts) > 6:
                need(parts[6] == "shade" and len(parts) > 7, f"layout: bad tail in {raw!r}")
                for tok in parts[7:]:
                    xy, kk = tok.split("=")
                    x, y = map(int, xy.split(","))
                    shades.append((x, y, int(kk, 16)))
            g = reused(name, kind, int(parts[2]), int(parts[3]), shipped, shades)
            mode, n = parts[4], int(parts[5])
        elif kind == "grid":
            g = drawn(name, src_dir / parts[2])
            mode, n = parts[3], int(parts[4])
        else:
            raise SystemExit(f"layout: unknown source {kind!r} in {raw!r}")
        if mode == "on":
            need(prev_left is not None, "layout: a mark needs a glyph before it")
            dx = prev_left + n - g.left
            g.mark = True
        else:
            need(mode == "gap", f"layout: expected 'gap' or 'on' in {raw!r}")
            dx = 0 if pen_right is None else pen_right + 1 + n - g.left
            pen_right, prev_left = g.right + dx, g.left + dx
        placed.append((g, dx))
    need(placed, "layout: no glyphs")
    return placed


# ---------------------------------------------------------------- build
def build(out_path: Path, src_dir: Path, quiet: bool) -> int:
    de_bytes = SRC["de"].read_bytes()
    need(de_bytes == SRC["en"].read_bytes(), "the original res/de/intro/pulsa.png must equal en")
    src_chunks = chunks(de_bytes)
    need([t for t, _ in src_chunks] == CHUNKS, f"base chunks {[t for t, _ in src_chunks]}, expected {CHUNKS}")
    ihdr, plte, trns = src_chunks[0][1], src_chunks[1][1], src_chunks[2][1]
    need(struct.unpack(">IIBBBBB", ihdr) == (W, H, 8, 3, 0, 0, 0), "base: expected 320x208 8-bit indexed")
    pal = [tuple(plte[i:i + 3]) for i in range(0, len(plte), 3)]
    tr = list(trns) + [255] * (len(pal) - len(trns))
    need(len(pal) == 52 and len(trns) == 36, f"base: {len(pal)} PLTE / {len(trns)} tRNS entries, expected 52 / 36")
    for kk in range(16):                          # the shade ramp the font uses
        need(tr[K_BLACK + kk] == 255 and pal[K_BLACK + kk][0] == round(253 * kk / 15),
             f"base: palette index {K_BLACK + kk} is not shade {kk}")
    black_levels = sorted((tr[i], i) for i in range(3, 36))
    need(all(pal[i] == (0, 0, 0) for _, i in black_levels), "base: indices 3..35 are not all black")
    lut_a = np.array(tr, np.int32)
    lut_k = np.array([round(p[0] * 15 / 253) if t == 255 else 0 for p, t in zip(pal, tr)], np.int32)

    idx_src = np.asarray(Image.open(SRC["de"]))
    need(idx_src.shape == (H, W), "base: decoded size")
    ys, xs = np.where(lut_a[idx_src] > 0)          # the old text: everything visible in the base
    en_box = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    need(en_box == EN_TEXT_BOX, f"base: alpha > 0 box {en_box}, expected {EN_TEXT_BOX} (\"Press to start\")")

    shipped = {lang: k_alpha(lang) for lang in ("en", "pl")}
    for lang, (k_s, a_s) in {**shipped, "es": k_alpha("es")}.items():   # the rules are the font's
        for what, bad in outline_rules(k_s, a_s):
            need(not bad.any(), f"shipped {lang} breaks an outline rule: {what}")
    placed = read_layout(src_dir, shipped)

    # centre the ink on x = 160, then move every glyph once to its place
    left = min(g.left + d for g, d in placed)
    right = max(g.right + d for g, d in placed)
    dx = int(np.floor(CENTRE_X - (left + right) / 2 + 0.5))
    glyphs = [shift(g, d + dx) for g, d in placed]
    left, right = left + dx, right + dx
    need((left, right) == (min(g.left for g in glyphs), max(g.right for g in glyphs)), "layout: ink box moved")

    K = np.max([g.k for g in glyphs], axis=0)
    A = np.max([g.alpha for g in glyphs], axis=0)
    # Where a hand-drawn glyph's outline meets another glyph's, the two outlines unite: there the
    # max of two separate coverages is lower than the coverage of their union (a see-through
    # pixel in the black), so such junction pixels take the model of the whole line if higher.
    # Junctions between two reused glyphs keep the shipped pixels.
    near_new = np.max([g.alpha if g.drawn else np.zeros((H, W)) for g in glyphs], axis=0) > 0
    n_layers = np.sum([g.alpha > 0 for g in glyphs], axis=0)
    junction = near_new & (n_layers >= 2)
    A = np.where(junction, np.maximum(A, model_alpha(K)), A)
    A = np.where(K > 0, 255.0, A)
    # the shipped outline rules (see the docstring): 4-neighbours of ink opaque, diagonals >= 167,
    # and a fringe outside the outline of faint ink too: a pixel 2 steps from ink that is still
    # (almost) transparent, alpha < RING2_MIN, takes the model of the line with every ink pixel
    # counted as k >= FAINT_AS
    ink = K > 0
    A = np.where(~ink & ndimage.binary_dilation(ink), 255.0, A)
    A = np.where(~ink & ndimage.binary_dilation(ink, np.ones((3, 3), bool)), np.maximum(A, DIAG_MIN), A)
    hole = (A < RING2_MIN) & ndimage.binary_dilation(ink, iterations=2)
    if hole.any():
        A = np.where(hole, np.maximum(model_alpha(np.where(ink, np.maximum(K, FAINT_AS), 0)), RING2_MIN), A)

    new = idx_src.copy()
    ys, xs = np.where(A >= 0.5)
    new_box = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    clear = np.zeros((H, W), bool)
    for (x0, y0, x1, y1) in (en_box, new_box):
        clear[y0:y1 + 1, x0:x1 + 1] = True
    new[clear] = 0
    levels = np.array([0] + [lv for lv, _ in black_levels] + [255], dtype=float)
    lv_index = [0] + [i for _, i in black_levels] + [K_BLACK]
    snap_err = 0.0
    for y, x in zip(*np.where((A >= 0.5) | (K > 0))):
        if K[y, x] > 0:
            new[y, x] = K_BLACK + int(K[y, x])
        else:
            j = int(np.argmin(np.abs(levels - A[y, x])))
            new[y, x] = lv_index[j]
            snap_err = max(snap_err, abs(levels[j] - A[y, x]))
    # a pixel left fully transparent that was fully transparent in the base keeps its base index
    keep = (lut_a[new] == 0) & (lut_a[idx_src] == 0)
    new[keep] = idx_src[keep]

    # ---- checks
    errors = []
    if new.max() >= len(pal):
        errors.append("an index outside the palette")
    if np.any(new[~clear] != idx_src[~clear]):
        errors.append("pixels changed outside the two text boxes")
    if snap_err > 8.5:
        errors.append(f"alpha snapped by {snap_err:.1f} > 8.5")
    ink_rows = np.where((K >= INK_K).any(axis=1))[0]
    if ink_rows.min() < 166 or ink_rows.max() > 185:
        errors.append(f"ink rows {ink_rows.min()}..{ink_rows.max()}, allowed 166..185")
    x0, y0, x1, y1 = MOON
    if np.any(A[y0:y1 + 1, x0:x1 + 1] >= 0.5) or np.any(new[y0:y1 + 1, x0:x1 + 1] != idx_src[y0:y1 + 1, x0:x1 + 1]):
        errors.append("ink or fringe inside the moon window (x >= 250, y < 100)")
    if abs((left + right) / 2 - CENTRE_X) > 1:
        errors.append(f"ink centre {(left + right) / 2}, want {CENTRE_X}")
    # the outline rules, on the pixels as written (palette index -> k, alpha); the last one also
    # proves that nothing of "Press to start" survived (its pixels are all > sqrt(8) from new ink
    # unless the new line covers them)
    for what, bad in outline_rules(lut_k[new], lut_a[new]):
        if bad.any():
            errors.append(f"{int(bad.sum())} x {what}: " + ", ".join(
                f"({x},{y})" for y, x in np.argwhere(bad)[:8]))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2

    # ---- assemble in memory, decode and check, then write
    raw = b"".join(b"\x00" + bytes(new[y].astype(np.uint8).tolist()) for y in range(H))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"PLTE", plte) + chunk(b"tRNS", trns)
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    out_chunks = chunks(png)
    need([t for t, _ in out_chunks] == CHUNKS, f"output chunks {[t for t, _ in out_chunks]}")
    need(out_chunks[1][1] == plte and out_chunks[2][1] == trns, "output palette or tRNS changed")
    with Image.open(io.BytesIO(png)) as im:
        need(im.mode == "P" and im.size == (W, H), f"output decodes as {im.mode} {im.size}")
        need(np.array_equal(np.asarray(im), new), "output PNG does not decode to the intended indices")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(png)

    if not quiet:
        print(f"wrote {out_path} ({len(png)} B, sha256 {hashlib.sha256(png).hexdigest()})")
        print(f"  ink x {left}..{right} (centre {(left + right) / 2}), rows {ink_rows.min()}..{ink_rows.max()};"
              f" alpha box {new_box}; old text box {en_box}; max alpha snap {snap_err:.1f}")
        prev = None
        for g in glyphs:
            rows = np.where((g.k >= INK_K).any(axis=1))[0]
            where = ("mark" if g.mark else "" if prev is None else f"gap {g.left - prev.right - 1}")
            src = "drawn" if g.drawn else "shipped"
            print(f"  {g.name:6s} {src:7s} ink x {g.left}..{g.right} rows {rows.min()}..{rows.max()} {where}")
            if not g.mark:
                prev = g
        for lang in ("en", "pl"):                 # how well the outline model fits the shipped lines
            k_s, a_s = shipped[lang]
            m = model_alpha(k_s)
            sel = (k_s == 0) & ((a_s > 0) | (m > 0))
            err = np.abs(m[sel] - a_s[sel])
            print(f"  outline model vs shipped {lang}: mean |d alpha| {err.mean():.1f}, p90 {np.percentile(err, 90):.0f}")
        changed = np.sum(new != idx_src)
        rgba = np.array([list(p) + [t] for p, t in zip(pal, tr)], np.int32)
        visible = np.sum(np.any(rgba[new] != rgba[idx_src], axis=-1))
        print(f"  {changed} pixels differ from de/en ({visible} in RGBA), all inside {en_box} + {new_box};"
              " palette and tRNS unchanged")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--src-dir", type=Path, default=SRC_DIR)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--fit", action="store_true", help="re-run the outline model's grid search and exit")
    a = ap.parse_args()
    if a.fit:
        return fit(a.quiet)
    out = a.out.resolve()
    for d in READ_ONLY:
        if out.is_relative_to(d.resolve()):
            raise SystemExit(f"refusing to write into {d}: extracted game data is read-only")
    return build(out, a.src_dir, a.quiet)


if __name__ == "__main__":
    sys.exit(main())

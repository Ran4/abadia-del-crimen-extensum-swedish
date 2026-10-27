# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Build the Swedish credit screen res/de/intro/pelicula.png ("och" / "Jean-Jacques Annauds" /
"film med samma namn"; GLOSSARY §8, images.md §2.7, FORMAT §6).

Deterministic: no randomness, integer/float arithmetic in a fixed order, a hand-written PNG
encoder (IHDR, one IDAT, IEND). Run it twice and the output is byte-identical. The pixels are a
function of the inputs alone; the file bytes also depend on the zlib that deflates the IDAT (the
kit's save_rgba_png, level 9), i.e. on the interpreter uv picks. So the builder prints two hashes:
"sha256" of the file (compare runs of one interpreter) and "pixels sha256" of the decoded RGBA
bytes (compare across interpreters), with the Python and zlib versions used.

Inputs (read-only data, never executed or changed; RES = res/ of the original jar, made from
original/ by tools/images/inputs.py):
  RES/de/intro/pelicula.png  the base (= en byte for byte, checked): "and" (script, own
                                      line) / "in Jean-Jacques Annaud’s" / "film of the same name"
  RES/en/intro/pelicula.png  the Phase A letter inventory is keyed on it (de == en)
  tools/images/fraktur.py             the Fraktur kit: coverage-space canvas, the shipped letters
                                      as coverage, the font's s and its spacing, the glow model
  tools/images/script_och.py          och_layer() and its placement on the en "and"'s baseline
  (both imported with bytecode writing off, so no __pycache__ appears next to them)
Output: assets_sv/res/de/intro/pelicula.png (8-bit RGBA, like the de file)

The layout is en's (the conjunction on its own line, then two Fraktur lines on baselines 126 and
156) with Swedish words:
  line 1  "och"   script_och.och_layer() where en has "and" (alpha box [26,78,59,93]), on the
                  "and"'s baseline (row 92), placed "compose": its strong left edge on the a's
                  (x 27). The "and" is removed by script_och.erase_and (cream ink -> alpha 0).
  line 2  "Jean-Jacques Annauds"  the shipped en pixels of "Jean-Jacques Annaud" (letter-exact,
                  Phase A ownership, with the slanted double hyphen), moved left as one block by
                  whole pixels (half-pixel phases kept) so the J starts at x LINE2_LEFT, the
                  left edge of line 3 ("film", x 36); then the font's s after the kept d
                  (fraktur.line_after: the kit's s glyph at the font's d->s advance). "in" and
                  "’s" are erased with the rest of the old line; the glow of the whole line is
                  regenerated from the new cores.
  line 3  "film med samma namn"   the shipped "film" is kept (same word, same place: its fully
                  covered pixels keep their bytes, its anti-aliased edge only gets the regenerated
                  glow of the moved J above it); "of the same name" is erased (whole components)
                  and " med samma namn" is typeset with the kit after the kept m (line_after: the
                  font's word space, its letters and kerning).

Checks on the result (check_result), each over every pixel of the image:
  - every changed pixel lies within the glow radius (fraktur.GLOW_R = 6 px, Chebyshev) of a pixel
    whose coverage the builder changed (the canvas edits, the erased "and", the placed "och");
  - image-only cross-check, independent of the builder's state: every changed pixel lies within
    GLOW_REACH - 1 = 7 px of ink (decomposed coverage > 0) in the base or in the result;
  - coarse: every changed pixel lies in the conjunction box or a line box padded by the glow;
  - the kept "film": core pixels unchanged, edge pixels changed by at most FILM_EDGE_TOL levels;
  - no ink or glow in the moon window (x >= 250, y < 100);
  - the conjunction line holds the och's pixels and nothing else;
and on the file: exactly IHDR/IDAT/IEND, 320x208 8-bit RGBA, no interlace, filter-0 rows, and the
PNG decodes back to the same pixels.

usage: uv run tools/images/build_pelicula.py [--out PATH] [--quiet]
         [--src en|it] [--left N] [--och-align compose|left|right] [--och-dx N]
  --out PATH   write there instead: a .png; inside the project only the real output or a path
               under work/phaseD/ (any track's scratch) is allowed (assets_sv/, tools/,
               work/inputs/, original/ and the rest are refused); outside it, anywhere
  --src/--left/--och-align/--och-dx  scratch experiments only (need --out): the source of the
               "Jean-Jacques Annaud" pixels, the left ink column of line 2, the och placement
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import struct
import sys
import tempfile
import warnings
import zlib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True        # importing inputs must not write tools/images/__pycache__
sys.path.insert(0, str(ROOT / "tools/images"))
import inputs  # noqa: E402  (original/ jar res/ + glyph inventory, see tools/images/inputs.py)
RES = inputs.RES
OUT = ROOT / "assets_sv/res/de/intro/pelicula.png"
PHASE_D = ROOT / "work/phaseD"                # scratch builds may go anywhere under it

sys.dont_write_bytecode = True        # importing the kit must not write tools/images/__pycache__
sys.path.insert(0, str(ROOT / "tools/images"))
import fraktur as fk  # noqa: E402
import script_och  # noqa: E402
from script_och import erase_and, och_layer, place_och  # noqa: E402

W, H = 320, 208
PNG_SIG = b"\x89PNG\r\n\x1a\n"
L2_EN = "in Jean-Jacques Annaud’s"    # Phase A line texts (fraktur.occurrences)
L3_EN = "film of the same name"
L2_IT = "Jean-Jacques Annaud"
NAME = "Jean-Jacques Annaud"
BASE_2 = 126                          # en baseline of line 2 (line 3: 156, kept)
LINE2_LEFT = 36                       # left ink column of the J (= "film" on line 3)
L2_ERASE = (20, 100, 300, 132)        # the whole old line 2 (rows 105..130 + AA)
L3_ERASE = (78, 131, 300, 166)        # "of the same name" ("film" ends at x 72)
FILM_LAST = 72                        # last ink column of the kept "film"
FILM_EDGE_TOL = 32                    # max change of a "film" edge pixel (glow under it; seen: 24)
CONJ_AREA = (0, 70, 319, 96)          # the conjunction line: only the och may have alpha here
GLOW_REACH = 8                        # shipped glow fades out 7-8 px from the ink
INK_REACH = GLOW_REACH - 1            # image-only check: changes within 7 px of old/new ink
AND_BOX = (26, 78, 59, 93)            # the en "and" (alpha > 0), = script_och.AND_BOX["pelicula"]
# coarse check: every changed pixel must lie in one of these: the conjunction, or an erase box
# plus the glow reach (the exact checks are the coverage-distance ones in check_result)
CHANGE_BOXES = (AND_BOX,
                (L2_ERASE[0] - GLOW_REACH, L2_ERASE[1] - GLOW_REACH,
                 L2_ERASE[2] + GLOW_REACH, L2_ERASE[3] + GLOW_REACH),
                (L3_ERASE[0] - GLOW_REACH, L3_ERASE[1] - GLOW_REACH,
                 L3_ERASE[2] + GLOW_REACH, L3_ERASE[3] + GLOW_REACH))
DEFAULTS = {"src": "en", "left": LINE2_LEFT, "och_align": "compose", "och_dx": 0}


def need(cond: object, msg: str) -> None:
    """A check that survives python -O (unlike assert)."""
    if not cond:
        raise SystemExit(f"build_pelicula: {msg}")


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
        need(zlib.crc32(typ + body) & 0xFFFFFFFF == crc, f"bad CRC in {typ!r}")
        out.append((typ, body))
        i += 12 + n
    return out


def check_inputs() -> None:
    en_b = (RES / "en/intro/pelicula.png").read_bytes()
    de_b = (RES / "de/intro/pelicula.png").read_bytes()
    need(de_b == en_b, "de pelicula.png is no longer en byte for byte")
    need(script_och.AND_BOX["pelicula"] == AND_BOX, "script_och.AND_BOX['pelicula'] changed")
    typ, body = chunks(de_b)[0]
    need(typ == b"IHDR" and len(body) == 13, "de pelicula.png does not start with IHDR")
    w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
    need((w, h, depth, ctype, interlace) == (W, H, 8, 6, 0),
         f"de pelicula.png is not 8-bit RGBA 320x208: {(w, h, depth, ctype, interlace)}")


def inside(box, x: int, y: int) -> bool:
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def build_image(opt: dict, notes: list[str]) -> Image.Image:
    cv = fk.Canvas.shipped("de", "pelicula")        # the en/de image with its script box

    # line 2: "Jean-Jacques Annaud" as shipped pixels, moved; then the font's s.
    if opt["src"] == "en":
        name = fk.letters("en", "pelicula", L2_EN, NAME)
        dy = 0
    else:
        name = fk.letters("it", "pelicula", L2_IT, NAME)
        dy = BASE_2 - name.glyphs[0]["baseline"]
    need([g["char"] for g in name.glyphs] == [c for c in NAME if c != " "],
         f"line 2 block is {[g['char'] for g in name.glyphs]}")
    dx = opt["left"] - name.glyphs[0]["ink_left"]
    d_id = name.glyphs[-1]["source"]
    with warnings.catch_warnings():
        warnings.simplefilter("error", fk.FrakturSpacingWarning)
        s_lay = fk.line_after(d_id, "s", dx, dy)
    cv.erase(L2_ERASE)                               # 'in Jean-Jacques Annaud’s' + its glow
    cv.draw(name.moved(dx, dy))
    cv.draw(s_lay)
    g_s = s_lay.glyphs[0]
    gap = g_s["ink_left"] - (name.glyphs[-1]["ink_right"] + dx) - 1
    need(1 <= gap <= 3, f"d -> s ink gap {gap} px (the font's letter gaps are 1-3)")
    notes.append(f"line 2: {opt['src']} '{NAME}' moved ({dx:+d},{dy:+d}): J ink from x "
                 f"{name.glyphs[0]['ink_left'] + dx}, d ink ..{name.glyphs[-1]['ink_right'] + dx}; "
                 f"s at x {g_s['x']} phase {g_s['phase']} (ink {g_s['ink_left']}..{g_s['ink_right']})")

    # line 3: keep the shipped "film", typeset " med samma namn" after its m.
    film = fk.letters("en", "pelicula", L3_EN, "film")
    need(film.glyphs[-1]["ink_right"] == FILM_LAST, "en 'film' moved?")
    m_id = film.glyphs[-1]["source"]
    with warnings.catch_warnings():
        warnings.simplefilter("error", fk.FrakturSpacingWarning)
        rest = fk.line_after(m_id, " med samma namn")
    gap = rest.glyphs[0]["ink_left"] - FILM_LAST - 1
    need(10 <= gap <= 12, f"'film' -> 'med' ink gap {gap} px (the font's word gaps are 10-12)")
    need(rest.glyphs[-1]["ink_right"] < W - 8, "line 3 runs too far right")
    cv.erase(L3_ERASE)                               # 'of the same name' + its glow
    cv.draw(rest)
    notes.append(f"line 3: 'film' kept; ' med samma namn' at x {rest.glyphs[0]['ink_left']}.."
                 f"{rest.glyphs[-1]['ink_right']}: "
                 + " ".join(f"{g['char']}{g['x']}/{g['phase']}" for g in rest.glyphs))

    img = cv.render()
    # the coverage this build changes: the canvas edits (Fraktur and script) ...
    cov = {i for i in range(W * H) if cv.c[i] != cv.c0[i] or cv.s[i] != cv.s0[i]}

    # line 1: the script "and" -> "och" (the och track's own code; no glow involved).
    x0, y0, x1, y1 = AND_BOX
    base_px = cv.base_img.load()
    cov |= {y * W + x for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if base_px[x, y][3]}
    n = erase_and(img, "pelicula")
    pos = place_och(img, "pelicula", align=opt["och_align"], dx=opt["och_dx"])
    lay = och_layer()
    la = lay.getchannel("A").load()
    # ... plus the erased "and" and the placed "och"
    cov |= {(pos[1] + j) * W + pos[0] + i for j in range(lay.height) for i in range(lay.width) if la[i, j]}
    notes.append(f"line 1: 'and' removed ({n} px); 'och' at {pos} ({lay.width}x{lay.height})")
    return img, cov


def dilate(mask: list[bool], r: int) -> list[bool]:
    """Chebyshev dilation of a W x H mask by r px (separable running sums, exact)."""
    rows = [False] * (W * H)
    for y in range(H):
        pre = [0] * (W + 1)
        for x in range(W):
            pre[x + 1] = pre[x] + mask[y * W + x]
        for x in range(W):
            rows[y * W + x] = pre[min(W, x + r + 1)] > pre[max(0, x - r)]
    out = [False] * (W * H)
    for x in range(W):
        pre = [0] * (H + 1)
        for y in range(H):
            pre[y + 1] = pre[y] + rows[y * W + x]
        for y in range(H):
            out[y * W + x] = pre[min(H, y + r + 1)] > pre[max(0, y - r)]
    return out


def _stray_msg(what: str, stray: list[int]) -> str:
    pts = [(i % W, i // W) for i in stray]
    coarse = sum(1 for c in pts if not any(inside(b, *c) for b in CHANGE_BOXES))
    return (f"{len(pts)} px changed {what}, bbox {fk.bbox_of(pts)}, first {pts[:5]}; "
            f"{coarse} of them also outside the line boxes {CHANGE_BOXES}")


def check_result(img: Image.Image, cov: set[int]) -> None:
    need(img.mode == "RGBA" and img.size == (W, H), f"result is {img.mode} {img.size}")
    base = Image.open(RES / "de/intro/pelicula.png").convert("RGBA")
    p, q = img.load(), base.load()
    new_px, old_px = list(img.getdata()), list(base.getdata())
    changed = [i for i in range(W * H) if new_px[i] != old_px[i]]
    # the claim: every pixel farther than the glow radius from changed coverage keeps its bytes
    near_cov = dilate([i in cov for i in range(W * H)], fk.GLOW_R)
    far = [i for i in changed if not near_cov[i]]
    need(not far, _stray_msg(f"farther than {fk.GLOW_R} px from changed coverage", far))
    # the same from the two images alone: changes only within INK_REACH of old or new ink
    ink = [fk.decompose_px(*a)[0] > 0 or fk.decompose_px(*b)[0] > 0 for a, b in zip(old_px, new_px)]
    near_ink = dilate(ink, INK_REACH)
    far = [i for i in changed if not near_ink[i]]
    need(not far, _stray_msg(f"farther than {INK_REACH} px from ink of the base or the result", far))
    # coarse: changes only in the conjunction or the two line boxes padded by the glow reach
    far = [i for i in changed if not any(inside(b, i % W, i // W) for b in CHANGE_BOXES)]
    need(not far, _stray_msg("outside the line boxes", far))
    # the kept "film": its fully covered pixels keep the base's bytes; its anti-aliased edge may
    # change only through the regenerated glow under it (line 2's J now hangs above the f and l)
    film = fk.letters("en", "pelicula", L3_EN, "film")
    core = [(x, y) for x, y, v in film.pixels() if v == 255 and p[x, y] != q[x, y]]
    need(not core, f"the kept 'film' changed at core pixels {core[:5]}")
    edge = [(x, y) for x, y, v in film.pixels()
            if max(abs(p[x, y][i] - q[x, y][i]) for i in range(4)) > FILM_EDGE_TOL]
    need(not edge, f"the kept 'film' edge changed by more than {FILM_EDGE_TOL} levels at {edge[:5]}")
    moon = fk.moon_pixels(img)
    need(not moon, f"{len(moon)} px of ink or glow in the moon window, bbox {fk.bbox_of(moon)}")
    # the conjunction line holds only the och (cream, 16 alpha levels, no glow)
    x0, y0, x1, y1 = CONJ_AREA
    lay = och_layer()
    bad = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
           if p[x, y][3] and (p[x, y][:3] != (253, 246, 231) or p[x, y][3] % 17)]
    need(not bad, f"non-och pixels on the conjunction line: {bad[:5]}")
    n_och = sum(1 for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if p[x, y][3])
    n_lay = sum(1 for a in lay.getchannel("A").getdata() if a)
    need(n_och == n_lay, f"conjunction line holds {n_och} px, the och layer {n_lay}")


def encode_checked(img: Image.Image) -> bytes:
    png = fk.save_rgba_png(img, None)
    cs = chunks(png)
    need([t for t, _ in cs] == [b"IHDR", b"IDAT", b"IEND"],
         f"chunk list is {[t for t, _ in cs]}, expected IHDR, IDAT, IEND")
    need(struct.unpack(">IIBBBBB", cs[0][1]) == (W, H, 8, 6, 0, 0, 0),
         "IHDR is not 320x208 8-bit RGBA, no interlace")
    raw = zlib.decompress(cs[1][1])
    stride = 1 + 4 * W
    need(len(raw) == H * stride and {raw[y * stride] for y in range(H)} == {0},
         "IDAT is not 208 filter-0 rows")
    with Image.open(io.BytesIO(png)) as back:
        need(back.mode == "RGBA" and back.size == (W, H), f"decodes as {back.mode} {back.size}")
        need(back.tobytes() == img.tobytes(), "PNG round trip changed pixels")
    return png


def write_atomic(out_path: Path, data: bytes) -> None:
    """Write through a hidden temporary '.<name>.<random>.part' in the target directory, then
    os.replace it over the target (atomic on one file system). A hard kill can leave only such a
    dot-file ending in .part, which no glob for *.png (or *.tmp) picks up. The file gets mode
    0666 & ~umask, as a plain open() would give (NamedTemporaryFile creates it 0600)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    umask = os.umask(0)
    os.umask(umask)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=out_path.parent, prefix=f".{out_path.name}.",
                                         suffix=".part", delete=False) as f:
            tmp = Path(f.name)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o666 & ~umask)
        os.replace(tmp, out_path)
    except BaseException:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
        raise


def safe_out(out: Path) -> Path:
    """--out must name a .png. Inside the project it must be the real output or lie under
    work/phaseD/ (this track's or any other track's scratch); assets_sv/, tools/, work/inputs/,
    original/ and everything else in the project are refused. Outside the project, anywhere.
    Symlinks are resolved first, so a link under work/phaseD/ cannot point the write elsewhere."""
    out = out.resolve()
    if out.suffix.lower() != ".png" or out.is_dir():
        sys.exit(f"refusing --out {out}: it must name a .png file")
    if out != OUT and (out == ROOT or ROOT in out.parents) and PHASE_D not in out.parents:
        sys.exit(f"refusing --out {out}: inside the project it must be {OUT} or under {PHASE_D}/")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--src", choices=("en", "it"), default=DEFAULTS["src"])
    ap.add_argument("--left", type=int, default=DEFAULTS["left"])
    ap.add_argument("--och-align", choices=("compose", "left", "right"), default=DEFAULTS["och_align"])
    ap.add_argument("--och-dx", type=int, default=DEFAULTS["och_dx"])
    a = ap.parse_args()
    out = safe_out(a.out)
    opt = {"src": a.src, "left": a.left, "och_align": a.och_align, "och_dx": a.och_dx}
    if opt != DEFAULTS and out == OUT:
        sys.exit("--src/--left/--och-* are for scratch experiments: pass a scratch --out "
                 "(under work/phaseD/ or outside the project)")
    check_inputs()
    notes: list[str] = []
    img, cov = build_image(opt, notes)
    check_result(img, cov)
    png = encode_checked(img)
    if out.is_file():
        # same pixels, other bytes: the zlib differs from the one that wrote the file (not an error)
        old = out.read_bytes()
        if old != png:
            try:
                with Image.open(io.BytesIO(old)) as prev:
                    same = prev.mode == "RGBA" and prev.tobytes() == img.tobytes()
            except Exception:
                same = False
            if same:
                print(f"note: {out.name} had these pixels in other bytes; zlib "
                      f"{zlib.ZLIB_RUNTIME_VERSION} deflates differently from the build that wrote it",
                      file=sys.stderr)
    write_atomic(out, png)
    if not a.quiet:
        for n in notes:
            print(n)
        print(f"wrote {out} ({len(png)} B)\n"
              f"  sha256        {hashlib.sha256(png).hexdigest()}  (file; zlib-dependent)\n"
              f"  pixels sha256 {hashlib.sha256(img.tobytes()).hexdigest()}  (decoded RGBA)\n"
              f"  python {sys.version.split()[0]} ({sys.executable}), zlib {zlib.ZLIB_RUNTIME_VERSION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

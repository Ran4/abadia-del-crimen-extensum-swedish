# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Regression: the Swedish build must not change a single pixel of any other language.

  uv run tools/regress.py [--game DIR | --jar PATCHED.jar] [--langs es,en,it,fr,pl] [--out DIR] [--java JAVA]

Defaults: --game game/, --out work/regress/. For every language it renders all strings,
pause-menu states, save/load lists, end screens, HUD hours and both parchments (tools/harness, the
game's own drawing code, headless) from the PRISTINE jar (original/) and from the PATCHED jar, and
asserts that every raw frame is pixel-identical and that the harness reports the same errors.
Then it checks the jar itself:
  * same entries in the same order; abadia/{m,l,o,n,p}.class (the other languages' text) and every
    entry outside abadia/{k,j,w,E}.class, res/fuente.png, res/letras, res/de/** byte-identical;
  * res/fuente.png: PLTE/tRNS bytes identical, cells 0..79 identical except originally blank cells;
  * res/letras: bytes 0..5563 identical except the 6 Swedish slot pointers (originally 0x0000),
    every original glyph decodes identically;
  * glyph coverage (code points the glyph routine draws): nothing lost; additions only Å å ä ö, '}' (the
    ring) and the codes of newly filled font cells (e.g. 'w' = cell 74, the HUD Ö), all forbidden by the lint.
Exit 0 = no difference, 1 = a difference (listed).

Concurrency: like render_strings.py it renders from a private snapshot of the patched jar, uses the
content-addressed harness build (never deleted, so tools/build.py or another render cannot pull it
away mid-run) and locks its --out dir; its default --out is outside work/build/, which build.py wipes.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import sys
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import letras as L  # noqa: E402
import pngio  # noqa: E402
from render_strings import build_harness, jar_snapshot, out_lock, run_harness  # noqa: E402

ORIG_JAR = ROOT / "original" / "TheAbbeyOfCrimeExtensum.jar"
ALLOWED_CHANGE = re.compile(r"^(abadia/[kjwE]\.class|res/fuente\.png|res/letras|res/de/.+)$")
OTHER_LANG_CLASSES = ["abadia/m.class", "abadia/l.class", "abadia/o.class", "abadia/n.class", "abadia/p.class"]
EXPECTED_NEW_GLYPHS = {0x7D, 0xC5, 0xE4, 0xE5, 0xF6}   # } Å ä å ö (FORMAT §3.4 side effects)


def coverage(path: pathlib.Path) -> set[int]:
    out = set()
    for ln in path.read_text(encoding="utf-8").split("\n"):
        if ln.startswith("U+"):
            out.add(int(ln[2:6], 16))
    return out


def font_extra_codes(pristine: pathlib.Path, patched: pathlib.Path) -> set[int]:
    """Char codes that reach a fuente.png cell the patch filled (blank cells 2/46/72..79, appended cells
    beyond the ring): j.a(int) draws them through its default path, so they gain ink. All of them are
    lowercase/symbols the lint forbids (e.g. 'w' = cell 74, the HUD Ö)."""
    with zipfile.ZipFile(pristine) as zo, zipfile.ZipFile(patched) as zn:
        _, _, ro = pngio.decode_indexed8(zo.read("res/fuente.png"))
        wn, _, rn = pngio.decode_indexed8(zn.read("res/fuente.png"))
    out = set()
    for c in range(wn // 8):
        new_ink = any(rn[y][c * 8 + x] != 53 for y in range(8) for x in range(8))
        old_ink = c < 80 and any(ro[y][c * 8 + x] != 53 for y in range(8) for x in range(8))
        if new_ink and not old_ink and c != 80:
            out.add(45 + c)
    return out


def compare_lang(lang: str, pristine: pathlib.Path, patched: pathlib.Path, base: pathlib.Path, java: str,
                 hb: pathlib.Path) -> tuple[list[str], int]:
    from PIL import Image
    probs = []
    po, pa = base / "pristine" / lang, base / "patched" / lang
    c1 = run_harness(pristine, lang, po, None, java, hb)
    c2 = run_harness(patched, lang, pa, None, java, hb)
    if c1 != c2:
        probs.append(f"{lang}: harness exit {c1} (pristine) vs {c2} (patched)")
    try:
        l1 = json.loads((po / "layout.json").read_text(encoding="utf-8"))
        l2 = json.loads((pa / "layout.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as ex:
        return probs + [f"{lang}: no layout.json ({ex})"], 0
    if l1["errors"] != l2["errors"]:
        probs.append(f"{lang}: harness errors differ: {sorted(set(l1['errors']) ^ set(l2['errors']))[:5]}")
    for key in ("messages", "endgame", "menu", "hours", "parchment"):
        if l1.get(key) != l2.get(key):
            probs.append(f"{lang}: layout.json section {key!r} differs")
    r1 = sorted(p.name for p in (po / "raw").glob("*.png"))
    r2 = sorted(p.name for p in (pa / "raw").glob("*.png"))
    if r1 != r2:
        probs.append(f"{lang}: raw frame sets differ: {sorted(set(r1) ^ set(r2))[:10]}")
    n = 0
    for name in sorted(set(r1) & set(r2)):
        a = Image.open(po / "raw" / name).convert("RGBA")
        b = Image.open(pa / "raw" / name).convert("RGBA")
        n += 1
        if a.size != b.size or a.tobytes() != b.tobytes():
            probs.append(f"{lang}: frame {name} differs")
    cov1, cov2 = coverage(po / "coverage.txt"), coverage(pa / "coverage.txt")
    lost, added = cov1 - cov2, cov2 - cov1
    if lost:
        probs.append(f"{lang}: glyph coverage lost {sorted(hex(c) for c in lost)}")
    expected = EXPECTED_NEW_GLYPHS | font_extra_codes(pristine, patched)
    if added - expected:
        probs.append(f"{lang}: unexpected new glyphs {sorted(hex(c) for c in added - expected)}")
    print(f"    {lang}: {n} frames compared, harness exit {c1}/{c2}, errors {len(l1['errors'])}/{len(l2['errors'])}, "
          f"new glyphs {' '.join(chr(c) for c in sorted(added))}" + ("  OK" if not probs else "  DIFF"))
    return probs, n


def check_jar(pristine: pathlib.Path, patched: pathlib.Path) -> list[str]:
    probs = []
    with zipfile.ZipFile(pristine) as zo, zipfile.ZipFile(patched) as zn:
        no, nn = [i.filename for i in zo.infolist()], [i.filename for i in zn.infolist()]
        if no != nn:
            probs.append(f"jar entry list/order differs: {sorted(set(no) ^ set(nn))[:10]}")
        changed, same = [], 0
        for name in no:
            if name not in nn:
                continue
            a, b = zo.read(name), zn.read(name)
            if a == b:
                same += 1
                continue
            changed.append(name)
            if not ALLOWED_CHANGE.match(name):
                probs.append(f"jar entry {name} changed (not allowed)")
        for c in OTHER_LANG_CLASSES:
            if zo.read(c) != zn.read(c):
                probs.append(f"{c} (another language's text) changed")
        print(f"    jar: {len(no)} entries, {same} byte-identical, changed: {', '.join(changed)}")
        print(f"    {', '.join(c.split('/')[1] for c in OTHER_LANG_CLASSES)}: byte-identical" if not any(
            zo.read(c) != zn.read(c) for c in OTHER_LANG_CLASSES) else "    other-language classes CHANGED")
        # fuente.png
        fo, fn = zo.read("res/fuente.png"), zn.read("res/fuente.png")
        for t in (b"PLTE", b"tRNS"):
            if pngio.chunk_body(fo, t) != pngio.chunk_body(fn, t):
                probs.append(f"fuente.png {t.decode()} differs")
        _, _, ro = pngio.decode_indexed8(fo)
        wn, hn, rn = pngio.decode_indexed8(fn)
        if hn != 8 or wn < 640:
            probs.append(f"fuente.png is {wn}x{hn}")
        else:
            refilled = []
            for c in range(80):
                a = [ro[y][c * 8:c * 8 + 8] for y in range(8)]
                b = [rn[y][c * 8:c * 8 + 8] for y in range(8)]
                if a != b:
                    if all(v == 53 for r in a for v in r):
                        refilled.append(c)
                    else:
                        probs.append(f"fuente.png cell {c} changed (it was not blank)")
            print(f"    fuente.png: {wn}x8, PLTE/tRNS identical, cells 0..79 identical except blank cells filled: {refilled}")
        # letras
        lo, ln = zo.read("res/letras"), zn.read("res/letras")
        slot_bytes = {(s - 44) * 2 + k for s in L.SLOT_CHARS for k in (0, 1)}
        diff = [k for k in range(len(lo)) if k >= len(ln) or lo[k] != ln[k]]
        bad = [k for k in diff if k not in slot_bytes]
        if bad:
            probs.append(f"letras bytes changed outside the slot pointers: {bad[:10]}")
        if any(lo[k] for k in diff):
            probs.append("letras: a changed slot pointer was not 0x0000 in the original")
        go, gn = L.Letras(lo), L.Letras(ln)
        for code, g in go.glyphs.items():
            h = gn.glyphs.get(code)
            if h is None or h["pixels"] != g["pixels"] or h["adv"] != g["adv"]:
                probs.append(f"letras glyph {code} changed")
        print(f"    letras: {len(lo)} -> {len(ln)} B, original bytes identical except {len(diff)} slot-pointer bytes; "
              f"{len(go.glyphs)} original glyphs identical; new slots "
              + " ".join(L.SLOT_CHARS[c] for c in sorted(set(gn.glyphs) - set(go.glyphs))))
    return probs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", type=pathlib.Path, default=ROOT / "game")
    ap.add_argument("--jar", type=pathlib.Path, default=None)
    ap.add_argument("--pristine", type=pathlib.Path, default=ORIG_JAR)
    ap.add_argument("--langs", default="es,en,it,fr,pl")
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "work" / "regress")
    ap.add_argument("--java", default="java")
    a = ap.parse_args()
    patched = (a.jar or a.game / "TheAbbeyOfCrimeExtensum.jar").resolve()
    if not patched.is_file():
        raise SystemExit(f"no jar at {patched}")
    out = a.out.resolve()
    with out_lock(out, "regress"), jar_snapshot(patched) as snap:
        sys.exit(regress(a, patched, snap, out))


def regress(a, patched: pathlib.Path, snap: pathlib.Path, out: pathlib.Path) -> int:
    if out.exists():
        if not (out / "pristine").exists() and any(out.iterdir()):
            raise SystemExit(f"refusing to wipe {out}")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    hb = build_harness()
    problems = []
    print(f"[1] render every string/menu/HUD/parchment frame: pristine {a.pristine} vs patched {patched} "
          f"(private snapshot; harness {hb})")
    total = 0
    for lang in a.langs.split(","):
        p, n = compare_lang(lang, a.pristine.resolve(), snap, out, a.java, hb)
        problems += p
        total += n
    print("[2] jar entries, fuente.png, letras")
    problems += check_jar(a.pristine.resolve(), snap)
    for p in problems:
        print(f"    DIFF {p}")
    print(f"\nregress: {total} frames in {len(a.langs.split(','))} languages; "
          + ("RESULT: OK (pixel-identical, no unexpected jar change)" if not problems else f"RESULT: FAIL ({len(problems)})"))
    print(f"output: {out}")
    return 1 if problems else 0


if __name__ == "__main__":
    main()

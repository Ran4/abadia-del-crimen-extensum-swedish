# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Render every Swedish string of the BUILT game with the game's own drawing code (headless
harness, tools/harness/) into contact sheets, and fail on any missing glyph or layout error.

  uv run tools/render_strings.py [--game DIR | --jar JAR] [--lang de] [--ref-lang es] [--out DIR]
                                 [--strings TSV] [--perg1 TXT] [--perg2 TXT] [--placeholder]
                                 [--no-lint] [--no-source-check] [--java JAVA]

Defaults: --game game/, --lang de, --ref-lang es, --out screenshots/strings/<lang>/,
--strings translation/strings_sv.tsv, --perg1/--perg2 translation/pergamino{1,2}_sv.txt.
Output sheets (3x): messages_NN.png (every g page, as the
dialogue box), menu.png (3 pause-menu states + 2 save/load slot lists), endgame.png, hours.png (HUD
hour strip), glyphs.png, parchment_intro.png / parchment_ending.png (every page of pergamino1/2
through the real abadia.y, 6 pages per sheet; only a text of more than 6 pages is split into
parchment_intro_01.png, _02 ...); raw/ 1x frames; report.txt; layout.json; harness.log; SUMMARY.txt.

Checks (exit 1 if any fails): harness exit 0 (no missing glyph, crash, no-progress layout,
--ref-lang size/@N mismatch); for --lang de the string lint (tools/lint_strings.py; --no-lint skips
it) and the source check (--no-source-check skips it): every rendered string and hour equals the sv
column of --strings, so does the never-drawn window title E.h[4] (and w.t[4], w.u[4]) read from the
jar's class files with tools/classfile.py, and the jar's res/de/pergamino1|2 equal --perg1/--perg2
encoded exactly as the build encodes them, so a source edited after the build is reported; every parchment page of the
jar's res/<lang>/pergamino1|2 is pixel-identical between the real game code and the tools/letras.py
emulator (so the build's width check measures what the game draws), and for de every parchment
line's ink edge is <= 244 and no page is blank. --lang es|en|it|fr|pl renders other languages from
the patched jar for regression (tools/regress.py compares them against the pristine jar).

Concurrency: the jar is copied to a private snapshot first (a build replacing game/ mid-run cannot
mix two jars), the harness classes come from a content-addressed dir that is never deleted
(tools/harness/build.sh, work/harness_build/), and a lock per output dir refuses a second run
writing to the same --out. report.txt names the jar as given (relative to the project root), not
the snapshot's random work/.tmp/jar-*/ path, so the tracked report changes only when the render does.
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import classfile  # noqa: E402
import letras as L  # noqa: E402
import lint_strings  # noqa: E402

LANGS = ["es", "en", "it", "fr", "de", "pl"]


def build_harness() -> pathlib.Path:
    """Build (or reuse) the harness; returns its content-addressed, never-deleted build dir."""
    res = subprocess.run([str(HERE / "harness" / "build.sh")], capture_output=True, text=True)
    lines = res.stdout.strip().split("\n")
    if res.returncode != 0 or not lines[-1] or not pathlib.Path(lines[-1]).is_dir():
        print(res.stdout + res.stderr)
        raise SystemExit("harness build failed")
    return pathlib.Path(lines[-1])


def run_harness(jar: pathlib.Path, lang: str, out: pathlib.Path, ref_lang: str | None, java: str,
                hb: pathlib.Path) -> int:
    cmd = [str(HERE / "harness" / "render.sh"), "--jar", str(jar), "--lang", lang, "--out", str(out)]
    if ref_lang:
        cmd += ["--ref-lang", ref_lang]
    env = dict(os.environ)
    env["JAVA"] = java
    env["HARNESS_BUILD"] = str(hb)
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)
    out.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    (out / "harness.log").write_text(res.stdout + res.stderr, encoding="utf-8")
    return res.returncode


@contextlib.contextmanager
def out_lock(out: pathlib.Path, tool: str):
    """Exclusive, non-blocking lock per output dir (work/.locks/), so two runs never wipe each other."""
    locks = ROOT / "work" / ".locks"
    locks.mkdir(parents=True, exist_ok=True)
    f = open(locks / (hashlib.sha256(str(out.resolve()).encode()).hexdigest()[:16] + ".lock"), "a+")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        f.seek(0)
        holder = f.read().strip()
        f.close()
        raise SystemExit(f"{tool}: another render_strings.py/regress.py run is writing to {out} ({holder})")
    try:
        f.seek(0)
        f.truncate()
        f.write(f"{tool} pid {os.getpid()} -> {out}\n")
        f.flush()
        yield
    finally:
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()


@contextlib.contextmanager
def jar_snapshot(jar: pathlib.Path):
    """A private copy of the jar for the whole run (tools/build.py may replace game/ meanwhile)."""
    tmp_root = ROOT / "work" / ".tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="jar-", dir=tmp_root))
    try:
        snap = tmp / jar.name
        shutil.copyfile(jar, snap)
        yield snap
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def safe_reset(out: pathlib.Path):
    out = out.resolve()
    if out.exists():
        ok = (out / "report.txt").exists() or (out / "layout.json").exists() or not any(out.iterdir())
        if not ok:
            raise SystemExit(f"refusing to wipe {out}: it does not look like a render output dir")
        shutil.rmtree(out)
    out.mkdir(parents=True)


def parchment_crosscheck(jar: pathlib.Path, lang: str, out: pathlib.Path, strict_width: bool) -> list[str]:
    """Emulator (tools/letras.py) vs the real abadia.y frames written by the harness."""
    from PIL import Image
    problems = []
    with zipfile.ZipFile(jar) as zf:
        lt = L.Letras(zf.read("res/letras"))
        perg = zf.read("res/pergamino.png")
        texts = {"intro": zf.read(f"res/{lang}/pergamino1"), "ending": zf.read(f"res/{lang}/pergamino2")}
    for name, data in texts.items():
        chk = L.check_bytes(data, lt, f"{lang}/{name}")
        for e in chk["errors"]:
            (problems.append if strict_width else print)(("" if strict_width else "note: ") + e)
        try:
            emu = L.render_pages(data, lt, perg)
        except L.GameHang as ex:
            problems.append(f"parchment {name}: emulator: {ex}")
            continue
        real = sorted((out / "raw").glob(f"parch_{name}_p*.png"))
        if len(real) != len(emu):
            problems.append(f"parchment {name}: game produced {len(real)} pages, emulator {len(emu)}")
            continue
        for k, (r, e) in enumerate(zip(real, emu), 1):
            ri = Image.open(r).convert("RGB")
            if ri.tobytes() != e.tobytes():
                diff = sum(1 for a, b in zip(ri.getdata(), e.getdata()) if a != b)
                problems.append(f"parchment {name} page {k}: emulator differs from the game in {diff} pixels")
        print(f"    parchment {name}: {len(emu)} pages, emulator == game (pixel-identical); widest ink x={chk['max_ink']}")
    return problems


def parchment_source_check(jar: pathlib.Path, sources: dict) -> list[str]:
    """The jar's res/de/pergamino1|2 must equal the translation files encoded exactly as the build does."""
    probs = []
    with zipfile.ZipFile(jar) as zf:
        for entry, path in sources.items():
            data, errors, _ = L.load_text_file(path)
            if errors:
                probs.append(f"{path}: {len(errors)} error(s), e.g. {errors[0]}")
            elif data != zf.read(f"res/de/{entry}"):
                probs.append(f"res/de/{entry}: the jar's bytes differ from {path} (edited after the build?)")
    return probs


def stale_check(layout: dict, tsv: pathlib.Path) -> list[str]:
    """The strings the harness rendered (read from the jar's classes) must equal the TSV's sv column."""
    try:
        sv = {(r["array"], r["index"]): r["sv"] for r in lint_strings.read_tsv(tsv)}
    except (OSError, ValueError) as ex:
        return [f"cannot read {tsv}: {ex}"]
    probs = []
    seen = 0
    for sec in ("messages", "endgame", "menu"):
        for ent in layout.get(sec, []):
            arr = ent.get("array", "")
            key = ("w.t" if arr.startswith("w.t") else "w.u" if arr.startswith("w.u") else arr, str(ent.get("index")))
            if key in sv:
                seen += 1
                if ent.get("raw") != sv[key]:
                    probs.append(f"{key[0]}[{key[1]}]: jar has {ent.get('raw')!r}, TSV has {sv[key]!r}")
    for ent in layout.get("hours", []):
        want = "".join(chr(b) for b in lint_strings.hud_bytes(sv.get(("b", str(ent["index"])), "")))
        seen += 1
        if ent.get("bytes") != want:
            probs.append(f"b[{ent['index']}]: jar has {ent.get('bytes')!r}, TSV maps to {want!r}")
    if seen < 190:
        probs.append(f"only {seen} rendered strings matched TSV keys")
    return probs


def class_source_check(jar: pathlib.Path, tsv: pathlib.Path) -> list[str]:
    """Strings outside k that are read statically from the jar's class files (tools/classfile.py, the
    same rule as ClassDiff clinit-strings): E.h[4], the window title, which no frame shows, and
    w.t[4]/w.u[4] (also rendered in the save slots)."""
    try:
        sv = {(r["array"], r["index"]): r["sv"] for r in lint_strings.read_tsv(tsv)}
    except (OSError, ValueError) as ex:
        return [f"cannot read {tsv}: {ex}"]
    probs = []
    with zipfile.ZipFile(jar) as zf:
        for cls, field in (("E", "h"), ("w", "t"), ("w", "u")):
            key = (f"{cls}.{field}", "4")
            try:
                got = classfile.array_value(zf.read(f"abadia/{cls}.class"), field, 4)
            except (KeyError, classfile.ClassFormatError, IndexError) as ex:
                probs.append(f"{key[0]}[4]: cannot read abadia/{cls}.class: {ex}")
                continue
            if key not in sv:
                probs.append(f"{key[0]}[4]: no row in {tsv}")
            elif got != sv[key]:
                probs.append(f"{key[0]}[4]: jar has {got!r}, TSV has {sv[key]!r}")
    return probs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", type=pathlib.Path, default=ROOT / "game")
    ap.add_argument("--jar", type=pathlib.Path, default=None)
    ap.add_argument("--lang", default="de", choices=LANGS)
    ap.add_argument("--ref-lang", default=None)
    ap.add_argument("--out", type=pathlib.Path, default=None)
    ap.add_argument("--strings", type=pathlib.Path, default=ROOT / "translation" / "strings_sv.tsv")
    ap.add_argument("--perg1", type=pathlib.Path, default=ROOT / "translation" / "pergamino1_sv.txt")
    ap.add_argument("--perg2", type=pathlib.Path, default=ROOT / "translation" / "pergamino2_sv.txt")
    ap.add_argument("--placeholder", action="store_true", help="lint: untranslated strings are warnings")
    ap.add_argument("--no-lint", action="store_true", help="skip the string lint")
    ap.add_argument("--no-source-check", action="store_true",
                    help="skip comparing the jar with --strings/--perg1/--perg2")
    ap.add_argument("--java", default="java")
    a = ap.parse_args()
    jar = (a.jar or a.game / "TheAbbeyOfCrimeExtensum.jar").resolve()
    if not jar.is_file():
        raise SystemExit(f"no jar at {jar} (build first: uv run tools/build.py)")
    out = (a.out or ROOT / "screenshots" / "strings" / a.lang).resolve()
    with out_lock(out, "render_strings"), jar_snapshot(jar) as snap:
        sys.exit(render(a, jar, snap, out))


def render(a, jar: pathlib.Path, snap: pathlib.Path, out: pathlib.Path) -> int:
    ref = a.ref_lang if a.ref_lang is not None else ("es" if a.lang != "es" else "en")
    failures: list[str] = []

    print(f"[1] harness build")
    hb = build_harness()
    print(f"    {hb}")
    if a.lang == "de" and not a.no_lint:
        print(f"[2] lint {a.strings}")
        try:
            errors, warnings = lint_strings.lint(lint_strings.read_tsv(a.strings), lint_strings.read_ref(), a.placeholder)
        except (OSError, ValueError) as ex:
            errors, warnings = [f"cannot read {a.strings}: {ex}"], []
        print(f"    {len(errors)} error(s), {len(warnings)} warning(s)")
        for e in errors[:20]:
            print(f"    ERROR {e}")
        if errors:
            failures.append(f"lint: {len(errors)} error(s)")
    print(f"[3] render --lang {a.lang} --ref-lang {ref} from {jar} (private snapshot)")
    safe_reset(out)
    code = run_harness(snap, a.lang, out, ref, a.java, hb)
    report = out / "report.txt"
    if report.exists():
        shown = jar.relative_to(ROOT) if jar.is_relative_to(ROOT) else jar
        report.write_text(report.read_text(encoding="utf-8").replace(str(snap), str(shown)), encoding="utf-8")
    try:
        layout = json.loads((out / "layout.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        layout = {"errors": ["no layout.json (harness crashed?)"], "warnings": []}
    missing = [e for e in layout["errors"] if "MISSING GLYPH" in e]
    print(f"    harness exit {code}: {len(layout['errors'])} error(s) ({len(missing)} missing glyphs), "
          f"{len(layout['warnings'])} warning(s); log {out / 'harness.log'}")
    for e in layout["errors"][:30]:
        print(f"    ERROR {e}")
    if code != 0:
        failures.append(f"harness exit {code} ({len(layout['errors'])} errors)")
    if a.lang == "de" and not a.no_source_check:
        stale = stale_check(layout, a.strings) if "messages" in layout else []
        stale += class_source_check(snap, a.strings)
        for p in stale[:10]:
            print(f"    ERROR {p}")
        if stale:
            failures.append(f"the jar does not match {a.strings} ({len(stale)} differences): rebuild")
        else:
            print(f"    every rendered string/hour" + (" " if "messages" in layout else " (no layout.json!) ")
                  + f"and the window title E.h[4] (read from E.class) equal the sv column of {a.strings}")
        pstale = parchment_source_check(snap, {"pergamino1": a.perg1, "pergamino2": a.perg2})
        for p in pstale:
            print(f"    ERROR {p}")
        if pstale:
            failures.append(f"the jar's parchments do not match {a.perg1.name}/{a.perg2.name}: rebuild")
        else:
            print(f"    res/de/pergamino1|2 equal {a.perg1} and {a.perg2} as the build encodes them")
    print("[4] parchment: real game code vs tools/letras.py emulator")
    if (out / "raw").is_dir():
        probs = parchment_crosscheck(snap, a.lang, out, strict_width=(a.lang == "de"))
        for p in probs:
            print(f"    ERROR {p}")
        failures += probs
    sheets = sorted(p.name for p in out.glob("*.png"))
    summary = [f"render_strings lang={a.lang} ref={ref} jar={jar}",
               f"harness exit {code}; errors {len(layout['errors'])}; warnings {len(layout['warnings'])}",
               f"sheets ({len(sheets)}): " + " ".join(sheets),
               "RESULT: " + ("OK" if not failures else "FAIL: " + "; ".join(failures))]
    (out / "SUMMARY.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n" + "\n".join(summary))
    print(f"output: {out}")
    return 1 if failures else 0


if __name__ == "__main__":
    main()

# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Build the Swedish game (language slot 'de') from original/ + translation/ + assets_sv/.

  uv run tools/build.py [options]          (cwd = project root; writes game/ and work/build/)

Inputs (defaults):
  --strings PATH      translation/strings_sv.tsv
  --perg1 PATH        translation/pergamino1_sv.txt     (intro parchment)
  --perg2 PATH        translation/pergamino2_sv.txt     (ending parchment)
  --assets DIR        assets_sv   (images in DIR/res/de/**, glyph additions in DIR/glyphs/)
  --fuente-add PATH   DIR/glyphs/fuente_add.json
  --letras-add PATH   DIR/glyphs/letras_add.json
  --out DIR           game/      (wiped and recreated; an existing savedata.bin is kept)
  (not an option) manual/Användarmanual.pdf, if it exists, is copied as is into the game dir as
                      "User's manual (Swedish).pdf" (DECISIONS D15; made by tools/manual/build_manual.py)
  --placeholder       Spanish placeholder text allowed: untranslated-text lint errors become warnings
  --allow-missing-assets   a missing Swedish image falls back to the original res/de file (WARNING)
  --no-image-rebuild  use the images already in assets_sv/res/de/ instead of rebuilding them

Steps (docs/FORMAT.md is the reference): 1 check the original jar, wipe work/build/; 11 lint the
strings first; 2 compile tools/java/*.java; 3 generate + compile abadia/k.java and prove its shape
with javap; 4 patch j.class (Å), w.class (w.t[4], w.u[4]), E.class (E.h[4]); 5 res/fuente.png;
6 res/letras; 7 res/de/pergamino1|2; 8a rebuild the Swedish images with tools/images/build_*.py
(only for the default --assets; they are derived files and not kept in git) from original/ alone:
tools/images/inputs.py extracts res/**.png from the original jar and regenerates the glyph inventory
into work/inputs/<key>/ (key = hash of the jar and the scripts; nothing under work/jar/ or
work/phaseA/ is read); 8 images; 9 the jar; verify classes on JDK 11 and 8;
10 game/; 12 work/build/manifest.json. Deterministic: two runs with the same inputs give identical
bytes (compare the manifests). Exit 0 = built, 1 = failed (nothing is written to --out then).
--out is checked before anything is touched. work/build/ belongs to this script alone (one build at
a time, work/.build.lock): the render harness lives in work/harness_build/ and regress output in
work/regress/, so a build never disturbs a running render_strings.py or regress.py.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import letras as L  # noqa: E402
import lint_strings  # noqa: E402
import pngio  # noqa: E402

ORIG = ROOT / "original"
ORIG_JAR = ORIG / "TheAbbeyOfCrimeExtensum.jar"
ORIG_JAR_SHA = "1bc6b3fcbaf6116bd0e4a92b96193be54e72686a00c1208ba909b7bd961a36f0"
WORK = ROOT / "work" / "build"
LOCK = ROOT / "work" / ".build.lock"
JAVA_SRC = HERE / "java"
ASM = [HERE / f"asm-{n}9.7.1.jar" for n in ("", "tree-", "analysis-", "util-")]
JAVA11, JAVAC, JAVAP = "java", "javac", "javap"
JAVA8 = "/usr/lib/jvm/java-8-openjdk-amd64/bin/java"
VERIFY_FLAGS = ["-Xverify:all", "-XX:-FailOverToOldVerifier", "-Djava.awt.headless=true"]
J_MD5 = "f197f5a3e4b9d1c553ede4194efc75af"   # FORMAT §3.4 / DECISIONS D5
JAR_NAME = "TheAbbeyOfCrimeExtensum.jar"

PRISTINE_PREFIX = {   # FORMAT §0 fingerprints (sha256 prefix, size)
    "abadia/j.class": ("79729f57317f67d1", 12022), "abadia/k.class": ("57df78b2654f5bd9", 35553),
    "abadia/w.class": ("ef7f3a737765b88a", 6384), "abadia/E.class": ("5d8fecda65d038ce", 15649),
    "res/fuente.png": ("f10a02e03cd0ed9e", 2448), "res/letras": ("047ebed09a422ebf", 5564),
}
W_OLD = {"t": "DÍA ", "u": "VACÍO"}
E_OLD = "Die Abtei Des Crime Extensum"

FONT_TRANSPARENT = 53
FONT_ORIG_CELLS = 80
RING_CELL = 80               # code 125, drawn by the patched j at y-2 (PatchJ args 125 -2 1)
MAX_ADD_CELL = 82            # code 127: the last cell no shipped string of any language reaches
BLANK_CELLS_DOC = {2, 46, 72, 73, 74, 75, 76, 77, 78, 79}   # FORMAT §3.3

SV_IMAGES = {"marcador.png": (320, 32)} | {f"intro/{n}.png": (320, 208) for n in
                                           ("loading", "manuydani", "pacoyjuan", "novela", "pelicula", "pulsa")}
KEEP_INTRO = ("luna", "monje", "niebla", "ventana")
# FORMAT §6.3/§6.4 placement rules, checked on the decoded pixels (WARNINGs: the image track owns them)
ONE_BIT_ALPHA = ("intro/loading.png",)                       # strictly 1-bit alpha
MOON_IMAGES = ("intro/manuydani.png", "intro/pacoyjuan.png", "intro/novela.png", "intro/pelicula.png",
               "intro/pulsa.png")                            # drawn while the moon window (250,0,70,100) is up
PULSA_BAND = (8, 160, 311, 191)    # x0,y0,x1,y1 inclusive; the shipped pulsa text of all 6 languages: x 74..246, y 164..187
SAVEDATA = "savedata.bin"
MANUAL_PDF = ROOT / "manual" / "Användarmanual.pdf"     # tools/manual/build_manual.py (D15)
MANUAL_NAME = "User's manual (Swedish).pdf"            # named like the original manuals


class BuildError(Exception):
    pass


class Log:
    def __init__(self):
        self.warnings: list[str] = []

    def step(self, n, text):
        print(f"\n[{n}] {text}", flush=True)

    def info(self, text):
        print(f"    {text}", flush=True)

    def warn(self, text):
        self.warnings.append(text)
        print(f"    WARNING: {text}", flush=True)


log = Log()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(p) -> str:
    p = pathlib.Path(p).resolve()
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def java_env() -> dict:
    env = dict(os.environ)
    for k in ("DISPLAY", "WAYLAND_DISPLAY", "JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS", "CLASSPATH"):
        env.pop(k, None)
    env["LC_ALL"] = "C.UTF-8"
    return env


def run(cmd: list, what: str, expect_fail: bool = False) -> str:
    res = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, env=java_env(), cwd=str(WORK))
    out = (res.stdout + res.stderr).strip()
    if expect_fail:
        if res.returncode == 0:
            raise BuildError(f"{what}: expected a failure, but it succeeded:\n{out}")
        return out
    if res.returncode != 0:
        raise BuildError(f"{what} failed (exit {res.returncode}):\n{out}")
    return out


def cp(*parts) -> str:
    return ":".join(str(p) for p in parts)


def load_json_strict(path: pathlib.Path):
    """json.loads that refuses duplicate keys in any object (json keeps the last one silently)."""
    def pairs(items):
        seen = {}
        for k, v in items:
            if k in seen:
                raise BuildError(f"{rel(path)}: duplicate key {k!r} in one object (the last one would win silently)")
            seen[k] = v
        return seen
    if not path.is_file():
        raise BuildError(f"missing {path}")
    try:
        return json.loads(path.read_bytes().decode("utf-8"), object_pairs_hook=pairs)
    except (ValueError, UnicodeDecodeError) as ex:
        raise BuildError(f"{rel(path)}: {ex}")


# ====================================================================================== steps
def step1_original() -> zipfile.ZipFile:
    log.step(1, "original jar")
    if not ORIG_JAR.is_file():
        raise BuildError(f"missing {ORIG_JAR}")
    digest = sha256(ORIG_JAR.read_bytes())
    if digest != ORIG_JAR_SHA:
        log.warn(f"original jar sha256 {digest} != expected {ORIG_JAR_SHA} (FORMAT §0)")
    else:
        log.info(f"{rel(ORIG_JAR)} sha256 OK")
    zf = zipfile.ZipFile(ORIG_JAR)
    for name, (prefix, size) in PRISTINE_PREFIX.items():
        data = zf.read(name)
        if not sha256(data).startswith(prefix) or len(data) != size:
            log.warn(f"original {name} does not match its FORMAT §0 fingerprint")
    if WORK.resolve() != (ROOT / "work" / "build").resolve():
        raise BuildError("refusing: unexpected work dir")
    if WORK.exists():
        shutil.rmtree(WORK)
    for sub in ("tools", "src/abadia", "classes/abadia", "orig/abadia", "res/de/intro", "javap", "verify", "neg/abadia"):
        (WORK / sub).mkdir(parents=True, exist_ok=True)
    log.info(f"work dir {rel(WORK)} recreated")
    return zf


def step_lint(args) -> list[dict]:
    log.step(11, f"lint {rel(args.strings)}" + (" (placeholder mode)" if args.placeholder else ""))
    try:
        rows = lint_strings.read_tsv(args.strings)
        ref = lint_strings.read_ref()
    except (OSError, ValueError) as ex:
        raise BuildError(f"cannot read the strings: {ex}")
    errors, warnings = lint_strings.lint(rows, ref, args.placeholder)
    report = [f"WARNING {w}" for w in warnings] + [f"ERROR {e}" for e in errors]
    (WORK / "lint.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    log.info(f"{len(errors)} error(s), {len(warnings)} warning(s) (full list: {rel(WORK / 'lint.txt')})")
    if warnings:
        log.warn(f"lint: {len(warnings)} warning(s), see {rel(WORK / 'lint.txt')}")
    if errors:
        for e in errors[:40]:
            print(f"    ERROR {e}")
        if len(errors) > 40:
            print(f"    ... {len(errors) - 40} more in {rel(WORK / 'lint.txt')}")
        raise BuildError(f"lint: {len(errors)} error(s)")
    return rows


def step2_java_tools():
    log.step(2, "compile tools/java (javac --release 8)")
    for jar in ASM:
        if not jar.is_file():
            raise BuildError(f"missing {jar}")
    srcs = sorted(JAVA_SRC.glob("*.java"))
    run([JAVAC, "--release", "8", "-nowarn", "-encoding", "UTF-8", "-cp", cp(*ASM), "-d", WORK / "tools", *srcs], "javac tools")
    log.info(", ".join(s.name for s in srcs))


def jtool(*args, java=JAVA11, extra=()) -> list:
    return [java, *extra, "-Djava.awt.headless=true", "-cp", cp(*ASM, WORK / "tools"), *args]


# ------------------------------------------------------------------------------ step 3: k
def java_string(s: str) -> str:
    out = ['"']
    for unit in struct.unpack(f"<{len(s.encode('utf-16-le')) // 2}H", s.encode("utf-16-le")):
        ch = chr(unit)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif unit < 0x20:
            out.append(f"\\{unit:03o}")
        elif unit > 0x7E:
            out.append(f"\\u{unit:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def gen_k_source(rows: list[dict]) -> tuple[str, dict]:
    arrays = {a: [] for a in "abcdefg"}
    for r in rows:
        if r["array"] in arrays:
            if int(r["index"]) != len(arrays[r["array"]]):
                raise BuildError(f"{r['array']} rows out of order at index {r['index']}")
            arrays[r["array"]].append(r["sv"])
    for a, n in lint_strings.SIZES.items():
        if len(arrays[a]) != n:
            raise BuildError(f"array {a} has {len(arrays[a])} entries, {n} required")
    if arrays["g"][0] != "":
        raise BuildError("g[0] must be empty")
    hud: list[int] = []
    for i, s in enumerate(arrays["b"]):
        if len(s) != 7 or any(ch not in lint_strings.HUD_ALLOWED for ch in s):
            raise BuildError(f"b[{i}] {s!r}: 7 chars of space, A-Z or Ö required")
        hud += lint_strings.hud_bytes(s)

    def strings(name, decl):
        body = ",\n".join("        " + java_string(s) for s in arrays[name])
        return f"    {decl} {name} = {{\n{body}\n    }};\n"

    src = ("// GENERATED by tools/build.py from the sv column of translation/strings_sv.tsv. Do not edit.\n"
           "// Shape = the original abadia.k (docs/FORMAT.md 1.12, DECISIONS D2a): field names, types, flags, order.\n"
           "package abadia;\n\npublic final class k {\n"
           + strings("a", "public static final String[]")
           + "    static final byte[] b = {\n"
           + "".join(f"        {', '.join(str(b) for b in hud[h * 7:h * 7 + 7])},\n" for h in range(7))
           + "    };\n"
           + strings("c", "static String[]") + strings("d", "static String[]")
           + strings("e", "static String[]") + strings("f", "static String[]")
           + strings("g", "static final String[]")
           + "}\n")
    return src, {"arrays": arrays, "hud": hud}


def parse_javap_v(text: str) -> dict:
    lines = text.split("\n")
    info = {"major": None, "class_flags": None, "members": []}
    in_body = False
    cur = None
    for ln in lines:
        if not in_body:
            m = re.match(r"\s+major version: (\d+)", ln)
            if m:
                info["major"] = int(m.group(1))
            m = re.match(r"\s+flags: \((0x[0-9a-f]+)\)", ln)
            if m and info["class_flags"] is None:
                info["class_flags"] = m.group(1)
            if ln == "{":
                in_body = True
            continue
        if ln.startswith("  ") and not ln.startswith("   ") and ln.strip():
            cur = {"decl": ln.strip(), "descriptor": None, "flags": None}
            info["members"].append(cur)
        elif cur is not None:
            m = re.match(r"    descriptor: (\S+)", ln)
            if m:
                cur["descriptor"] = m.group(1)
            m = re.match(r"    flags: \((0x[0-9a-f]+)\)", ln)
            if m:
                cur["flags"] = m.group(1)
    return info


def step3_k(rows: list[dict], zf: zipfile.ZipFile) -> dict:
    log.step(3, "generate abadia/k.java, javac --release 7, prove the shape with javap")
    src, kdata = gen_k_source(rows)
    if not src.isascii():
        raise BuildError("k.java must be pure ASCII")
    srcf = WORK / "src/abadia/k.java"
    srcf.write_text(src, encoding="ascii")
    run([JAVAC, "--release", "7", "-g:none", "-encoding", "UTF-8", "-Xlint:-options", "-nowarn",
         "-d", WORK / "classes", srcf], "javac k.java")
    newk = WORK / "classes/abadia/k.class"
    origk = WORK / "orig/abadia/k.class"
    origk.write_bytes(zf.read("abadia/k.class"))
    out = {}
    for tag, path in (("orig", origk), ("new", newk)):
        out[tag + "_ps"] = run([JAVAP, "-p", "-s", path], f"javap -p -s {tag}")
        out[tag + "_v"] = run([JAVAP, "-v", "-p", path], f"javap -v {tag}")
        (WORK / f"javap/k_{tag}_ps.txt").write_text(out[tag + "_ps"] + "\n", encoding="utf-8")
        (WORK / f"javap/k_{tag}_v.txt").write_text(out[tag + "_v"] + "\n", encoding="utf-8")
    # javap -p -s: identical except the extra default constructor (D2a)
    ctor = ["public abadia.k();", "descriptor: ()V"]
    o_ps = [ln.strip() for ln in out["orig_ps"].split("\n") if ln.strip() and not ln.startswith("Classfile")]
    n_ps = [ln.strip() for ln in out["new_ps"].split("\n") if ln.strip() and not ln.startswith("Classfile")]
    i = n_ps.index(ctor[0]) if ctor[0] in n_ps else -1
    if i < 0 or n_ps[i + 1] != ctor[1]:
        raise BuildError("generated k: no default constructor where expected (javap -p -s)")
    n_wo = n_ps[:i] + n_ps[i + 2:]
    if n_wo != o_ps:
        raise BuildError("generated k: javap -p -s differs from the original beyond the default constructor:\n"
                         + "\n".join(sorted(set(n_wo) ^ set(o_ps))))
    ov, nv = parse_javap_v(out["orig_v"]), parse_javap_v(out["new_v"])
    if (ov["major"], ov["class_flags"]) != (51, "0x0031") or (nv["major"], nv["class_flags"]) != (51, "0x0031"):
        raise BuildError(f"k major/flags: original {ov['major']}/{ov['class_flags']}, generated {nv['major']}/{nv['class_flags']}")
    of = [(m["decl"], m["descriptor"], m["flags"]) for m in ov["members"] if m["descriptor"] and not m["descriptor"].startswith("(")]
    nf = [(m["decl"], m["descriptor"], m["flags"]) for m in nv["members"] if m["descriptor"] and not m["descriptor"].startswith("(")]
    if of != nf or len(of) != 7:
        raise BuildError(f"k fields differ:\n original {of}\n generated {nf}")
    om = sorted(m["decl"] for m in ov["members"] if m["descriptor"] and m["descriptor"].startswith("("))
    nm = sorted(m["decl"] for m in nv["members"] if m["descriptor"] and m["descriptor"].startswith("("))
    if om != ["static {};"] or nm != ["public abadia.k();", "static {};"]:
        raise BuildError(f"k methods: original {om}, generated {nm}")
    log.info(f"k.class {newk.stat().st_size} B: major 51, flags 0x0031, 7 fields identical "
             f"(names, descriptors, flags, order); extra public abadia.k() allowed (D2a)")
    kdata["class"] = newk.read_bytes()
    return kdata


# ------------------------------------------------------------------------------ step 4: j w E
def escape_spec(s: str) -> str:
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ord(ch) < 0x20 or ord(ch) > 0x7E:
            for unit in struct.unpack(f"<{len(ch.encode('utf-16-le')) // 2}H", ch.encode("utf-16-le")):
                out.append(f"\\u{unit:04x}")
        else:
            out.append(ch)
    return "".join(out)


def clinit_strings(path) -> list[tuple[str, int, str]]:
    out = run(jtool("ClassDiff", "clinit-strings", path), f"ClassDiff clinit-strings {path}")
    res = []
    for ln in out.split("\n"):
        if ln:
            f, i, v = ln.split("\t")
            res.append((f, int(i), v))
    return res


def step4_classes(rows: list[dict], zf: zipfile.ZipFile) -> dict:
    log.step(4, "patch abadia/j.class (Å), w.class (w.t[4], w.u[4]), E.class (E.h[4])")
    sv = {(r["array"], r["index"]): r["sv"] for r in rows}
    for c in ("j", "w", "E"):
        (WORK / f"orig/abadia/{c}.class").write_bytes(zf.read(f"abadia/{c}.class"))
    oj, nj = WORK / "orig/abadia/j.class", WORK / "classes/abadia/j.class"
    log.info(run(jtool("PatchJ", oj, nj, "125", "-2", "1"), "PatchJ"))
    md5 = hashlib.md5(nj.read_bytes()).hexdigest()
    if md5 != J_MD5:
        raise BuildError(f"patched j.class md5 {md5} != {J_MD5}")
    log.info(f"j.class {nj.stat().st_size} B md5 {md5} OK")
    log.info(run(jtool("ClassDiff", "samecode", oj, nj, "a(IIILjava/awt/Graphics;)V"), "ClassDiff j"))
    # negative control for the verifier step: the same patch with a broken frame
    run(jtool("PatchJ", oj, WORK / "neg/abadia/j.class", "125", "-2", "1", "1"), "PatchJ (negative control)")

    specs = {"w": [(4, W_OLD["t"], sv[("w.t", "4")]), (4, W_OLD["u"], sv[("w.u", "4")])],
             "E": [(4, E_OLD, sv[("E.h", "4")])]}
    expect = {"w": {("t", 4): sv[("w.t", "4")], ("u", 4): sv[("w.u", "4")]}, "E": {("h", 4): sv[("E.h", "4")]}}
    for c, spec in specs.items():
        specf = WORK / f"patch_{c}.spec"
        specf.write_text("".join(f"{i}\t{escape_spec(o)}\t{escape_spec(n)}\n" for i, o, n in spec), encoding="utf-8")
        o, n = WORK / f"orig/abadia/{c}.class", WORK / f"classes/abadia/{c}.class"
        for ln in run(jtool("PatchStrings", o, n, specf), f"PatchStrings {c}").split("\n"):
            log.info(ln.replace(str(WORK) + "/", ""))
        log.info(run(jtool("ClassDiff", "samecode", o, n, "<clinit>()V"), f"ClassDiff {c}"))
        before, after = clinit_strings(o), clinit_strings(n)
        if len(before) != len(after):
            raise BuildError(f"{c}.<clinit> string slots changed in number")
        for (f0, i0, v0), (f1, i1, v1) in zip(before, after):
            if (f0, i0) != (f1, i1):
                raise BuildError(f"{c}.<clinit> slot order changed")
            want = expect[c].get((f1, i1))
            if want is not None:
                if v1 != escape_spec(want):
                    raise BuildError(f"{c}.{f1}[{i1}] = {v1!r}, expected {escape_spec(want)!r}")
            elif v0 != v1:
                raise BuildError(f"{c}.{f1}[{i1}] changed from {v0!r} to {v1!r} (only index 4 may change)")
        log.info(f"{c}.<clinit>: only " + ", ".join(f"{f}[{i}]" for f, i in expect[c]) + " changed")
    return {c: (WORK / f"classes/abadia/{c}.class").read_bytes() for c in ("j", "w", "E")}


# ------------------------------------------------------------------------------ step 5: fuente
def step5_fuente(path: pathlib.Path, zf: zipfile.ZipFile, hud: list[int]) -> bytes:
    log.step(5, f"res/fuente.png = original + {rel(path)}")
    add = load_json_strict(path)
    orig = zf.read("res/fuente.png")
    oc = pngio.chunks(orig)
    plte, trns = pngio.chunk_body(orig, b"PLTE"), pngio.chunk_body(orig, b"tRNS")
    ow, oh, orows = pngio.decode_indexed8(orig)
    if (ow, oh) != (640, 8) or plte is None or trns is None:
        raise BuildError("original fuente.png is not the expected 640x8 palette PNG with tRNS")
    npal = len(plte) // 3

    def alpha(i):
        return trns[i] if i < len(trns) else 255

    problems = []
    if not isinstance(add, dict) or set(add) - {"legend", "cells"}:
        problems.append("top level must be {legend, cells}")
    legend = add.get("legend", {}) if isinstance(add, dict) else {}
    cells = add.get("cells", {}) if isinstance(add, dict) else {}
    if legend.get(".") != FONT_TRANSPARENT:
        problems.append(f'legend "." must be {FONT_TRANSPARENT} (the transparent background)')
    for ch, idx in legend.items():
        if len(ch) != 1 or not isinstance(idx, int) or isinstance(idx, bool):
            problems.append(f"legend entry {ch!r}: {idx!r}")
        elif not 0 <= idx < npal:
            problems.append(f"legend {ch!r} -> {idx}: not in the {npal}-entry PLTE")
        elif ch != "." and (alpha(idx) != 255 or idx == FONT_TRANSPARENT):
            problems.append(f"legend {ch!r} -> {idx}: ink must use an opaque palette index (alpha {alpha(idx)})")
    blank_orig = {c for c in range(FONT_ORIG_CELLS)
                  if all(orows[y][c * 8 + x] == FONT_TRANSPARENT for y in range(8) for x in range(8))}
    if blank_orig != BLANK_CELLS_DOC:
        log.warn(f"original blank cells {sorted(blank_orig)} differ from FORMAT §3.3 {sorted(BLANK_CELLS_DOC)}")
    parsed = {}
    for key, cell in cells.items():
        if not re.fullmatch(r"[0-9]+", key) or key != str(int(key)):
            problems.append(f"cell key {key!r} is not canonical (write \"{int(key)}\")"
                            if re.fullmatch(r"[0-9]+", key) else f"cell key {key!r} is not a decimal number")
            continue
        n = int(key)
        if n < FONT_ORIG_CELLS and n not in blank_orig:
            problems.append(f"cell {n} is not blank in the original (only {sorted(blank_orig)} may be filled)")
            continue
        if n == 75:
            log.warn("cell 75 (code 120 'x') is unreachable: j.a maps 'x' to Ê and the hour byte 120 is forbidden")
        if n > MAX_ADD_CELL:
            problems.append(f"cell {n}: appended cells must be {RING_CELL}..{MAX_ADD_CELL} (codes 125..127). Cell n is "
                            f"drawn for char code n+45 >= 128, which other languages' shipped strings reach "
                            f"(cell 98 = U+008F in Italian g[124], g[156], g[157]), so filling it would change them")
            continue
        rws = cell.get("rows") if isinstance(cell, dict) else None
        if not isinstance(rws, list) or len(rws) != 8 or any(not isinstance(r, str) or len(r) != 8 for r in rws):
            problems.append(f"cell {n}: rows must be 8 strings of 8 chars")
            continue
        bad = sorted(set("".join(rws)) - set(legend))
        if bad:
            problems.append(f"cell {n}: characters {bad} not in the legend")
            continue
        if not isinstance(cell.get("purpose", ""), str):
            problems.append(f"cell {n}: purpose must be a string")
        parsed[n] = [[legend[ch] for ch in r] for r in rws]
    if problems:
        raise BuildError("fuente_add.json: " + "; ".join(problems))
    ncells = max([FONT_ORIG_CELLS - 1] + list(parsed)) + 1
    width = 8 * ncells
    rows = [bytearray(orows[y]) + bytearray([FONT_TRANSPARENT] * (width - 640)) for y in range(8)]
    for n, cell in sorted(parsed.items()):
        for y in range(8):
            rows[y][n * 8:n * 8 + 8] = bytes(cell[y])
    data = pngio.encode_indexed8(width, 8, rows, plte, trns)
    # ---- verify the written file
    nc = pngio.chunks(data)
    if [t for t, _, _ in nc] != [b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND"]:
        raise BuildError("fuente.png chunk layout")
    if pngio.chunk_body(data, b"PLTE") != plte or pngio.chunk_body(data, b"tRNS") != trns:
        raise BuildError("fuente.png PLTE/tRNS not copied verbatim")
    plte_pos = [off for t, _, off in nc if t == b"PLTE"][0] + 4
    if plte_pos >= 1000 or data.find(b"PLTE") != plte_pos:
        raise BuildError(f"fuente.png PLTE tag at {plte_pos} (must be the first 'PLTE' within 1000 bytes)")
    info = pngio.ihdr(data)
    if (info["color_type"], info["bit_depth"]) != (3, 8):
        raise BuildError("fuente.png must be 8-bit colour type 3")
    w2, h2, rows2 = pngio.decode_indexed8(data)
    for c in range(ncells):
        cell_new = [rows2[y][c * 8:c * 8 + 8] for y in range(8)]
        if c < FONT_ORIG_CELLS and c not in parsed:
            if cell_new != [orows[y][c * 8:c * 8 + 8] for y in range(8)]:
                raise BuildError(f"fuente.png cell {c} changed")
        elif c in parsed:
            if [list(r) for r in cell_new] != parsed[c]:
                raise BuildError(f"fuente.png cell {c} not written as specified")
        elif any(v != FONT_TRANSPARENT for r in cell_new for v in r):
            raise BuildError(f"fuente.png appended cell {c} is not transparent")
    filled = {c for c in range(ncells) if any(rows2[y][c * 8 + x] != FONT_TRANSPARENT for y in range(8) for x in range(8))}
    if RING_CELL not in filled:
        raise BuildError(f"fuente.png: cell {RING_CELL} (the Å ring, code 125) is missing or blank")
    for h in range(7):
        for k, b in enumerate(hud[h * 7:h * 7 + 7]):
            if b != 32 and (b - 45) not in filled:
                raise BuildError(f"HUD hour {h} cell {k}: byte {b} draws cell {b - 45}, which is blank or missing")
    for c in sorted(parsed):
        log.info(f"cell {c}: {cells[str(c)].get('purpose', '')}")
    log.info(f"{width}x8 ({ncells} cells), PLTE/tRNS verbatim, cells 0..79 identical except filled blanks "
             f"{sorted(c for c in parsed if c < 80)}; {len(data)} B")
    return data


# ------------------------------------------------------------------------------ step 6: letras
def step6_letras(path: pathlib.Path, zf: zipfile.ZipFile) -> bytes:
    log.step(6, f"res/letras = original + {rel(path)}")
    add = load_json_strict(path)
    orig = zf.read("res/letras")
    if len(orig) != L.ORIG_SIZE:
        raise BuildError(f"original letras is {len(orig)} B, expected {L.ORIG_SIZE}")
    if not isinstance(add, dict):
        raise BuildError("letras_add.json: not an object")
    new, problems = L.apply_add(orig, add)
    if problems:
        raise BuildError("letras_add.json: " + "; ".join(problems))
    errors, warnings = L.verify_add(orig, new, add)
    for w in warnings:
        log.warn(w)
    if errors:
        raise BuildError("letras: " + "; ".join(errors))
    added = sorted(int(k, 16) for k in add["glyphs"])
    missing = sorted(set(L.SLOT_CHARS) - set(added))
    if missing:
        log.warn("letras_add.json lacks " + " ".join(L.SLOT_CHARS[s] for s in missing)
                 + " (any parchment text using them fails the byte check)")
    lt = L.Letras(new)
    for s in added:
        g = lt.glyphs[s]
        rep = len(g["pixels"]) - len(set(g["pixels"]))
        log.info(f"slot {s:02X} {L.SLOT_CHARS[s]}: {len(g['pixels'])} px ({rep} repeated, drawn darker), "
                 f"advance {g['adv']}, addr 0x{g['addr']:04X}")
    log.info(f"{len(orig)} -> {len(new)} B; original bytes unchanged except {len(added)} slot pointers")
    return new


# ------------------------------------------------------------------------------ step 7: pergamino
def step7_pergamino(paths: dict, letras_bytes: bytes) -> dict:
    log.step(7, "res/de/pergamino1, pergamino2")
    lt = L.Letras(letras_bytes)
    out = {}
    for name, path in paths.items():
        if not path.is_file():
            raise BuildError(f"missing {path}")
        data, errors, src_lines = L.load_text_file(path, rel(path))   # the same reader as `letras.py check --text`
        if errors:
            for e in errors[:30]:
                print(f"    ERROR {e}")
            raise BuildError(f"{rel(path)}: {len(errors)} bad character(s)/format error(s)")
        res = L.check_bytes(data, lt, f"{name} ({rel(path)})", src_lines)
        for w in res["warnings"]:
            log.warn(w)
        if res["errors"]:
            for e in res["errors"][:30]:
                print(f"    ERROR {e}")
            raise BuildError(f"{rel(path)}: {len(res['errors'])} layout error(s)")
        log.info(f"{name}: {len(data)} B, {res['pages']} page(s), {res['lines']} lines, widest ink x={res['max_ink']} "
                 f"(limit {L.INK_LIMIT})")
        out[name] = data
    return out


# ------------------------------------------------------------------------------ step 8: images
def _bbox(pts) -> str:
    xs, ys = [x for x, _ in pts], [y for _, y in pts]
    return f"[{min(xs)},{min(ys)},{max(xs)},{max(ys)}]"


def image_rules(name: str, data: bytes, odata: bytes, where: str) -> list[str]:
    """Decode a Swedish image (Pillow, which FORMAT §6.4 shows decodes like the game's AWT) and return
    WARNINGs for the FORMAT §6.3/§6.4 rules. A file that does not decode is a BuildError."""
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
        rgba = im.convert("RGBA")
        orgba = Image.open(io.BytesIO(odata)).convert("RGBA")
    except Exception as ex:   # Pillow raises OSError, SyntaxError, ValueError, zlib.error ... on bad data
        raise BuildError(f"{where}: the pixel data does not decode: {type(ex).__name__}: {ex}")
    w, h = rgba.size
    px, opx = rgba.load(), orgba.load()
    out = []
    if rgba.tobytes() == orgba.tobytes():
        out.append(f"{name}: pixel-identical to the original (English) res/de/{name}: not translated?")
    if name in ONE_BIT_ALPHA:
        part = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] not in (0, 255)]
        if part:
            out.append(f"{name}: {len(part)} pixels with partial alpha in {_bbox(part)} (FORMAT §6.4: strictly 1-bit alpha)")
    if name in MOON_IMAGES:
        moon = [(x, y) for y in range(min(h, 100)) for x in range(250, w) if px[x, y][3]]
        if moon:
            omoon = sum(1 for y in range(min(h, 100)) for x in range(250, w) if opx[x, y][3])
            out.append(f"{name}: {len(moon)} non-transparent pixels in the moon window x >= 250, y < 100 at "
                       f"{_bbox(moon)} (FORMAT §6.3: luna/niebla/ventana are drawn opaque there; keep ink and glow "
                       f"out; the original de file has {omoon})")
    if name == "intro/pulsa.png":
        x0, y0, x1, y1 = PULSA_BAND
        stray = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] and not (x0 <= x <= x1 and y0 <= y <= y1)]
        if stray:
            out.append(f"{name}: {len(stray)} non-transparent pixels outside the text band x {x0}..{x1}, y {y0}..{y1} "
                       f"at {_bbox(stray)} (FORMAT §6.3: pulsa is drawn over monje/logo and must stay transparent "
                       f"outside its text)")
    if name == "marcador.png":
        changed = [(x, y) for y in range(h) for x in range(w) if px[x, y] != opx[x, y]]
        # v.b() paints x 37..60, y 7..14 black every frame: a change there is invisible, so only new
        # (non-dark) ink is reported, as a word that will look clipped
        boxed = [(x, y) for x, y in changed if 37 <= x <= 60 and 7 <= y <= 14]
        hidden_ink = [(x, y) for x, y in boxed if max(px[x, y][:3]) > 40 and px[x, y][3]]
        boxed_set = set(boxed)
        outside = [(x, y) for x, y in changed if (x, y) not in boxed_set and not (y <= 20 and x <= 38)]
        if hidden_ink:
            out.append(f"{name}: {len(hidden_ink)} pixels of new ink at {_bbox(hidden_ink)} lie in the day-numeral "
                       f"box x 37..60, y 7..14, which v.b() paints black every frame (FORMAT §6.3: keep the word at "
                       f"x <= 36 on rows 7..14)")
        if outside:
            out.append(f"{name}: {len(outside)} pixels differ from the original de file outside the day-word area "
                       f"(rows 0..20, x <= 38) at {_bbox(outside)} (FORMAT §6.3: x >= 39 is the numeral frame, "
                       f"rows >= 21 the hour strip)")
    return out


IMAGE_BUILDERS = ["marcador", "loading", "pulsa", "manuydani", "pacoyjuan", "novela", "pelicula"]


def step8a_rebuild_images(args) -> str | None:
    log.step("8a", "rebuild the Swedish images (tools/images/build_*.py -> assets_sv/res/de/)")
    if args.no_image_rebuild:
        log.info("skipped (--no-image-rebuild)")
        return None
    if args.assets != (ROOT / "assets_sv").resolve():
        log.info(f"skipped: --assets is {rel(args.assets)}, and the builders write to assets_sv/")
        return None
    script = HERE / "images" / "inputs.py"
    r = subprocess.run(["uv", "run", "--quiet", str(script)], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        raise BuildError(f"{rel(script)} failed (exit {r.returncode}):\n{r.stdout[-2000:]}{r.stderr[-2000:]}")
    inputs_dir = rel(r.stdout.strip().splitlines()[-1])
    log.info(f"builder inputs: {inputs_dir} (res/**.png of the original jar + glyph inventory, made by {rel(script)})")
    for name in IMAGE_BUILDERS:
        script = HERE / "images" / f"build_{name}.py"
        r = subprocess.run(["uv", "run", "--quiet", str(script)], cwd=ROOT, capture_output=True, text=True)
        if r.returncode:
            raise BuildError(f"{rel(script)} failed (exit {r.returncode}):\n{r.stdout[-2000:]}{r.stderr[-2000:]}")
        log.info(f"{rel(script)}: OK")
    return inputs_dir


def step8_images(args, zf: zipfile.ZipFile) -> tuple[dict, dict]:
    img_dir = args.assets / "res" / "de"
    log.step(8, f"images from {rel(img_dir)}")
    found = {}
    if img_dir.is_dir():
        for p in sorted(img_dir.rglob("*")):
            if p.is_file():
                found[p.relative_to(img_dir).as_posix()] = p
    unknown = sorted(set(found) - set(SV_IMAGES))
    if unknown:
        raise BuildError(f"unexpected files in {rel(img_dir)}: {unknown} (only {sorted(SV_IMAGES)})")
    out, sources = {}, {}
    for name, (w, h) in SV_IMAGES.items():
        orig_name = f"res/de/{name}"
        if name not in found:
            if not args.allow_missing_assets:
                raise BuildError(f"missing Swedish image {rel(img_dir / name)} (use --allow-missing-assets to fall back)")
            log.warn(f"!!! MISSING Swedish image {name}: using the ORIGINAL {orig_name} (English) !!!")
            out[orig_name] = zf.read(orig_name)
            sources[name] = "FALLBACK original " + orig_name
            continue
        data = found[name].read_bytes()
        try:
            info = pngio.ihdr(data)
            types = [t for t, _, _ in pngio.chunks(data)]
            pngio.check_image_data(data)
        except pngio.PngError as ex:
            raise BuildError(f"{rel(found[name])}: {ex}")
        if (info["width"], info["height"]) != (w, h):
            raise BuildError(f"{rel(found[name])}: {info['width']}x{info['height']}, must be {w}x{h}")
        bad = [t.decode("latin-1") for t in types if t in (b"gAMA", b"iCCP")]
        if bad:
            raise BuildError(f"{rel(found[name])}: contains {bad} chunks (FORMAT §6.4: none allowed)")
        odata = zf.read(orig_name)
        oinfo = pngio.ihdr(odata)
        if info["color_type"] != oinfo["color_type"]:
            raise BuildError(f"{rel(found[name])}: colour type {info['color_type']}, the original de file has "
                             f"{oinfo['color_type']} (keep each file's mode, FORMAT §6.4)")
        if info["interlace"]:
            log.warn(f"{name}: interlaced PNG")
        other = sorted({t.decode("latin-1") for t in types} - {"IHDR", "PLTE", "tRNS", "IDAT", "IEND", "pHYs", "tEXt"})
        if other:
            log.warn(f"{name}: extra chunks {other}")
        rule_warnings = image_rules(name, data, odata, rel(found[name]))
        for wmsg in rule_warnings:
            log.warn(wmsg)
        out[orig_name] = data
        sources[name] = rel(found[name]) + " sha256 " + sha256(data)
        log.info(f"{name}: {w}x{h} colour type {info['color_type']} from {rel(found[name])}; pixel data decodes"
                 + ("; FORMAT §6.3/§6.4 rules OK" if not rule_warnings else f"; {len(rule_warnings)} rule warning(s)"))
    es_logo = zf.read("res/es/intro/logo.png")
    out["res/de/intro/logo.png"] = es_logo
    sources["intro/logo.png"] = "byte copy of res/es/intro/logo.png (DECISIONS D3a)"
    log.info("intro/logo.png = byte copy of res/es/intro/logo.png; luna/monje/niebla/ventana kept")
    return out, sources


# ------------------------------------------------------------------------------ step 9: jar
def step9_jar(zf: zipfile.ZipFile, changed: dict) -> pathlib.Path:
    log.step(9, "rebuild the jar (same entry order, compression and dates)")
    names = [i.filename for i in zf.infolist()]
    missing = sorted(set(changed) - set(names))
    if missing:
        raise BuildError(f"replacement entries not in the original jar: {missing}")
    allowed = re.compile(r"^(abadia/[kjwE]\.class|res/fuente\.png|res/letras|res/de/.+)$")
    for n in changed:
        if not allowed.match(n):
            raise BuildError(f"refusing to replace {n}")
    jar = WORK / JAR_NAME
    with zipfile.ZipFile(jar, "w") as out:
        for info in zf.infolist():
            data = changed.get(info.filename)
            if data is None:
                data = zf.read(info.filename)
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type = info.compress_type
            zi.external_attr = info.external_attr
            zi.create_system = info.create_system
            zi.create_version = info.create_version
            zi.extract_version = info.extract_version
            zi.extra = info.extra
            zi.comment = info.comment
            out.writestr(zi, data)
            zi.external_attr = info.external_attr   # zipfile turns 0 into 0o600<<16; the central directory keeps ours
    with zipfile.ZipFile(jar) as chk:
        if chk.testzip() is not None:
            raise BuildError("jar CRC check failed")
        new = chk.infolist()
        if [i.filename for i in new] != names:
            raise BuildError("jar entry order changed")
        for a, b in zip(zf.infolist(), new):
            if (a.compress_type, a.date_time, a.external_attr, a.extra) != (b.compress_type, b.date_time, b.external_attr, b.extra):
                raise BuildError(f"{a.filename}: compression/date/attributes changed")
            want = changed.get(a.filename)
            if chk.read(b.filename) != (want if want is not None else zf.read(a.filename)):
                raise BuildError(f"{a.filename}: content mismatch")
    log.info(f"{rel(jar)}: {len(names)} entries, {len(changed)} replaced, {jar.stat().st_size} B")
    return jar


def step9b_verify(jar: pathlib.Path, kdata: dict, rows: list[dict]):
    log.step("9b", "verify classes: CheckClassAdapter + load/link under -Xverify:all on JDK 11 and JDK 8")
    classes = ["abadia/k", "abadia/j", "abadia/w", "abadia/E"]
    sv = {(r["array"], r["index"]): r["sv"] for r in rows}
    if not pathlib.Path(JAVA8).exists():
        raise BuildError(f"JDK 8 not found at {JAVA8}")
    dumps = {}
    for tag, java in (("jdk11", JAVA11), ("jdk8", JAVA8)):
        dump = WORK / f"verify/{tag}_dump.txt"
        out = run(jtool("VerifyClasses", "--jar", jar, "--init", "abadia/k,abadia/w", "--dump", dump, *classes,
                        java=java, extra=VERIFY_FLAGS[:2]), f"VerifyClasses ({tag})")
        (WORK / f"verify/{tag}.txt").write_text(out + "\n", encoding="utf-8")
        log.info(out.split("\n")[-1])
        neg = run(jtool("VerifyClasses", "--jar", jar, "--classes", WORK / "neg", "abadia/j",
                        java=java, extra=VERIFY_FLAGS[:2]), f"negative control ({tag})", expect_fail=True)
        if "VerifyError" not in neg:
            raise BuildError(f"negative control ({tag}): the broken-frame j.class was not rejected by the JVM verifier:\n{neg}")
        log.info(f"negative control ({tag}): broken-frame j.class rejected (java.lang.VerifyError) -> the link step verifies")
        dumps[tag] = dump.read_text(encoding="utf-8")
    if dumps["jdk11"] != dumps["jdk8"]:
        raise BuildError("JDK 8 and JDK 11 see different k/w values")
    pristine = WORK / "verify/pristine_dump.txt"
    run(jtool("VerifyClasses", "--jar", ORIG_JAR, "--init", "abadia/w", "--dump", pristine, "abadia/w",
              extra=VERIFY_FLAGS[:2]), "VerifyClasses (pristine w)")
    got = dict(ln.split("\t", 1) for ln in dumps["jdk11"].split("\n") if ln)
    orig = dict(ln.split("\t", 1) for ln in pristine.read_text(encoding="utf-8").split("\n") if ln)
    want = {}
    for a, arr in kdata["arrays"].items():
        if a == "b":
            continue
        want[f"abadia/k.{a}.length"] = str(len(arr))
        for i, s in enumerate(arr):
            want[f"abadia/k.{a}[{i}]"] = escape_spec(s)
    want["abadia/k.b.length"] = "49"
    for i, b in enumerate(kdata["hud"]):
        want[f"abadia/k.b[{i}]"] = str(b)
    for f in ("t", "u"):
        for i in range(6):
            key = f"abadia/w.{f}[{i}]"
            want[key] = escape_spec(sv[(f"w.{f}", "4")]) if i == 4 else orig[key]
        want[f"abadia/w.{f}.length"] = "6"
    bad = [k for k in want if got.get(k) != want[k]]
    if bad:
        raise BuildError("runtime values differ: " + "; ".join(f"{k}: got {got.get(k)!r} want {want[k]!r}" for k in bad[:10]))
    n_str = sum(len(v) for a, v in kdata["arrays"].items() if a != "b")
    n_hours = len(kdata["arrays"].get("b", []))
    log.info(f"runtime values of k ({n_str} strings (a,c..g) + {n_hours} hour names (b, {len(kdata['hud'])} bytes)) "
             f"and w.t/w.u match the TSV; w.t/w.u other slots unchanged")


# ------------------------------------------------------------------------------ step 10: game dir
def game_file_names() -> list[str]:
    names = [p.name for p in sorted(ORIG.iterdir()) if p.suffix in (".sh", ".bat", ".pdf")]
    names += ["TheAbbeyOfCrimeExtensum(Swedish).sh", "TheAbbeyOfCrimeExtensum(Swedish).bat", JAR_NAME]
    return names + ([MANUAL_NAME] if MANUAL_PDF.is_file() else [])


def check_out_dir(out: pathlib.Path):
    """Refuse an --out this build must not wipe. Run before step 1 (nothing touched yet) and again in step 10."""
    root, orig, work = ROOT.resolve(), ORIG.resolve(), WORK.resolve()
    if out == pathlib.Path("/") or out == root or out in root.parents or out == orig or orig in out.parents \
            or out == work or work in out.parents or out == root / "work" or out == root / "tools" \
            or out == root / "translation" or out == root / "assets_sv" or out == root / "docs":
        raise BuildError(f"refusing to use {out} as the output dir")
    if out.exists() and not out.is_dir():
        raise BuildError(f"--out {out} exists and is not a directory")
    if out.exists():
        # MANUAL_NAME always: a game dir from a build made while manual/ had the PDF stays wipeable.
        allowed = set(game_file_names()) | {SAVEDATA, MANUAL_NAME}
        unknown = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.relative_to(out).as_posix() not in allowed)
        bad = sorted(p.relative_to(out).as_posix() for p in out.iterdir() if p.is_dir() or p.is_symlink())
        if unknown or bad:
            raise BuildError(f"refusing to wipe {out}: it contains files this build does not write: {(bad + unknown)[:10]}")


def step10_game(args, jar: pathlib.Path) -> pathlib.Path:
    out = args.out
    log.step(10, f"game dir {rel(out)}")
    check_out_dir(out)
    en_sh = (ORIG / "TheAbbeyOfCrimeExtensum(English).sh").read_bytes()
    en_bat = (ORIG / "TheAbbeyOfCrimeExtensum(English).bat").read_bytes()
    if not en_sh.endswith(b" en") or not en_bat.endswith(b" en"):
        raise BuildError("unexpected English launcher format")
    new_files = {name: ("copy", p) for name, p in
                 ((p.name, p) for p in sorted(ORIG.iterdir()) if p.suffix in (".sh", ".bat", ".pdf"))}
    new_files["TheAbbeyOfCrimeExtensum(Swedish).sh"] = ("data", en_sh[:-3] + b" de")
    new_files["TheAbbeyOfCrimeExtensum(Swedish).bat"] = ("data", en_bat[:-3] + b" de")
    new_files[JAR_NAME] = ("copy", jar)
    if MANUAL_PDF.is_file():
        new_files[MANUAL_NAME] = ("copy", MANUAL_PDF)
    else:
        log.info(f"no Swedish manual: {rel(MANUAL_PDF)} does not exist (uv run tools/manual/build_manual.py)")
    if sorted(new_files) != sorted(game_file_names()):
        raise BuildError("internal: game file list mismatch")
    keep_save = None
    if out.exists():
        if (out / SAVEDATA).is_file():
            keep_save = (out / SAVEDATA).read_bytes()
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name, (kind, src) in new_files.items():
        dst = out / name
        dst.write_bytes(src.read_bytes() if kind == "copy" else src)
        os.chmod(dst, 0o755 if name.endswith(".sh") else 0o644)
    if keep_save is not None:
        (out / SAVEDATA).write_bytes(keep_save)
        log.info(f"kept the existing {SAVEDATA}")
    log.info(f"{len(new_files)} files: {sum(n.endswith('.sh') for n in new_files)} .sh (755), "
             f"{sum(n.endswith('.bat') for n in new_files)} .bat, {sum(n.endswith('.pdf') for n in new_files)} PDFs, the jar")
    return out


# ====================================================================================== main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strings", type=pathlib.Path, default=ROOT / "translation" / "strings_sv.tsv")
    ap.add_argument("--perg1", type=pathlib.Path, default=ROOT / "translation" / "pergamino1_sv.txt")
    ap.add_argument("--perg2", type=pathlib.Path, default=ROOT / "translation" / "pergamino2_sv.txt")
    ap.add_argument("--assets", type=pathlib.Path, default=ROOT / "assets_sv")
    ap.add_argument("--fuente-add", type=pathlib.Path, default=None)
    ap.add_argument("--letras-add", type=pathlib.Path, default=None)
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "game")
    ap.add_argument("--placeholder", action="store_true")
    ap.add_argument("--allow-missing-assets", action="store_true")
    ap.add_argument("--no-image-rebuild", action="store_true")
    args = ap.parse_args()
    args.fuente_add = args.fuente_add or args.assets / "glyphs" / "fuente_add.json"
    args.letras_add = args.letras_add or args.assets / "glyphs" / "letras_add.json"
    for name in ("strings", "perg1", "perg2", "assets", "fuente_add", "letras_add", "out"):
        setattr(args, name, getattr(args, name).resolve())

    LOCK.parent.mkdir(parents=True, exist_ok=True)
    lockf = open(LOCK, "w")
    try:
        fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("BUILD FAILED: another build.py is running (work/.build.lock)")
        sys.exit(1)
    try:
        check_out_dir(args.out)
        zf = step1_original()
        rows = step_lint(args)
        step2_java_tools()
        kdata = step3_k(rows, zf)
        cls = step4_classes(rows, zf)
        fuente = step5_fuente(args.fuente_add, zf, kdata["hud"])
        letras = step6_letras(args.letras_add, zf)
        perg = step7_pergamino({"pergamino1": args.perg1, "pergamino2": args.perg2}, letras)
        image_inputs = step8a_rebuild_images(args)
        images, img_sources = step8_images(args, zf)
        changed = {"abadia/k.class": kdata["class"], "abadia/j.class": cls["j"], "abadia/w.class": cls["w"],
                   "abadia/E.class": cls["E"], "res/fuente.png": fuente, "res/letras": letras,
                   "res/de/pergamino1": perg["pergamino1"], "res/de/pergamino2": perg["pergamino2"], **images}
        for name, data in changed.items():
            p = WORK / name.replace("abadia/", "classes/abadia/") if name.startswith("abadia/") else WORK / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        jar = step9_jar(zf, changed)
        step9b_verify(jar, kdata, rows)
        out = step10_game(args, jar)

        log.step(12, "manifest")
        game_files = {}
        for p in sorted(out.rglob("*")):
            if p.is_file() and p.name != SAVEDATA:
                game_files[p.relative_to(out).as_posix()] = {"sha256": sha256(p.read_bytes()),
                                                              "mode": oct(p.stat().st_mode & 0o777)}
        actually_changed = {n: sha256(d) for n, d in sorted(changed.items()) if d != zf.read(n)}
        manifest = {
            "original_jar_sha256": sha256(ORIG_JAR.read_bytes()),
            "options": {"placeholder": args.placeholder, "allow_missing_assets": args.allow_missing_assets},
            "inputs": {k: {"path": rel(getattr(args, k)), "sha256": sha256(getattr(args, k).read_bytes())}
                       for k in ("strings", "perg1", "perg2", "fuente_add", "letras_add")},
            "images": img_sources,
            "image_inputs": image_inputs,
            "game": game_files,
            "jar_changed_entries": actually_changed,
            "jar_unchanged_replacements": sorted(n for n, d in changed.items() if d == zf.read(n)),
            "warnings": log.warnings,
        }
        mtext = json.dumps(manifest, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
        (WORK / "manifest.json").write_text(mtext, encoding="utf-8")
        log.info(f"{rel(WORK / 'manifest.json')} sha256 {sha256(mtext.encode())}")
        print("\n==== BUILD OK ====")
        print(f"game dir : {rel(out)}  (launch: '{out / 'TheAbbeyOfCrimeExtensum(Swedish).sh'}')")
        print(f"jar      : sha256 {game_files[JAR_NAME]['sha256']}")
        print(f"changed  : {', '.join(actually_changed)}")
        fallback = [k for k, v in img_sources.items() if v.startswith("FALLBACK")]
        if fallback:
            print(f"!!! FALLBACK IMAGES (original English de files): {', '.join(fallback)} !!!")
        if args.placeholder:
            print("!!! PLACEHOLDER MODE: untranslated strings were allowed !!!")
        print(f"warnings : {len(log.warnings)} (listed in the manifest; lint details in {rel(WORK / 'lint.txt')})")
    except BuildError as ex:
        print(f"\nBUILD FAILED: {ex}")
        sys.exit(1)
    finally:
        fcntl.flock(lockf, fcntl.LOCK_UN)
        lockf.close()


if __name__ == "__main__":
    main()

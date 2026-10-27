# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Read-only inputs of the image builders, made from original/ alone.

  uv run tools/images/inputs.py          prepare them (if needed) and print the directory

The builders (tools/images/build_*.py, fraktur.py, script_och.py, preview_intro.py) never read the
extracted jar of Phase A (work/jar/) or its glyph inventory (work/phaseA/images/glyphs/). They read
two trees that this module derives from original/TheAbbeyOfCrimeExtensum.jar:

  JAR_DIR / "res/..."   every res/**.png entry of the original jar, extracted byte for byte
                        (RES = JAR_DIR / "res", so a source like 'res/es/intro/novela.png' is
                        JAR_DIR / that path)
  GLYPHS / ...          the glyph inventory: index.json, font_metrics.json, fraktur/*_mask.png,
                        hud/BACKGROUND_reconstructed_x0-41_y0-21.png and the rest, made by the
                        Phase A inventory scripts, copied into tools/images/inventory/ (unchanged
                        but for pinned dependency versions, the builders' pillow==11.3.0,
                        numpy==2.3.2 and scipy==1.16.1, so a new uv resolution cannot drift them)
                        (glyph_inventory.py RES OUT; font_metrics.py OUT; hud_glyphs.py RES OUT;
                        marks.py OUT; merge_index.py OUT)

Both live in work/inputs/<key>/ (git-ignored scratch), key = sha256 of the original jar, of the five
inventory scripts and of this file. The first use of a key builds it in a temporary directory and
publishes it with one atomic rename (under work/inputs/.lock); after that it is never changed, so
deleting work/ is always safe and a concurrent reader sees either nothing or the finished tree.
Importing this module prepares the inputs when they are missing (that runs `uv run` on the five
scripts, ~10 s); tools/build.py step 8a does it explicitly before running the builders.
The jar is untrusted data: only res/**.png entries with plain relative names are extracted, and the
scripts that read them are run from tools/, never from inside the data directory.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ORIG_JAR = ROOT / "original" / "TheAbbeyOfCrimeExtensum.jar"
BASE = ROOT / "work" / "inputs"
INVENTORY = HERE / "inventory"
# (script, arguments): R = the extracted res/ dir, G = the glyph dir; run in this order
STEPS = [("glyph_inventory.py", "RG"), ("font_metrics.py", "G"), ("hud_glyphs.py", "RG"),
         ("marks.py", "G"), ("merge_index.py", "G")]


def _key() -> str:
    h = hashlib.sha256()
    for p in [ORIG_JAR, Path(__file__).resolve()] + [INVENTORY / s for s, _ in STEPS]:
        if not p.is_file():
            sys.exit(f"inputs: missing {p}")
        h.update(p.name.encode() + b"\0" + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()[:16]


def _extract(jar: Path, dest: Path) -> int:
    n = 0
    with zipfile.ZipFile(jar) as zf:
        for info in zf.infolist():
            name = info.filename
            pp = PurePosixPath(name)
            if info.is_dir() or not name.startswith("res/") or not name.endswith(".png"):
                continue
            if pp.is_absolute() or ".." in pp.parts or "\\" in name:
                sys.exit(f"inputs: refusing jar entry with an unsafe name: {name!r}")
            out = dest / pp
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(zf.read(info))
            n += 1
    return n


def _build(key: str, final: Path) -> None:
    tmp = BASE / f".tmp-{key}-{os.getpid()}"
    if tmp.exists():
        shutil.rmtree(tmp)
    try:
        n = _extract(ORIG_JAR, tmp / "jar")
        res, glyphs = tmp / "jar" / "res", tmp / "glyphs"
        glyphs.mkdir(parents=True)
        env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY", "PYTHONPATH")}
        for script, argspec in STEPS:
            args = [str(res) if a == "R" else str(glyphs) for a in argspec]
            r = subprocess.run(["uv", "run", "--quiet", str(INVENTORY / script), *args], cwd=ROOT, env=env,
                               capture_output=True, text=True)
            if r.returncode:
                sys.exit(f"inputs: {script} failed (exit {r.returncode}):\n{r.stdout[-1500:]}{r.stderr[-1500:]}")
        auto = json.loads((glyphs / "auto_index.json").read_text(encoding="utf-8"))
        if auto["problems"]:
            sys.exit(f"inputs: the glyph inventory reports {len(auto['problems'])} problem line(s)")
        stamp = {"key": key, "original_jar_sha256": hashlib.sha256(ORIG_JAR.read_bytes()).hexdigest(),
                 "png_entries": n, "glyphs": len(auto["glyphs"]),
                 "scripts": {s: hashlib.sha256((INVENTORY / s).read_bytes()).hexdigest() for s, _ in STEPS}}
        (tmp / "DONE.json").write_text(json.dumps(stamp, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        os.rename(tmp, final)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)


def prepare() -> Path:
    """The inputs directory for the current original jar and scripts, built on first use."""
    if not ORIG_JAR.is_file():
        sys.exit(f"inputs: missing {ORIG_JAR} (the pristine download, see docs/FORMAT.md §0)")
    key = _key()
    final = BASE / key
    if (final / "DONE.json").is_file():
        return final
    BASE.mkdir(parents=True, exist_ok=True)
    with open(BASE / ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            if not (final / "DONE.json").is_file():
                if final.exists():          # a tree without its stamp is never published; be safe anyway
                    shutil.rmtree(final)
                _build(key, final)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
    return final


DIR = prepare()
JAR_DIR = DIR / "jar"
RES = JAR_DIR / "res"
GLYPHS = DIR / "glyphs"


if __name__ == "__main__":
    print(DIR)

# Build tooling (Phase D)

Everything runs from the project root. Python is always `uv run` (PEP 723 inline scripts); Java is
the system `java`/`javac` (JDK 11) plus JDK 8 at `/usr/lib/jvm/java-8-openjdk-amd64` for
verification. Nothing here opens a window: every Java process runs with `DISPLAY` unset and
`-Djava.awt.headless=true`. `docs/FORMAT.md` is the reference for every rule cited below.

## Build the game

```sh
uv run tools/build.py                 # translation/ + assets_sv/ + original/ -> game/
```

**Inputs.** Only these: `original/` (the pristine download: the jar, the launchers and the PDFs;
read, never written), `translation/`, the tracked parts of `assets_sv/` (`glyphs/*.json`,
`image_src/**`), and `tools/` itself. Everything else is derived on every build:
`assets_sv/res/de/**` is rewritten by the image builders (step 8a), and the builders read nothing
from `work/jar/` or `work/phaseA/`: `tools/images/inputs.py` extracts `res/**.png` from the original
jar and regenerates the glyph inventory with the Phase A scripts copied into
`tools/images/inventory/` (`glyph_inventory.py`, `font_metrics.py`, `hud_glyphs.py`, `marks.py`,
`merge_index.py`, byte copies), into `work/inputs/<key>/` (key = hash of the jar, the five scripts
and `inputs.py`; published by an atomic rename, never changed; regenerated output is byte-identical
to the Phase A inventory: 1803/1803 files). Deleting `work/` is always safe.

**Prerequisites** (not in git): `uv`; JDK 11 (`java`, `javac`, `javap` on the PATH); JDK 8 at
`/usr/lib/jvm/java-8-openjdk-amd64` (step 9b verifies the classes on it; the build fails without
it); and the ASM jars in `tools/` (git-ignored, from Maven Central; the local copies match Maven's
published SHA-1):

| file | URL (`https://repo1.maven.org/maven2/` + ...) | sha256 |
|---|---|---|
| `asm-9.7.1.jar` | `org/ow2/asm/asm/9.7.1/asm-9.7.1.jar` | `8cadd43ac5eb6d09de05faecca38b917a040bb9139c7edeb4cc81c740b713281` |
| `asm-tree-9.7.1.jar` | `org/ow2/asm/asm-tree/9.7.1/asm-tree-9.7.1.jar` | `9929881f59eb6b840e86d54570c77b59ce721d104e6dfd7a40978991c2d3b41f` |
| `asm-analysis-9.7.1.jar` | `org/ow2/asm/asm-analysis/9.7.1/asm-analysis-9.7.1.jar` | `85b29371884ba31bb76edf22323c2c24e172c3267a67152eba3d1ccc2e041ef2` |
| `asm-util-9.7.1.jar` | `org/ow2/asm/asm-util/9.7.1/asm-util-9.7.1.jar` | `f885be71b5c90556f5f1ad1c4f9276b29b96057c497d46666fe4ddbec3cb43c6` |
| `asm-commons-9.7.1.jar` (not used by the build) | `org/ow2/asm/asm-commons/9.7.1/asm-commons-9.7.1.jar` | `9a579b54d292ad9be171d4313fd4739c635592c2b5ac3a459bbd1049cddec6a0` |
| `cfr-0.152.jar` (decompiling only) | `org/benf/cfr/0.152/cfr-0.152.jar` | `f686e8f3ded377d7bc87d216a90e9e9512df4156e75b06c655a16648ae8765b2` |
| `vineflower-1.10.1.jar` (decompiling only) | `org/vineflower/vineflower/1.10.1/vineflower-1.10.1.jar` | `b9b208e50793b64657a6b6292067526613f549de7405f9243624b02f4276e409` |

Clean-room check (Phase E round 1): the tracked and trackable files (`git ls-files -co
--exclude-standard`) copied into an empty directory, plus `original/` and the ASM jars, built with
no `work/`, `game/` or `assets_sv/res/`. The jar and `work/build/manifest.json` (sha256 of every game
file and changed jar entry) were byte-identical to the in-tree build.

| option | default | meaning |
|---|---|---|
| `--strings PATH` | `translation/strings_sv.tsv` | all in-game strings (format: header `array index context speaker max_len es en sv note`, rows as `tools/data/context.tsv`) |
| `--perg1 PATH`, `--perg2 PATH` | `translation/pergamino{1,2}_sv.txt` | intro / ending parchment, UTF-8, one parchment line per text line |
| `--assets DIR` | `assets_sv` | Swedish images in `DIR/res/de/**`, glyph additions in `DIR/glyphs/` |
| `--fuente-add PATH`, `--letras-add PATH` | `DIR/glyphs/fuente_add.json`, `DIR/glyphs/letras_add.json` | font additions |
| `--out DIR` | `game/` | wiped and recreated; checked before anything is touched (refuses a file, a dir holding files it did not write, and project/system dirs; keeps `savedata.bin`) |
| `--placeholder` | off | Spanish placeholder text allowed: the untranslated-string lint errors (used `g`, `a c d e f`, HUD hours `b`, `w.t`, `w.u`) become warnings |
| `--allow-missing-assets` | off | a missing Swedish image falls back to the original `res/de` (English) file, with a loud WARNING |
| `--no-image-rebuild` | off | skip step 8a and use the images already in `assets_sv/res/de/` |

What it does (scratch in `work/build/`, wiped each run and used by nothing else; one build at a
time): checks the original jar's sha256; rebuilds the seven Swedish images from `work/inputs/<key>/`
(step 8a, above);
lints the strings first and stops on errors; compiles `tools/java/*.java`; generates
`abadia/k.java` from the `sv` column (non-ASCII as `\uXXXX`), compiles it with
`javac --release 7` and proves with `javap` that fields, descriptors, flags, class flags (0x0031) and
major (51) equal the original (extra default constructor allowed, D2a); patches `j.class` for Å
(`PatchJ 125 -2 1`, md5 `f197f5a3…`), `w.class` (`w.t[4]`, `w.u[4]`) and `E.class` (`E.h[4]`) with
ASM, proving that every other method and every other array slot is unchanged; builds
`res/fuente.png` (own PNG writer, PLTE/tRNS copied verbatim), `res/letras` (glyphs appended at EOF)
and `res/de/pergamino1|2` (byte map, CR lines, `0x1A`; every line's ink edge ≤ 244; no blank page and
no trailing whitespace-only lines); font cells may be added only in the original blank cells and
80..82 (a cell ≥ 83 is drawn for codes ≥ 128 that other languages use); glyph JSON keys must be
canonical (cell `"80"`, not `"080"`; slot `"5B"`, not `"5b"`) and no object may repeat a key; copies the
images (size/colour type checked, the pixel data fully inflated and decoded, and WARNINGs for the
FORMAT §6.3/§6.4 rules: 1-bit alpha in `loading.png`, nothing in the moon window x ≥ 250, y < 100 from
`manuydani` on, `pulsa` transparent outside its text band, `marcador` changed only in the day-word
area, and any image still pixel-identical to the English original; `logo.png` = es copy); rebuilds the jar with the original entry
order, compression and dates; verifies k/j/w/E with ASM `CheckClassAdapter` and by loading and
linking them under `-Xverify:all` on JDK 11 and JDK 8 (a broken-frame `j.class` is the negative
control that must be rejected), and compares the runtime values of `k` and `w` with the TSV; then
writes `game/` (original launchers and PDFs, the jar, `TheAbbeyOfCrimeExtensum(Swedish).sh/.bat`
made from the English launcher with ` en` → ` de`) and `work/build/manifest.json` (sha256 of every
game file and changed jar entry). Two runs with the same inputs give byte-identical output.

## Check

```sh
uv run tools/lint_strings.py [TSV] [--placeholder]   # string rules only (FORMAT §1.13); exit 1 on errors
                                                     # (an empty label f[3..7] is allowed: GLOSSARY §6.3 f[5] = "";
                                                     # a b row equal to its es/en hour is untranslated, except
                                                     # ' SEXT  '; a b note 'bytes=...' must equal the sv cell's bytes)
uv run tools/render_strings.py                       # all Swedish strings of game/ -> screenshots/strings/de/
uv run tools/render_strings.py --lang fr             # another language from the patched jar
uv run tools/regress.py                              # es en it fr pl: pristine vs patched, pixel-identical
```

`render_strings.py` (options `--game DIR`/`--jar`, `--out`, `--strings`, `--perg1`, `--perg2`,
`--placeholder`, `--ref-lang`, `--no-lint`, `--no-source-check`) runs the lint, renders with the
game's own code (message pages, pause-menu states, save slots, end screen, HUD hours, both
parchments; see `tools/harness/HARNESS.md`), checks that the jar's strings (every rendered one, plus
the never-drawn window title `E.h[4]` read from `E.class`) and parchments equal
`--strings`/`--perg1`/`--perg2` (so a source edited after the build is reported), and that the
parchment emulator `tools/letras.py` is pixel-identical to the real code. Exit 1 on any missing
glyph, layout error, lint error or mismatch. `regress.py` (`--out`, default `work/regress/`) also
checks that only `abadia/{k,j,w,E}.class`, `res/fuente.png`, `res/letras` and `res/de/**` differ from
the original jar, that fuente cells 0..79 and the original letras bytes are untouched, and that no
glyph was lost.

Both can run concurrently with each other, with other tracks' renders and with `build.py`: each
renders from a private snapshot of the jar (`work/.tmp/`, removed at exit), takes a lock per output
dir (`work/.locks/`), and uses the harness build that `tools/harness/build.sh` prints: a
content-addressed dir `work/harness_build/<key>` (key = hash of the sources, the script and javac),
published by an atomic rename and never modified or deleted. Old keys can be deleted by hand when
no render runs.

Parchment helper: `uv run tools/letras.py check FILE --text --letras game/TheAbbeyOfCrimeExtensum.jar`
(per-line ink edge; `--letras` takes a letras file or a jar and reads its `res/letras`; prefer the
built jar to `work/build/res/letras`, which every build wipes; `--text` files are read exactly as the
build reads them), `width "LINE"`, `pages FILE OUTDIR --text`, `encode`, `dump`.

## Files

| path | role |
|---|---|
| `build.py` | the build |
| `lint_strings.py`, `text_sim.py` | string lint; exact port of the message timing (copy of `work/phaseA/scripts/text_sim.py`) |
| `letras.py` | parchment codec: byte map, `letras_add.json`, decode, measure, render (port of `letras_render.py`) |
| `pngio.py` | stdlib PNG reader/writer for the palette font; strict IDAT check for the images |
| `classfile.py` | stdlib class-file reader: `<clinit>` array strings (as `ClassDiff clinit-strings`), used for `E.h[4]` |
| `java/PatchJ.java`, `PatchStrings.java`, `ClassDiff.java`, `VerifyClasses.java` | ASM patchers and verifiers |
| `harness/` | self-contained copy of the Phase A rendering harness (`build.sh`, `render.sh`, `src/`) |
| `render_strings.py`, `regress.py` | the two checkers above |
| `data/context.tsv` | byte copy of `work/phaseA/context.tsv` (row keys, es, en, used/dead) |
| `run_headless.sh`, `drivers/` | live game runs on a private Xvfb (FORMAT §7); a driver is stopped after `DRIVER_TIMEOUT` (default 1800 s), so `interactive.sh MAX` with MAX above that needs `DRIVER_TIMEOUT` raised too |
| `images/build_*.py`, `fraktur.py`, `script_och.py`, `preview_intro.py` | the seven Swedish image builders and their kits (run by step 8a) |
| `images/inputs.py`, `images/inventory/` | the builders' read-only inputs, made from `original/` alone (see *Inputs* above) |
| `check_glossary.py` | strings and parchments against `translation/glossary.tsv` (page breaks and parchment line wraps are ignored when matching) |

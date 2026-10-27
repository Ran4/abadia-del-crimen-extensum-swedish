# Build tooling (Phases D–F)

Everything runs from the project root. Python is always `uv run` (PEP 723 inline scripts); Java is
the system `java`/`javac` (JDK 11) plus JDK 8 at `/usr/lib/jvm/java-8-openjdk-amd64` for
verification. Nothing here puts a window on your screen. The build and the checkers run Java with
`DISPLAY` unset and `-Djava.awt.headless=true`. `run_headless.sh` runs the real game on a private
Xvfb display (never `:0`) and proves with `check_invisible` that `:0` has no game window (FORMAT
§7.1). `docs/FORMAT.md` is the reference for every rule cited below.

## Build the game

```sh
uv run tools/build.py                 # translation/ + assets_sv/ + original/ -> game/
```

**Inputs.** Only these: `original/` (the pristine download: the jar, the launchers and the PDFs;
read, never written), `translation/`, the tracked parts of `assets_sv/` (`glyphs/*.json`,
`image_src/**`), and `tools/` itself; plus `manual/Användarmanual.pdf` when it exists, which step
10 copies unchanged into the game dir as `User's manual (Swedish).pdf` (DECISIONS D15; without it
the game dir simply has no Swedish manual). Everything else is derived on every build:
`assets_sv/res/de/**` is rewritten by the image builders (step 8a), and the builders read nothing
from `work/jar/` or `work/phaseA/`: `tools/images/inputs.py` extracts `res/**.png` from the original
jar and regenerates the glyph inventory with the Phase A scripts copied into
`tools/images/inventory/` (`glyph_inventory.py`, `font_metrics.py`, `hud_glyphs.py`, `marks.py`,
`merge_index.py`; copies whose only change is that their dependencies are pinned to the builders'
versions, `pillow==11.3.0`, `numpy==2.3.2`, `scipy==1.16.1`), into `work/inputs/<key>/` (key = hash
of the jar, the five scripts and `inputs.py`; published by an atomic rename, never changed;
regenerated output is byte-identical to the Phase A inventory: 1803/1803 files; with the pins it is
still byte-identical to the unpinned Phase E tree, all 1900 files apart from `DONE.json`, checked
in the Phase F final verification). Deleting `work/` is always safe **for the build and the
checkers** (`build.py`, `lint_strings.py`, `check_glossary.py`, `render_strings.py`, `regress.py`).
It is not safe for everything else in `work/`:
- `translate_tool.py` `show`, `check`, `plan`, `merge` and `gameorder` read the Phase A dump
  (`work/phaseA/strings_all.json`, `text_index.json`) and the chunk files in `work/phaseC/`; its
  `letras` command and `letras.py` without `--letras` read `work/jar/res/letras`; and `letras.py
  pages` reads `work/jar/res/pergamino.png` unless `--res DIR` is given (after a build,
  `work/inputs/<key>/jar/res/` holds the original file).
- `work/` is also the only copy of the verification evidence that `docs/FORMAT.md` and the
  `screenshots/**/INDEX.md` files cite: the run dirs (`work/runs/`, `work/phaseE/runs/*/`, with
  `game.log`, `evidence.log`, `driver.log` and the agent's `events.log`), the raw shots and the
  match outputs. It also holds the Phase E runtime tools that drove the day-1 route: the read-only
  Java agent (`work/phaseE/agent/`) and the drivers (`work/phaseE/drivers/`: `follow.py`,
  `recorder.sh`, `skip_pages.sh`, `k.sh`; FORMAT §7.8). Keep it as the verification archive
  (DECISIONS D14).

The seven Swedish images in `assets_sv/res/de/` are derived files and are **not in git**
(`.gitignore`: `assets_sv/res/`). Every build regenerates them (step 8a), so a fresh checkout builds
without them; `--no-image-rebuild` uses whatever is already there.

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

**Runtime runs (`run_headless.sh`)** need more, none of it in git: Xvfb unpacked into
`tools/xvfb-root/` (git-ignored, like `tools/*.deb`; this machine has no system Xvfb):
`(cd tools && apt-get download xvfb && dpkg-deb -x xvfb_*.deb xvfb-root)`, or set `XVFB_BIN`. Also
`bwrap`, `pactl`/`parec` (PulseAudio or PipeWire), `xdotool`, `xwininfo`, `xwd` and ImageMagick 6
(`convert`, `identify`). The build and the checkers need none of these.

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
time): checks the original jar's sha256; lints the strings first and stops on errors (logged as
step 11); compiles `tools/java/*.java`; generates `abadia/k.java` from the `sv` column (non-ASCII
as `\uXXXX`), compiles it with
`javac --release 7` and proves with `javap` that fields, descriptors, flags, class flags (0x0031) and
major (51) equal the original (extra default constructor allowed, D2a); patches `j.class` for Å
(`PatchJ 125 -2 1`, md5 `f197f5a3…`), `w.class` (`w.t[4]`, `w.u[4]`) and `E.class` (`E.h[4]`) with
ASM, proving that every other method and every other array slot is unchanged; builds
`res/fuente.png` (own PNG writer, PLTE/tRNS copied verbatim), `res/letras` (glyphs appended at EOF)
and `res/de/pergamino1|2` (byte map, CR lines, `0x1A`; every line's ink edge ≤ 244; no blank page and
no trailing whitespace-only lines); font cells may be added only in the original blank cells and
80..82 (a cell ≥ 83 is drawn for codes ≥ 128 that other languages use); glyph JSON keys must be
canonical (cell `"80"`, not `"080"`; slot `"5B"`, not `"5b"`) and no object may repeat a key;
rebuilds the seven Swedish images, which are not in git, from `work/inputs/<key>/` (step 8a, above:
`tools/images/inputs.py`, then the seven `tools/images/build_*.py`; only for the default `--assets`,
and not with `--no-image-rebuild`); copies the images (size/colour type checked, the pixel data
fully inflated and decoded, and WARNINGs for the FORMAT §6.3/§6.4 rules: 1-bit alpha in
`loading.png`, nothing in the moon window x ≥ 250, y < 100 from `manuydani` on, `pulsa` transparent
outside its text band, `marcador` changed only in the day-word area, and any image still
pixel-identical to the English original; `logo.png` = es copy); rebuilds the jar with the original
entry order, compression and dates; verifies k/j/w/E with ASM `CheckClassAdapter` and by loading and
linking them under `-Xverify:all` on JDK 11 and JDK 8 (a broken-frame `j.class` is the negative
control that must be rejected), and compares the runtime values of `k` and `w` with the TSV; then
writes `game/` (original launchers and PDFs, the jar, `TheAbbeyOfCrimeExtensum(Swedish).sh/.bat`
made from the English launcher with ` en` → ` de`, and `User's manual (Swedish).pdf` when
`manual/Användarmanual.pdf` exists) and `work/build/manifest.json` (sha256 of every
game file and changed jar entry). Two runs with the same inputs give byte-identical output.

## Check

```sh
uv run tools/lint_strings.py [TSV] [--placeholder] [--ref REF] [-q]
                                                     # string rules only (FORMAT §1.13); exit 1 on errors,
                                                     # 2 if the TSV or REF cannot be read; --ref is the
                                                     # reference table (default tools/data/context.tsv),
                                                     # -q prints errors only
                                                     # (an empty label f[3..7] is allowed: GLOSSARY §6.3 f[5] = "";
                                                     # a b row equal to its es/en hour is untranslated, except
                                                     # ' SEXT  '; a b note starting 'bytes=...', if any, must equal
                                                     # the sv cell's bytes; the build takes the bytes from the cell)
uv run tools/check_glossary.py [-q] [--only g:52,54] # strings + parchments against translation/glossary.tsv
                                                     # (also --strings, --glossary, --perg1, --perg2; exit 1 on errors)
uv run tools/render_strings.py                       # all Swedish strings of game/ -> screenshots/strings/de/
uv run tools/render_strings.py --lang fr             # another language from the patched jar
uv run tools/regress.py                              # es en it fr pl: pristine vs patched, pixel-identical
```

Rules worth knowing before editing a string (FORMAT §1.7, §1.8, DECISIONS D12, D13):
- **Remigio's walk:** `lint_strings.py` caps g157 at **215** ticks, from the walk window measured in
  Phase E (220–223 ticks until g158 interrupts it); g158 ≤ 96 (≤ 129 after g157), g159 ≤ 211,
  g51 ≤ 77. The g157 cap assumes that g49 leaves no `bR` (its last page needs a budget of 40 or
  more; the Swedish leaves 0), which the lint does not check (FORMAT §1.8).
  `uv run tools/translate_tool.py pages "TEXT"` prints a draft's pages and ticks.
- **The ▶▶ marker:** the visible part of line 2 must stay ≤ 34 glyphs on every page. The lint does
  not check this; `render_strings.py` passes the harness warning `line 2 has 35 chars … overlapped by
  the blinking continue-marker` through, and the Swedish report must have none
  (`screenshots/strings/de/report.txt`).

State on the shipped TSV (jar `43846c9e…`; Phase F final verification: `work/phaseF/render_r1.log`,
`regress_r1.log`, and `render_r2.log`, `regress_r2.log` after its rebuild): lint 0 errors (1
warning: g126's space before its second marker, as in es); `check_glossary.py` 0 errors, 1 warning,
13 manual checks (variants, checked by hand); render 0 errors (9 expected warnings); `regress.py`
OK, 3711 frames.

`render_strings.py` (options `--game DIR` (default `game/`) or `--jar JAR`, `--lang`
(es en it fr de pl, default de), `--out` (default `screenshots/strings/<lang>/`), `--strings`,
`--perg1`, `--perg2`, `--placeholder`, `--ref-lang` (default es, or en for es), `--no-lint`,
`--no-source-check`, `--java` (default `java`)) runs the lint, renders with the
game's own code (message pages, pause-menu states, save slots, end screen, HUD hours, both
parchments; see `tools/harness/HARNESS.md`), checks that the jar's strings (every rendered one, plus
the never-drawn window title `E.h[4]` read from `E.class`) and parchments equal
`--strings`/`--perg1`/`--perg2` (so a source edited after the build is reported), and that the
parchment emulator `tools/letras.py` is pixel-identical to the real code. Exit 1 on any missing
glyph, layout error, lint error or mismatch. `regress.py` (options `--game DIR` (default `game/`)
or `--jar JAR` for the patched jar, `--pristine JAR` (default `original/TheAbbeyOfCrimeExtensum.jar`),
`--langs` (default `es,en,it,fr,pl`), `--out` (default `work/regress/`), `--java`) also checks that
only `abadia/{k,j,w,E}.class`, `res/fuente.png`, `res/letras` and `res/de/**` differ from
the original jar, that fuente cells 0..79 are unchanged except originally blank cells (74 today),
that the original letras bytes are unchanged except the six slot pointers (12 bytes), and that no
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
build reads them), `width "LINE"`, `pages FILE OUTDIR --text [--res DIR]` (`DIR` holds the
original `pergamino.png`, e.g. `work/inputs/<key>/jar/res`; the default is `work/jar/res`),
`encode`, `dump`.

## Edit the translation

`translation/strings_sv.tsv` is the source of truth; edit it directly, or round-trip rows through
a chunk file so that `check` can lint them with the glossary and timing:

```sh
uv run tools/translate_tool.py extract g52,g54 work/edit.json   # TSV rows -> chunk file
#   edit the "sv" (and "note") fields in that file
uv run tools/translate_tool.py check work/edit.json             # lint + glossary + ticks for those rows
uv run tools/translate_tool.py apply work/edit.json             # rows -> back into the TSV
uv run tools/build.py && uv run tools/render_strings.py  # rebuild, then render and compare
```

`merge` (the Phase C step that rebuilt the whole TSV from `work/phaseC/chunks/`) is guarded: it
refuses once the TSV is newer than every chunk file, because the Phase E and F fixes live only in
the TSV. `--force` overrides that and would discard them. The guard compares only file times:
editing any chunk file (c01–c12, u01, ui) lifts it, and `merge` then still rewrites every row from
the chunk files, so every Phase E and F fix, outside that chunk too, goes back to the Phase C
text. Use `extract`/`apply` instead. Other commands: `show CHUNK|g52,g54` (source rows
with es/en/fr/it, es pages and glossary rows), `pages "TEXT"`, `gameorder [--sv-only]` (every used
`g` string in rough game order, for reading), `plan`, `letras`. Strings changed this way are checked
by the harness render, which equals live play (FORMAT §9 question 9). Their language review is
separate: Phase F ran the Phase C editor, blind back-translation and meaning loop on such a chunk
file (`work/phaseF/e01.json`, and `work/phaseF/ui_review/x01.json` for the UI rows);
`docs/TRANSLATION_REVIEW.md` records every review pass and DECISIONS D17 summarises it.

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
| `data/context.tsv` | byte copy of `work/phaseA/context.tsv` (row keys, es, en, used/dead); the lint's `--ref`. Its `max_len` column is the Phase A value (g157 `keep <=232 ticks`, no line-2 rule); the current limits are g157 ≤ 215 (D12) and visible line 2 ≤ 34 (D13), and against this table only the keys, es and en are enforced (FORMAT §1.11) |
| `run_headless.sh`, `drivers/` | live game runs on a private Xvfb (FORMAT §7; needs the *Runtime runs* prerequisites above, Xvfb in `tools/xvfb-root/` or `XVFB_BIN`); a driver is stopped after `DRIVER_TIMEOUT` (default 1800 s), so `interactive.sh MAX` with MAX above that needs `DRIVER_TIMEOUT` raised too |
| `headless_lib.sh` | the drivers' helpers (`shot`, `tap`, `hold`, `wait_stable`, `check_invisible`, `audio_level`, …); `audio_level` measures the null sink with `parec \| od \| awk` and no longer calls `python3` (Phase E) |
| `translate_tool.py` | translation helper: `extract`/`apply` between the TSV and chunk files, `check`, `pages`, `show`, `gameorder`, and the guarded `merge` (see *Edit the translation*) |
| `images/build_*.py`, `fraktur.py`, `script_och.py`, `preview_intro.py` | the seven Swedish image builders (run by step 8a), their kits `fraktur.py` and `script_och.py` (imported by the builders), and `preview_intro.py` (preview only, writes to `work/phaseD/preview/`, not part of the build) |
| `images/inputs.py`, `images/inventory/` | the builders' read-only inputs, made from `original/` alone (see *Inputs* above) |
| `check_glossary.py` | strings and parchments against `translation/glossary.tsv` (page breaks and parchment line wraps are ignored when matching) |
| `manual/build_manual.py` | the Swedish user manual (DECISIONS D15): `uv run tools/manual/build_manual.py` writes `manual/Användarmanual.docx` (python-docx; Junicode regular and bold embedded), converts it with `soffice --headless --convert-to pdf` (private profile in `work/phaseF/lo_profile/`), adds the PDF's URI link annotations with PyMuPDF (LibreOffice 7.3 drops the `.docx` hyperlinks on export) and checks them and the searchable headings. `--no-pdf`, `--links-only`. Reads `translation/strings_sv.tsv`, `pergamino1_sv.txt`, `screenshots/runtime_sv/` and the English PDF in `original/`; needs Junicode, LibreOffice and poppler-utils |
| `drivers/manual_menu.sh` | `run_headless.sh` driver for the manual's menu picture: the pause menu opened before anyone speaks (`screenshots/runtime_sv/49_menu_no_dialogue.png`) |
| `review_record.py` | regenerates `docs/TRANSLATION_REVIEW.md` from the workflow journals in `~/.claude/projects/…/subagents/workflows/` and from `work/phaseF/ui_review/x01_result.json`. The journals are outside the project; once they are cleaned up, the committed file is the only copy and must not be regenerated |

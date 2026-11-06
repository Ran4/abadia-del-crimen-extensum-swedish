# CLAUDE.md

Swedish translation of *La Abadía del Crimen Extensum* (Pazos & Celemín, 2016, a Java 7 AWT
game). The Swedish text lives in the game's unused language slot `de`. `README.md` is the
player-facing description, in Swedish. This file covers how to work on the project.

Reference docs, all in English:

- `docs/FORMAT.md`: the game's data formats and limits. Rules are cited as §N.N.
- `docs/DECISIONS.md`: decisions that change or extend the original plan, cited as D1, D2, ….
- `docs/GLOSSARY.md`: terminology and the style guide (forms of address, names, hours, fixed phrases).
- `tools/README_tools.md`: every tool, flag and build step, in detail.
- `tools/harness/HARNESS.md`: the rendering harness that `render_strings.py` uses.
- `implementation_prompt.md`: the original brief. Its *Ground rules* still apply.

## Ground rules

- **Personal use only.** The repo has a GitHub remote (`origin`). Push only when the user asks.
  Never commit, upload or publish the patched jar, the original assets or anything derived from
  them. `.gitignore` keeps those out of git (see *Never commit game images* below).
- **Never put a window on the user's screen, and never make a sound.** Never run the launchers or
  `java -jar` on `DISPLAY=:0`. Live runs always go through `tools/run_headless.sh` (see below).
  The build and the checkers run Java with `DISPLAY` unset and `-Djava.awt.headless=true`. The
  manual is converted with `soffice --headless`.
- **Kill only what you started**, by PID. Other tools on this machine run their own `Xvfb`
  processes, so leave those alone. Never use `pkill -f <pattern>`: it also kills your own shell
  whenever the pattern is on its command line.
- **`original/` is read-only.** It holds the pristine download. The build reads from it and never
  writes to it.
- **Other languages must stay pixel-identical.** You may only *add* glyphs, in originally blank
  font cells or in cells 80..82. Never change an existing glyph or its index. `regress.py` checks
  this.
- **Python always runs through `uv run`** (PEP 723 inline dependencies). Never call `python3`
  directly, and that includes the shell harness.
- **Translate from the Spanish.** Use the other languages only to check meaning. Never look up or
  copy from the published Swedish edition of *Rosens namn* or from the film's Swedish subtitles.
- **Generated directories:** `game/` and `assets_sv/res/` are rebuilt on every build, so never
  edit them by hand. `game/` is wiped and recreated, keeping only `savedata.bin`. The build
  refuses to run if `game/` holds files it did not write.
- **`work/` is the verification archive** (DECISIONS D14). It holds the run logs and raw shots
  that `docs/FORMAT.md` and `screenshots/**/INDEX.md` cite, plus the Phase A/C data that
  `translate_tool.py` reads. The build and the checkers work without it, but do not delete it.
- **Never commit game images.** `original/`, `work/`, `game/`, `assets_sv/res/`,
  `tools/xvfb-root/` and the PNGs in `screenshots/` are git-ignored. They contain or derive from
  the original art. Only their text indexes and reports are tracked.
- **Do not regenerate `docs/TRANSLATION_REVIEW.md`.** `tools/review_record.py` builds it from
  workflow journals outside the project. Once those are cleaned up, the committed file is the only
  copy.

## Build

```sh
uv run tools/build.py
```

Rebuild after any change in `translation/`, `assets_sv/glyphs/`, `assets_sv/image_src/` or
`tools/images/`. Only one build can run at a time.

**Prerequisites** (none of these are in git):

- `uv`
- JDK 11 (`java`, `javac` and `javap` on the PATH)
- JDK 8 at `/usr/lib/jvm/java-8-openjdk-amd64`. The verification step uses it, and the build fails
  without it.
- The ASM jars in `tools/` (`asm-9.7.1.jar`, `asm-tree-9.7.1.jar`, `asm-analysis-9.7.1.jar`,
  `asm-util-9.7.1.jar`), from Maven Central. `tools/README_tools.md` lists their URLs and sha256
  sums.
- `original/` with the original jar, launchers and PDFs

**The build checks, among other things:**

- the sha256 of the original jar (a mismatch only warns);
- the string lint, before anything is built (an error stops the build);
- that the generated `abadia/k.class` has exactly the original's fields, flags and class version;
- that the patches to `j.class` (Å), `w.class` ("DAG", "TOM") and `E.class` (window title) change
  nothing else;
- that every parchment line fits the page width;
- the size and format of the seven Swedish images, which are regenerated from the original and
  `assets_sv/` on every run unless you pass `--no-image-rebuild`;
- that the patched classes load and link under `-Xverify:all` on both JDK 11 and JDK 8;
- that the strings in the finished jar equal the TSV.

The output is `game/` plus `work/build/manifest.json`. The same inputs give byte-identical output.
If any check fails, `game/` is left untouched. All flags are listed in `tools/README_tools.md`.

## Editing the translation

| File | Contents |
|---|---|
| `translation/strings_sv.tsv` | Every in-game string, the source of truth. The Swedish text is in column `sv` |
| `translation/pergamino1_sv.txt`, `pergamino2_sv.txt` | The intro and ending parchments (UTF-8, one text line per parchment line) |
| `assets_sv/glyphs/` | Added glyphs: `fuente_add.json` (game font) and `letras_add.json` (parchment hand) |
| `assets_sv/image_src/` | Hand-drawn letters for the images, as text files |
| `tools/images/` | Builders for the seven Swedish images (run by `build.py`) |
| `translation/glossary.tsv` | The glossary in machine-readable form, for `check_glossary.py` (the build does not read it) |

**String rules.** Details are in `docs/GLOSSARY.md` and in `docs/FORMAT.md` (§1.4 and §1.13 for
strings, §4.5 and §4.7 for parchments).

- Strings are written in CAPITALS. The one exception is the window title `E.h[4]`.
- Speaker codes `@N` must match the Spanish exactly.
- Inside a line, `_` starts a new page and `*` a new line. Spaces count toward the length.
- Stay within the `max_len` column. A few lines have a tick budget instead, which the lint checks
  (DECISIONS D12). For example, Remigio's walk caps g157 at 215 ticks.
- Line 2 of every page may show at most 34 glyphs, because the blinking ▶▶ marker covers the 35th
  (DECISIONS D13). **The lint does not check this.** Run `render_strings.py` and make sure
  `screenshots/strings/de/report.txt` has no "continue-marker" warning.
- The parchment hand has only a–z, A–Z, å ä ö Å Ä Ö, a few accented letters (é, í and ñ among
  them, which the credits need), space, `, - . : ;` and the digits 1, 2, 3 and 7. Spell numbers
  out.
- The game does not wrap parchment lines, so break them by hand. A page holds 11 lines, and the
  ink may reach at most x = 244. Measure with `letras.py check` (below).
- `München` cannot be written on the parchment, because the hand has no ü. It became `Bayern`
  instead (D10).

**Workflow.** Edit the TSV directly, or round-trip rows through a chunk file so that `check` can
lint them against the glossary and the timing:

```sh
uv run tools/translate_tool.py extract g52,g54 work/edit.json   # TSV rows -> chunk file
#   edit the "sv" (and "note") fields
uv run tools/translate_tool.py check work/edit.json             # lint + glossary + ticks
uv run tools/translate_tool.py apply work/edit.json             # rows -> back into the TSV
uv run tools/build.py && uv run tools/render_strings.py
```

**Never use `translate_tool.py merge`.** It rebuilds every row from the Phase C chunk files and
throws away every Phase E and F fix.

**Window title.** `E.h[4]` is "La Abadía del Crimen Extensum" (D6). Before you change it, add a
word from the new title to `TITLE_RE` in all three of `tools/run_headless.sh`,
`tools/headless_lib.sh` and `tools/lint_strings.py`. Otherwise the harness cannot find the window,
and the lint keeps warning.

## Checks

```sh
uv run tools/lint_strings.py      # string rules only, no build needed
uv run tools/check_glossary.py    # strings and parchments against translation/glossary.tsv
uv run tools/render_strings.py    # renders every Swedish string from game/ with the game's own
                                  # code into screenshots/strings/de/; fails on a missing glyph
uv run tools/regress.py           # es en it fr pl: the original and the patched game must be
                                  # pixel-identical
```

`render_strings.py` and `regress.py` read the *built* game, so run them after `build.py`.
`render_strings.py` notices when the TSV or the parchment files change after a build. It does not
notice changed glyphs or images, so always rebuild first. Both checkers can run alongside each
other and alongside `build.py`. `tools/README_tools.md` records the expected warning counts on the
shipped TSV.

Helpers:

```sh
uv run tools/translate_tool.py pages "@0 TEXT"     # how the game splits a line into pages,
                                                   # and how many ticks it takes
uv run tools/letras.py check translation/pergamino1_sv.txt --text \
    --letras game/TheAbbeyOfCrimeExtensum.jar      # measures the ink edge of each parchment line
```

## Running the game headless

```sh
tools/run_headless.sh <gamedir> <lang> <driver.sh> [driver-args...]   # lang: es en it fr de pl
```

The game runs on a private Xvfb (`-displayfd`, unix socket only), never on `:0`. `check_invisible`
queries `:0` read-only, once the window is up and again after the driver, to prove no game window
is there. Audio is
silenced three ways: a private PulseAudio/PipeWire null sink, a private ALSA config that points at
it, and `bwrap` hiding `/dev/snd` from the JVM. A watchdog kills the game if any of its audio
reaches another sink.

Each run gets its own `work/runs/<stamp>-<lang>-<pid>/`. It holds `game.log` (java output),
`evidence.log` (invisibility and silence evidence), `driver.log` and `shots/`. Set `SHOT_DIR` or
`RUN_DIR` to override those paths. Other env knobs (`DRIVER_TIMEOUT`, default 1800 s;
`WINDOW_TIMEOUT`; `JAVA_BIN`; `XVFB_BIN`; …) are listed in the header of `run_headless.sh`.

A driver is a bash script. It gets `DISPLAY`, `GAME_PID`, `WIN_ID`, `SHOT_DIR`, `RUN_DIR` and
more, and runs `source "$HEADLESS_LIB"` to load the helpers in `tools/headless_lib.sh`: `shot
NAME` (a native 320x208 PNG), `burst`, `tap KEY [secs]`, `hold`, `keys`, `wait_s`, `wait_stable`,
`dlog`, ….

Drivers in `tools/drivers/`:

- `pristine_tour.sh`: intro → start of the parchment → HUD → pause menu → end screen (about
  11 minutes). The header lists its knobs (`PHASES`, `PARCH_FULL=1`, `GAMEOVER=1`, …).

  ```sh
  SHOT_DIR=work/runs/my-tour tools/run_headless.sh game de tools/drivers/pristine_tour.sh
  ```

- `interactive.sh [MAX]`: keeps the game running so you can drive it from other shells. Run
  `source $RUN_DIR/env.sh` to get the variables and helpers, and `touch $RUN_DIR/stop` to end the
  session. For more than 1800 s, raise `DRIVER_TIMEOUT` as well.
- `manual_menu.sh`: takes the pause-menu picture for the manual.
- `probe_timeline.sh [SECS] [IV]`: no input, a screenshot every IV seconds, for measuring the
  intro timeline. `probe_parchment.sh` is an early probe, superseded by
  `PHASES=parchment PARCH_FULL=1` on the tour.

Timing: "Press to start" appears about 45 s after launch (drivers wait `INTRO_SECS=52`). Space or
Enter skips the intro pictures. Space skips the intro parchment while it is still being written,
and a finished parchment waits for space.

**Prerequisites:** `bwrap`, `xdotool`, `xwd`, `xwininfo`, ImageMagick 6 (`convert`, `identify`),
`pactl` and `parec`, plus Xvfb unpacked into `tools/xvfb-root/`, because the machine has no system
Xvfb. Unpack it once, without sudo:

```sh
(cd tools && apt-get download xvfb && dpkg-deb -x xvfb_*.deb xvfb-root)
```

Under Java 11 the game prints two harmless stack traces at startup, and so does the original.

## User manual

```sh
uv run tools/manual/build_manual.py          # --no-pdf: write only the .docx
```

The script writes `manual/Användarmanual.docx` with python-docx and embeds Junicode. It converts
the file with `soffice --headless --convert-to pdf`, using a private profile in
`work/phaseF/lo_profile/`. Then it adds the PDF's link annotations with PyMuPDF, because
LibreOffice drops them on export. Finally it checks that every page has its links and that the
headings are searchable.

The menu lines and hours come straight from `translation/strings_sv.tsv`, and the prologue page is
the intro parchment. The pictures are from `screenshots/runtime_sv/`. The menu picture is made with
`tools/drivers/manual_menu.sh`. The script needs LibreOffice, the Junicode font and poppler-utils
(`pdfimages`, `pdftotext`).

The PDF is the reference for how the manual should look. The next `build.py` copies it into
`game/` as `User's manual (Swedish).pdf`. Neither manual file is in git (D14, D15).

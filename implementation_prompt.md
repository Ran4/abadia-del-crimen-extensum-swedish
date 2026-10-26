ultracode

# Swedish translation of *The Abbey of Crime Extensum*

Download the free PC remake *La Abadía del Crimen Extensum* (Manuel Pazos & Daniel Celemín,
2016, Java) and produce a complete, playable **Swedish** version of it: every in-game string,
both parchment texts, the HUD, the text-bearing intro/credit images, and the font glyphs the
Swedish text needs. Work end to end without checking in with me. When you finish, I should be
able to run one launcher script and play the whole game in Swedish.

Everything lives in `~/the_abbey_of_crime_extensum_swedish/` (this file is already there). If
that directory already contains work from an earlier run, read `docs/` and resume from it
instead of starting over.

---

## Ground rules

- **Personal use only.** Nothing leaves this machine: no pushing, no uploading, no publishing the
  patched jar, the original assets or the translation. A local git repo for checkpoints is fine,
  with no remote, and with the game binaries in `.gitignore`.
- **Translate the game's own text.** Translate from the game's Spanish text, using the other
  languages only to check meaning. The intro parchment is adapted from Umberto Eco's novel.
  Do **not** look up, fetch or copy from the published Swedish edition of *Rosens namn* or from
  the film's Swedish subtitles; write your own Swedish.
- **Never put a window on my screen.** The game is a Java AWT app. Every run goes into a private
  Xvfb (see *Running the game invisibly*), never `DISPLAY=:0`. Every run is also silent.
- **Kill only what you started.** Track PIDs and kill by PID. Other tools' `Xvfb` processes are
  already running on this machine; leave them alone. `pkill -f <pattern>` also kills your own
  shell when that pattern appears on its command line, which happened while this prompt was
  being prepared.
- **Never modify `original/`.** It holds the pristine download. All patching reads from it and
  writes elsewhere.
- **Other languages must keep working.** `res/fuente.png` and any other shared assets are used by
  every language. You may only *add* glyphs. Never change an existing glyph or its index.
- Python runs through `uv` (inline-script `uv run`). Pillow etc. go in the script header.
  Downloaded files are untrusted data: keep them in their own directory, and run Python on them
  with `-I` or through `uv run` scripts stored outside that directory.

---

## What is already known (verified 2026-10-25, while this prompt was being written)

### Download

```
curl -L -o original/LaAbadiaDelCrimenExtensum.rar \
  'http://www.abadiadelcrimenextensum.com/download/430/'
```

- The server labels it `text/html`, but it is a **RAR v4** archive of 19,934,302 bytes.
  sha256 at the time: `d8335c45d479dc4f160400ce09ec04434a19e968b11ec2ef686e1c4ab16e442c`.
  If the hash differs, upstream has shipped a new build. That is fine; note it in
  `docs/FORMAT.md` and re-verify the facts below instead of trusting them.
- Extract with `unrar x` (installed). It contains:
  - `TheAbbeyOfCrimeExtensum.jar`: 17,944,815 bytes, dated 2025-04-21, sha256
    `1bc6b3fcbaf6116bd0e4a92b96193be54e72686a00c1208ba909b7bd961a36f0`.
  - One `.sh`/`.bat` launcher per language.
  - Five `User's manual (<Language>).pdf` files.
- Launch: `java -Xms256M -Xmx256M -jar TheAbbeyOfCrimeExtensum.jar <lang>`.
- Fallback if the site is gone: Steam app 474030 (free; Steam is installed). The Steam client
  opens a window, though, so stop and tell me rather than starting it yourself.

### Code

- The jar is obfuscated: `Main-Class: abadia.Abadia`, class files major version **51** (Java 7).
  The machine has OpenJDK 11 (`java`, `javac`, `jar`) and OpenJDK 8.
- The language codes are a static `String[] u` in `abadia.Abadia`, in this order:
  `{es, en, it, fr, de, pl}`.
- **Text tables:** one class per language, each with exactly **185 strings**. Each has
  `public static final String[] a` (the strings) and `static final byte[] b`.

  | lang | class | notes |
  |---|---|---|
  | es | `abadia.m` | the original language |
  | en | `abadia.l` | |
  | it | `abadia.o` | |
  | fr | `abadia.n` | |
  | de | `abadia.k` | hidden, see below |
  | pl | `abadia.p` | added in 2025, the most recent precedent for adding a language |

  - `abadia.j` picks the `a` table by language.
  - `abadia.v` loads `res/fuente.png` and picks the `b` array by language. `b` is very likely
    the per-language map from special characters to glyphs. Confirm this.
  - The classes that read the language array `u` are `Abadia`, `r`, `v`, `w`, `y`.
- **`de` is an unused spare slot.** No launcher offers it.
  - Every `res/de/*` file is byte-identical to `res/en/*`.
  - Its table `abadia.k` is mostly Spanish, with a few German strings. It contains Ä, Ö, Ü and
    ß, so some umlaut handling probably exists on that path already.
- In-game strings are **all UPPERCASE**, with accented capitals:
  - es: Í É Á Ó Ú Ñ Ü ¿ ¡
  - fr: É È À Ê Î Û Â Ô Ç Ù Œ
  - pl: Ł Ę Ś Ż Ą Ć Ź Ń Ó
- `res/fuente.png` is 640×8: **80 glyphs of 8×8**. It is the in-game font, shared by every
  language.

### Parchment

- `res/<lang>/pergamino1` is the intro parchment and `res/<lang>/pergamino2` the ending one.
  Both are plain text with CR (`0x0D`) line breaks.
- Encodings:
  - es, en, fr and it are Latin-1/cp1252. fr and it use `0x92` for ’.
  - pl contains UTF-8 sequences.

  Find out exactly how the reader decodes each language.
- `res/letras` (5,564 bytes) is a binary table that starts with 16-bit little-endian offsets.
  It is probably the glyph data for the handwritten parchment font. Check whether it can draw
  å, ä, ö and Å, Ä, Ö, and how Polish and French accents are drawn.

### Images

- **Per-language images**, which differ byte-wise between languages and therefore contain text:
  - `res/<lang>/marcador.png`: the HUD, 320×32.
  - `res/<lang>/intro/`: `loading.png`, `logo.png`, `manuydani.png`, `novela.png`,
    `pacoyjuan.png`, `pelicula.png` and `pulsa.png`. All are 320×208, and several are indexed
    PNGs; keep each file's mode and palette.
  - `logo.png`: es and it have their own; en, fr, de and pl share one.
  - `pulsa.png`: es and pl have their own; en, fr, it and de share one.
- **Language-neutral images:** `intro/{luna,monje,niebla,ventana}.png`.
- **Voices:** `res/sound/voces/*.ogg` holds one set of per-character clips. Re-voicing is out of
  scope.

### Local environment

- **Xvfb is not installed and there is no sudo**, but this works (tested; it came up on :97 at
  1280×800×24 and `xdpyinfo` answered):
  ```
  apt-get download xvfb && dpkg-deb -x xvfb_*.deb xvfb-root   # → xvfb-root/usr/bin/Xvfb
  ```
- Audio: PulseAudio on PipeWire, with `pactl` available.
- Also available: `xdotool`, `xwininfo`, `xwd`, ImageMagick 6 (`convert`, `import`; there is no
  `magick`), `ffmpeg`, `unrar`, `7z`.
- The X session is X11.

---

## Decisions already made (change one only if investigation proves it unworkable, and record why in `docs/DECISIONS.md`)

1. **Swedish takes over the spare `de` slot.**
   - Replace `abadia.k`'s strings and `b` map, and every `res/de/*` file.
   - Ship a launcher `TheAbbeyOfCrimeExtensum(Swedish).sh` that passes `de`.
   - This needs no changes to dispatch code.
   - First check `Abadia`, `r`, `v`, `w`, `y`, `j` for anything special-cased on the `de` index
     or code. Only if `de` is truly unusable, add a real `sv` code by bytecode-patching
     (ASM, or equivalent).
2. **Patch the text by regenerating `abadia.k` from source, not by hex-editing.**
   - It is only static arrays. Decompile it with CFR or Vineflower (download the jar into
     `tools/`), then write a generator that emits `k.java` from the translation sources.
   - Compile with `javac --release 7`.
   - Prove with `javap -p -s` that the new class has exactly the same fields, descriptors and
     modifiers as the original.
3. **Logo:** use the Spanish `logo.png`. *La Abadía del Crimen* is the game's real name, and
   this avoids redrawing a piece of title art. Every other text-bearing image gets a Swedish
   version.
4. **Translate from the Spanish table (`m`) and `res/es/*`.**
   - Use en (`l`), fr (`n`) and it (`o`) at the same index to settle ambiguity.
   - The `de` table is not a source.

---

## How to run it (ultracode: orchestrate with workflows, stay in the loop between them)

Run this as a sequence of workflows, one per phase below. Read each phase's results before you
write the next workflow. Phases A and E are where mistakes get expensive: verify adversarially
there.

### Phase A: Download and understand (do the download inline first, then fan out readers)

Download, check the hash, extract into `original/`, and copy the extracted files to a working
tree. Then fan out parallel readers over the separable questions:

- **The text table and its markers.**
  - Find every control code, placeholder, padding or special character convention in `a`. Do
    this by aligning all six tables index by index.
  - Find what each of the 185 indices is for: scrolling message, HUD hour name, day label, menu
    item, etc.
  - Find the **maximum length** each context allows, by measuring field widths in pixels and
    glyphs.
  - Find whether any game logic waits on a message to finish scrolling.
- **The font path.** How `abadia.v` maps characters to `fuente.png` glyphs through `b`:
  - Which of the 80 slots are free or unused.
  - Whether the glyph count comes from the image width.
  - Whether Ä and Ö already exist.
  - Exactly what must be added for Å, Ä and Ö.
- **The parchment path.**
  - How `pergamino1`/`pergamino2` are decoded.
  - How `letras` encodes glyphs and accents.
  - How lines wrap and what limits the line width.
  - What is needed for å, ä, ö (and capitals, if the text needs them).
- **The `de` slot.** Does anything treat `de` specially (Decision 1)?
- **The images.**
  - For each per-language image: which text it shows, and in which pixel font.
  - Gather a glyph inventory for each image font from all language versions, since the
    accents present in fr, es and pl versions give you diacritics to copy the style of.

Write the merged result to **`docs/FORMAT.md`**: a precise, checked description that later
phases build on. Have at least one independent agent try to refute each load-bearing claim
before you rely on it, especially the `b` map semantics, the length limits and the parchment
encoding.

### Phase B: Glossary and style guide (one strong agent plus a critic, before any translation)

Write **`docs/GLOSSARY.md`**, covering:

- **Register.** Natural, idiomatic Swedish with a slightly elevated, historical tone, as in a good
  Swedish translation of a medieval novel. No anglicisms, no hispanicisms.
- **Address.** One decision on *du*/*ni* and on titles (*broder*, *fader*, *abboten*), applied
  consistently per pair of speakers.
- **Names.** A fixed Swedish form for every character name and place, using the game's own
  names, and Swedish conventions for Latin and medieval names.
- **Latin** stays Latin (OBSEQUIUM, Latin quotations).
- **Canonical hours.** These must fit the measured HUD field.
  - The game uses Noche, Prima, Tercia, Sexta, Nona, Vísperas and Completas.
  - Swedish candidates: NATT, PRIM, TERS, SEXT, NON, VESPER, and KOMPLETORIUM / COMPLETORIUM /
    NATTBÖN.
  - Pick the forms that fit and stay unambiguous.
- **Day label** (DAG) and any other HUD or menu term.
- **Recurring phrases** that must always be rendered the same way.

### Phase C: Translate (fan out in parallel)

**The 185 strings**, in chunks of roughly 20–25:

- Each translator gets, for every index:
  - es, en, fr and it.
  - The context and max length from `FORMAT.md`.
  - The glossary.
- Each returns structured `{index, sv, note}`.
- Then, per chunk:
  - An independent **Swedish editor** pass: correctness, idiom, glossary use, length, markers
    preserved exactly.
  - A **blind back-translation** pass: back-translate the Swedish to Spanish without seeing the
    source, and compare it with the source to catch shifts in meaning.
- Loop each chunk until both passes are clean.
- Finally, one agent reads **all 185 strings in game order** for consistency of names, address
  forms, tense and tone.

**The parchments** (`pergamino1`, `pergamino2`) are prose:

- One translator and one editor each, looped until the editor passes them.
- Respect the line-width limit and the exact byte encoding the reader expects.
- Keep the original's line and paragraph rhythm.

Store everything as editable sources:

- `translation/strings_sv.tsv`, with columns `index`, `context`, `max_len`, `es`, `en`, `sv`,
  `note`.
- `translation/pergamino1_sv.txt` and `translation/pergamino2_sv.txt`.

### Phase D: Glyphs, images and build tooling (fan out in parallel with Phase C)

**In-game font.** Add the missing Swedish capitals (at least Å, plus Ä and Ö if absent) to
`fuente.png`:

- Match the existing pixel style. Build Å from A plus a ring in the style of the existing
  accents.
- Only fill unused slots or append; never touch existing glyphs.
- Wire them up through the Swedish `b` map.

**Parchment font.** Make the parchment able to draw å, ä, ö (and the capitals if used),
following the mechanism Polish and French already use.

**Text-bearing images.** These are `marcador.png` and the intro images `loading`, `manuydani`,
`novela`, `pacoyjuan`, `pelicula` and `pulsa`. Each gets a builder-and-critic loop:

- **Builder.** Compose the Swedish text from glyphs cut out of the existing language versions,
  so it is the identical pixel font. Compose diacritics from existing accent marks. Keep the
  image's size, mode, palette and layout.
- **Critic.**
  - View the original and the Swedish image side by side at 4× nearest-neighbour.
  - Reject any of these: mixed fonts, a different palette, misalignment, stray pixels,
    awkward line breaks, wrong Swedish.
- Loop until the critic passes, at most 6 rounds per image. If an image still fails after that,
  say so in the final report.

**Build tooling.** Write it in `tools/`:

- **`build.py`.** Builds `game/` from `original/` plus `translation/` plus `assets_sv/`:
  - Regenerates `k.java`, compiles it, and swaps the class into a copy of the jar.
  - Writes the Swedish `pergamino*` in the right encoding into `res/de/`.
  - Installs the images and the font.
  - Copies the remaining original files and writes the Swedish launcher.
  - Must be deterministic and idempotent.
- **`render_strings.py`, or preferably a small Java harness.** Draws every Swedish string the
  way the game draws it, into contact sheets in `screenshots/strings/`, and **fails on any
  character that has no glyph**.
  - Prefer calling the game's own drawing code on the patched jar through a classpath harness.
  - Fall back to a faithful reimplementation of `abadia.v` only if the obfuscated API makes
    that impractical.
- **`run_headless.sh`.** The recipe below.

### Phase E: Integrate and verify (adversarial; loop until clean)

1. **Static checks.**
   - `k` has exactly 185 strings.
   - Every index is translated: no leftover Spanish or English except deliberate Latin and
     names.
   - Markers and placeholders are identical to the source, index by index.
   - Every string is within its `max_len`.
   - Every character is mappable.
   - The other five language classes are byte-identical to the original.
   - `fuente.png` changes are additions only, checked pixel-diff against the original.
2. **Contact sheets.** Render every string. Then have a critic look at every sheet for glyph,
   clipping and overflow problems.
3. **Runtime, Swedish.**
   - Boot the patched game (`de`) invisibly and drive it with `xdotool`.
   - Capture screenshots of:
     - each intro and credit screen;
     - several frames of the intro parchment being written, including frames with å, ä, ö;
     - the press-key screen;
     - the in-game HUD (DAG + hour name);
     - the first in-game messages (the abbot's welcome at the start);
     - a couple of further interactions if you can reach them.
   - The run's stdout/stderr must show no exceptions.
   - If the ending parchment cannot be reached by playing, render it via the harness or by
     invoking its code path directly.
4. **Runtime, regression.**
   - Run the patched jar with `en`, `es` and `pl` at the same checkpoints as the pristine jar.
   - Every language that does not use the added glyphs must look identical. Diff the
     screenshots.
5. **Critic panel.** Several independent agents look at the full screenshot set and the full
   string table, each through a distinct lens:
   - Swedish language quality.
   - Visual and glyph fidelity.
   - Completeness: is any untranslated text left anywhere, in strings, parchments or images?
   - Does it actually run?

   Fix what they find, rebuild, re-run, and repeat until a round finds nothing new.

### Phase F: Deliver

- `game/`: the playable folder. Contents:
  - The patched jar.
  - All original files.
  - The original language launchers, untouched.
  - `TheAbbeyOfCrimeExtensum(Swedish).sh`, executable, passing `de`, in the same style as the
    existing launchers.
- `README.md`, in Swedish:
  - How to start the game.
  - The controls, in short (from the English manual).
  - What was translated, and what was not and why: logo, voices.
  - How to rebuild after editing `translation/`: `uv run tools/build.py`.
- `docs/FORMAT.md`, `docs/GLOSSARY.md`, `docs/DECISIONS.md`.
- `screenshots/`: the verification set.
- **Optional, only after everything above passes:** a Swedish user manual translated from the
  English PDF, written in the same register, as `.docx` plus `.pdf`.

Do **not** launch the game visibly at the end. Tell me the command instead.

---

## Running the game invisibly (`tools/run_headless.sh`)

```sh
# One-time: a private Xvfb, no sudo needed
(cd tools && apt-get download xvfb && dpkg-deb -x xvfb_*.deb xvfb-root)

# Start Xvfb on a free display; -displayfd prints the display number it picked
exec 3> tools/.xvfb_display
tools/xvfb-root/usr/bin/Xvfb -displayfd 3 -screen 0 1280x800x24 -nolisten tcp & XVFB=$!
# read the display number N from that file once it is non-empty

# Silence: route audio to a throwaway null sink
MOD=$(pactl load-module module-null-sink sink_name=abbey_mute)

( cd game && DISPLAY=:N PULSE_SINK=abbey_mute \
    java -Xms256M -Xmx256M -jar TheAbbeyOfCrimeExtensum.jar de ) > run.log 2>&1 & GAME=$!

# Drive and capture (always on :N)
DISPLAY=:N xdotool search --sync --name '.' windowfocus --sync   # there is no WM, so use windowfocus, not windowactivate
DISPLAY=:N xdotool key space
xwd -root -display :N | convert xwd:- screenshots/step_01.png

# Cleanup, by PID only
kill $GAME $XVFB; pactl unload-module "$MOD"
```

- Give the game time to load before the first capture.
- Also capture a few seconds of frames around animated parts, such as the parchment being
  written.
- **Prove it stayed invisible.** During the run:
  - `DISPLAY=:0 xdotool search --name 'Abad|Abbey'` must return nothing.
  - `pactl list sink-inputs` must show the java stream on `abbey_mute`.
- **If keys don't register:**
  - Check that the game window holds focus (`xdotool getwindowfocus` on `:N`).
  - Try `xdotool key --window <id>`.
  - As a last resort, use a `java.awt.Robot`-based driver inside the harness.

---

## Definition of done

- [ ] `game/TheAbbeyOfCrimeExtensum(Swedish).sh` starts the game in Swedish. The Phase E
      runtime screenshots show:
  - Swedish intro and credit screens.
  - A Swedish intro parchment, with å, ä and ö drawn correctly.
  - A Swedish HUD.
  - Swedish in-game messages.
- [ ] Every one of the 185 strings and both parchments are in Swedish and have passed the
      editor, back-translation and consistency passes.
- [ ] Every string renders with no missing glyphs (contact sheets in `screenshots/strings/`).
- [ ] en, es and pl are unaffected: no visible regression in their screenshots.
- [ ] `uv run tools/build.py` rebuilds `game/` from `original/` plus the sources, reproducibly.
- [ ] No window appeared on `:0` and no sound played at any point.
- [ ] Final report to me:
  - What was done and the command to play.
  - Anything left imperfect, stated plainly (e.g. an image whose critic loop ran out of rounds,
    a code path you could not reach at runtime).

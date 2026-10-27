# DECISIONS.md

The four decisions in `implementation_prompt.md` hold: Swedish takes over the `de` slot; `abadia.k` is
regenerated from source; the logo is the Spanish one; translation is made from es. This file records
only what Phase A showed must **change or be added** (D2a–D7) and the decisions taken later, in
Phases B–F (D8–D18), with the reason for each. Details and evidence are in `docs/FORMAT.md`; the
wording behind D8–D11 is in `docs/GLOSSARY.md`. D17 summarises the translation review passes,
whose full record is `docs/TRANSLATION_REVIEW.md`.

## D2a. Clarification of Decision 2 (regenerate `abadia.k`)
- `javac --release 7 -encoding UTF-8` on JDK 11 works and produces major 51, class flags 0x0031, and
  field flags identical to the original: `a` 0x19, `b` 0x18, `c d e f` 0x08, `g` 0x18 (VERIFIED).
- javac always adds a `public abadia.k()` default constructor. The original has only `<clinit>`.
- **Change:** the `javap -p -s` proof compares the **fields** (names, descriptors, flags), the
  class flags and the major version. It must allow that extra `<init>`.
- **Reason:** no javac setting removes the constructor, and nothing instantiates `k`.

## D3a. Addition to Decision 3 (logo)
- `res/de/intro/logo.png` = byte copy of `res/es/intro/logo.png`.
- **The Swedish `loading.png` also takes its title art from es** (rows y < 175, "La abadia del crimen
  extensum"). Only its bottom line, rows 181..193, gets new Swedish text.
- **Reason:** the en/de loading screen shows the English title art. Pairing it with the es logo
  would show two different titles. The decision's own rationale (the game's real name, no title
  art to redraw) applies here unchanged.

## D5. New: Å in the in-game font needs a bytecode patch of `abadia/j.class` and an appended ring glyph
- **What:**
  - Patch the private `j.a(IIILjava/awt/Graphics;)V` with ASM (`work/phaseA/proto_font/src/PatchJ.java`,
    args `125 -2 1`). The new switch keys are:
    - 197 Å and 229 å → a new block that draws A, then code 125 at y−2;
    - 228 → the Ä target;
    - 246 → the Ö target.
  - The new block gets an explicit F_FULL frame. No COMPUTE_FRAMES. The constant pool is unchanged.
    The expected output is 12092 B, md5 `f197f5a3e4b9d1c553ede4194efc75af`.
  - Append a ring glyph as cell 80 (x 640..647) to `res/fuente.png`, which becomes 648×8. It must
    stay **indexed** with the original PLTE/tRNS: palette 1/6 for ink, 53 for background.
- **Ring height:** dy −2. At dy −3 the ring touches the dialogue box border on line 1.
- **Verification:**
  - `ClassReader.accept(new CheckClassAdapter(cw, true), 0)`;
  - `-Xverify:all` on JDK 8 and 11;
  - a pixel regression of every other language.
- **HUD hour names:** these can use only precomposed glyphs, placed in blank cells
  (2, 46, 72–74, 76–79 = bytes 47, 91, 117–119, 121–124) or in appended cells 81–82 (bytes
  126–127, after the image is widened further; FORMAT §2.4, and `tools/build.py` allows cells up
  to 82). The hour bytes in `k.b` reference them. Example: the glossary's `NATTBÖN` uses a
  squashed Ö in cell 74, byte 119.
- **Reason:**
  - The prompt assumed `b` is a per-language char→glyph map that could "wire up" new glyphs. It is
    not: `b` holds the 7 HUD hour names as raw cells.
  - The only char→glyph map is the switch in `j`, which all languages share. Å is not in it and
    draws nothing.
  - No data-only route gives Å a proper accent above the cell. A precomposed cell squashes the A, and
    reusing the grave or circumflex glyph breaks French.
  - The patch changes no pixel for any other language (VERIFIED regression over all 1128 shipped
    strings, in white and black font).
- **Consequence:** `}` (code 125) draws a ring, so the string lint must forbid it.
- **Status (Phase D/E):** applied by `tools/build.py` steps 4 and 5. Step 4 runs the maintained
  port `tools/java/PatchJ.java` (same args `125 -2 1`, same output md5), not the Phase A prototype.
  The built `j.class` has the expected md5; the ring art is final (FORMAT §3.4); es, en, it, fr and
  pl render pixel-identically to the pristine jar (`tools/regress.py`, 3711 frames). VERIFIED.

## D6. New: patch the slot-4 strings that live outside `abadia.k`
- **Which strings:** `w.t[4]` (save-slot "DAY " word, currently Spanish `DÍA `), `w.u[4]` (empty
  slot, currently `VACÍO`) and `E.h[4]` (window title, currently German).
- **Mechanism:**
  - Replace the LDC that follows `ICONST_4` in `<clinit>` with a **new** constant, using
    `work/phaseA/refute_deslot_1/scripts/PatchTW.java` with `ClassWriter(reader, 0)`.
  - **Never edit** `w` CP #7 or #15 in place: Spanish index 0 shares them.
  - The patch is VERIFIED on JDK 8 and 11. Spanish is unchanged.
- **Length limits:**
  - `w.t[4]` ≤ 6 chars including its trailing space, e.g. `DAG `;
  - `w.u[4]` ≤ 15 chars.
- **Window title:** keep the game's real name `La Abadía del Crimen Extensum`, for the same reason
  as Decision 3. It also matches `TITLE_RE` in `tools/run_headless.sh` (line 56).
  - If a Swedish title is wanted instead, first add a word from it to `TITLE_RE` in **all three**
    copies: `tools/run_headless.sh` (line 56, hard-coded), `tools/headless_lib.sh` (the env
    default) and `tools/lint_strings.py` (`TITLE_RE`, used for the `E.h[4]` warning). Otherwise every
    Swedish runtime run times out finding the window, and the lint keeps warning.
- **Reason:** replacing `k` alone would leave Spanish words in the save/load menu and a German
  window title.
- **Status:** applied by `tools/build.py` step 4 with the maintained port
  `tools/java/PatchStrings.java` (a port of `PatchTW`, same method: a new constant, exactly one site
  per replacement, `ClassWriter(reader, 0)`): `w.t[4]` = `DAG `, `w.u[4]` = `TOM`, `E.h[4]` = `La
  Abadía del Crimen Extensum` (the Spanish title was kept). `render_strings.py` compares all three
  with the TSV; the filled and empty save slots were seen live (`screenshots/runtime_sv/INDEX.md`, files 26–27 and
  40–41). VERIFIED.

## D7. New: parchment å ä ö Å Ä Ö as a data-only `res/letras` extension
- **Placement:**
  - Append six precomposed glyphs to `letras` (first free address 0xBC93).
  - Point six **empty** table slots at them: Ä `0x5B`, Ö `0x5C`, Å `0x5D` (drawn red like all
    capitals), å `0x60`, ä `0x7B`, ö `0x7C` (drawn black).
- **Text files:** the Swedish `res/de/pergamino1|2` are written as raw bytes using those slot bytes.
  The byte map is in FORMAT §4.7. Lines end with CR, the file ends with `1A`, and no byte outside
  the whitelist is allowed.
- **No change** to `y.class`.
- **Glyph design (the Phase A requirement; the final glyphs are under Status):**
  - The capitals need a shorter body in rows 2..14 with the mark in rows 0–1. The prototype capitals
    are placeholders.
  - The lowercase prototypes are usable.
- **Reason:**
  - The parchment reader does no charset decoding. Every encoding of these letters either hangs
    (`Caracter: N` forever, which cannot be skipped in the ending), vanishes, or draws ą/ń.
  - Filling empty slots needs no code change. All 12 shipped texts give byte-identical drawLine logs
    with the extended `letras`, because no other language emits those bytes.
  - The prompt's "follow the mechanism Polish and French use" is not possible without a `y.class`
    patch. Those languages use composed drawLine overlays, and the set has no diaeresis or ring.
- **Status:** applied with final glyphs (`assets_sv/glyphs/letras_add.json`; the capitals got the
  shorter body: final bodies in rows 3..14, the Ä/Ö dots in rows 0–1, the Å ring in rows 0–2).
  Both parchments run through the real `y.a()` without a `Caracter:` line, and the intro was
  written live (FORMAT §4.7). VERIFIED.

## D8. NATTBÖN for COMPLETAS, with a precomposed HUD Ö
- **What:** HUD hour 6 (`k.b[42..48]`) is `NATTBÖN` = bytes `78,65,84,84,66,119,78`. Byte 119 draws
  `res/fuente.png` cell 74, blank in the original, which now holds a precomposed Ö: the cell-16
  diaeresis in row 0, the O of the shipped HUD Ó (cell 68) in rows 2–7
  (`assets_sv/glyphs/fuente_add.json`). In speech and parchment the hour is `NATTBÖNEN`
  (GLOSSARY §5.2).
- **Why a glyph, not the letter Ö:** U+00D6 is byte 214, a negative Java byte. The HUD draws
  nothing for it and the save label shows a blank. So the build never encodes U+00D6.
  `lint_strings.hud_bytes` maps the sv cell's Ö to byte 119 (A–Z and space as themselves), and the
  lint allows only those characters in a `b` row. The `bytes=` notes of the `hour_hud` rows in
  `translation/glossary.tsv` are reference byte lists (documentation only; nothing checks them
  against the build, which takes the bytes from the sv cell). If a `strings_sv.tsv` `b` note starts
  with `bytes=`, the lint requires it to equal the cell's bytes; none does today. Editing a note in
  either file changes nothing in the HUD.
- **Reason for the word:** the Swedish names of compline do not fit 7 plain cells legibly
  (`KOMPLETORIUM` is 12). `KOMPLET` would fit, but it reads as a misspelt `KOMPLETT` ("complete"),
  which misleads on a clock. `NATTBÖN` is a plain Swedish word, says what the hour is for (the abbot
  sends everyone to their cells), and the clock order VESPER → NATTBÖN → NATT is literally true.
- **Reason for cell 74:** a blank cell reachable as a byte needs no code change. 119 is not a switch
  key, so the save label draws the same cell through `j.a(int)` (`DAG 7 NATTBÖN`, 13 of 15 glyphs).
- **Cost:** lowercase `w` now draws Ö in messages; the lint already rejects lowercase.
- **Fallback (not used):** `KOMPLET`.
- **Evidence:** FORMAT §2.4; `screenshots/strings/de/hours.png`; `tools/regress.py` (fuente cells
  0..79 unchanged except cell 74). VERIFIED.

## D9. Pause-menu row 5: the label `f[5]` is the empty string
- **What:** `f[5]` = `""`; the values `d` = `KLASSISK STYRNING` / `RIKTNINGSSTYRNING` (17 glyphs)
  carry the whole row.
- **Reason:**
  - Spanish reads as one phrase (`CONTROL CLÁSICO`). Swedish puts the adjective first, which a
    label-then-value row cannot do.
  - `STYRNING: ` plus a Swedish word for "directional" is too wide (`STYRNING: RIKTNINGSSTYRD` =
    24 > 23, the highlight bar).
  - The code just concatenates (`w.java`: `v[i].concat(value)`), so `""` draws only the value. The
    array keeps its 10 entries, which `w.a()` requires (FORMAT §1.1).
- **Checks:** `lint_strings.py` allows an empty label in `f[3..7]`; the harness prints a warning for
  it, which is expected. Both values were seen live (`screenshots/runtime_sv/INDEX.md`, files 33–34).
  VERIFIED.
- **Fallback (not used):** `f[5]` = `STYRNING: `, `d` = `KLASSISK` / `RIKTAD`, less idiomatic.

## D10. Munich in the ending parchment: `När vi kom till Bayern`
- **What:** es `Cuando llegamos a Munich` → `När vi kom till Bayern` (`pergamino2`).
- **Reason:**
  - `München` needs ü, which the parchment cannot draw. cp1252 `FC` is beyond the 81-entry table
    (codes 44..124); its address word comes from the unreferenced region and points outside the
    file (FORMAT §4.6), which hangs the writer (`Caracter:` every tick), and in the ending that is
    an unskippable soft-lock. UTF-8 `C3 BC` silently draws ż (`Mżnchen`), because the reader
    ignores the lead byte.
  - `Bayern` is true (Munich lies in Bavaria) and inside the charset. `Munchen` and `Munich` are not
    Swedish.
  - The optional upgrade (a precomposed ü in empty slot `0x3C`, GLOSSARY §9.4, whose step 2 this
    list states for the current tools) was not done, so the text keeps `Bayern`. It would need the
    entry `"ü": 0x3C` in `tools/letras.py` `SV_SLOTS` (which also feeds `TEXT_MAP`) as well as the
    glyph in `letras_add.json`: `apply_add` refuses any slot outside the six Swedish ones, and the
    text encoder rejects ü.

## D11. Credit and title-screen wording: `efter …`, Swedish quotes `”…”`, `Tryck för att starta`
- **What:**
  - `pacoyjuan.png`: `efter spelet av / Paco Menéndez / och Juan Delcán`; `novela.png`: `efter romanen /
    ”Rosens namn” / av Umberto Eco`; `pelicula.png`: `och / Jean-Jacques Annauds / film med samma namn`.
    The four credit screens read as one sentence, as the Spanish ones do.
  - The parchment credits use the same idiom: `Efter spelet av`.
  - `pulsa.png`: `Tryck för att starta`.
- **Reason:**
  - `efter` is the Swedish credit idiom for "based on" (`efter en roman av`). Unlike `baserat på`
    it needs no å, and the Fraktur font has no ring to copy.
  - Swedish typography closes and opens a quotation with the same mark, `”`. The Fraktur font
    already has that glyph, so the title needs no new one (the Spanish `“…”` would be wrong in
    Swedish).
  - `Tryck för att starta` and `Tryck för att börja` are equally natural; `starta` needs one
    hand-drawn letter fewer (no b) in the pulsa font.
- **Evidence:** GLOSSARY §8; all four screens and the press line seen live
  (`screenshots/runtime_sv/INDEX.md`, files 02–10). VERIFIED.

## D12. Tick cap for g157 (Remigio's walk): 215 ticks, from the measured walk window
- **What:** `g[157]` ≤ **215** ticks (`text_sim`, isolated), enforced by `tools/lint_strings.py`
  (`TICK_CAPS`). g158 (≤ 96, ≤ 129 chained), g159 (≤ 211) and g51 (≤ 77) keep their caps.
- **Reason:**
  - The Phase A cap (≤ 232) was the longest shipped text (it), chosen while the walk was unmeasured.
  - Phase E measured the window from g157's start until Remigio reaches waypoint 8, where g158
    interrupts it: 220, 223 and 223 ticks in runs 1, 2 and 4. Remigio never paused, so that is the
    shortest window. es (221) and it (232) already lose part of their linger there.
  - 215 keeps the whole message, its 17-tick linger included, inside the window with a 5-tick margin.
    The Swedish g157 is 194 (193 live).
  - The windows of g158 (187) and g159 (319) are far above their caps, so those caps stay.
- **Evidence:** FORMAT §1.8, §9 question 1; `work/phaseE/runs/run{1,2,4}/agent/events.log`. VERIFIED.

## D13. No glyph under the ▶▶ marker: visible line 2 ≤ 34 glyphs on every page
- **What:** on every message page the visible part of line 2 (trailing `_` and spaces excluded) is at
  most 34 glyphs. Where a line 1 fills 35 glyphs, a `_` may end the page with line 2 empty.
- **Reason:**
  - In scripted scenes the blinking ▶▶ (glyph 95 at (306,164)) covers glyph 35 of line 2, which is
    usually the full stop or the end of a word. The shipped languages accept it (es 20 pages, fr 33);
    Swedish avoids it at the cost of a rewording or a page break.
  - Whether ▶▶ shows depends on `abadia.b.i.c` at runtime, not on the message, so the rule covers
    every page. That is also what the harness warning checks.
- **A full line 1:** the `_` that ends such a page may be the one the game inserts for a following
  `@N` (g159: `NU ÄR DE UPPTAGNA MED SINA SYSSLOR.@0`, line 1 exactly 35 glyphs, the inserted `_`
  alone on line 2). Never type a `_` right before `@` (FORMAT §1.4: `_ @0` gives a blank page).
- **Applied:** Phase E reworded the strings that had such a page: g52, g114, g155 (round 1) and g77,
  g122, g143, g149, g150 (round 2). Phase F's later language edits changed page layouts again
  (g54 got a page break after its vocative; g61, g64, g122, g131, g149, g150 and g163 were
  reworded; g149's `PRYTT BOKEN MED` lengthens line 2 of its last page from 27 to 29 glyphs)
  and kept the rule: the render of the final jar (`43846c9e…`) has no such warning
  (`screenshots/strings/de/report.txt`, `work/phaseF/render_r1.log` from the Phase F final
  verification, and `render_r2.log` after its rebuild). VERIFIED.

## D14. Derived images and screenshots stay out of git and are rebuilt
- **What:**
  - `assets_sv/res/` (the seven Swedish PNGs) is git-ignored. `tools/build.py` step 8a regenerates
    it on every build with `tools/images/build_*.py` from tracked sources (`assets_sv/image_src/**`
    and `tools/images/`) and from `original/` through `tools/images/inputs.py`. (The glyph JSONs in
    `assets_sv/glyphs/` feed build steps 5–6, the font and `letras`, not the image builders.)
    `--no-image-rebuild` skips the step, and so does a non-default `--assets`.
  - Under `screenshots/` only `*.md`, `*.txt` and `*.tsv` (indexes, reports, page lists) are
    tracked. The PNGs stay on disk as the verification set.
  - `original/`, `game/`, `work/`, `*.jar`, `*.rar` and `*.pdf` are git-ignored as before.
- **Reason:**
  - Every image and screenshot is derived from the original game's art. This is a personal
    translation, and the repository must not carry copies of that art.
  - The images are reproducible: a clean-room build with no `work/`, `game/` or `assets_sv/res/`
    gave a byte-identical jar and manifest (`tools/README_tools.md`). A tracked copy could only
    go stale.
  - The tracked text reports keep the verification reviewable without the frames.
- **Consequence:** deleting `work/` is safe for the build, but `work/` also holds the raw runtime
  evidence (run logs, agent `events.log`, raw shots) that the `INDEX.md` files and FORMAT cite, and
  the Phase A data that `tools/translate_tool.py` reads. Keep it as the verification archive.

## D15. The Swedish user manual
- **Status:** made in Phase F: `manual/Användarmanual.docx` and `manual/Användarmanual.pdf`, from
  `tools/manual/build_manual.py`. The brief made it optional, "only after everything above passes".
- **Source text:** the brief settles it: "a Swedish user manual translated from the English PDF".
  So the English PDF is the source, and the Spanish and other manuals are used only to check
  meaning. The translate-from-es rule (Decision 4) covers the game's own text: the table `m` and
  `res/es/*`.
- **Wording:** the GLOSSARY terms and names (Vilhelm, Adso, the canonical hours with NATTBÖN, Dag)
  and the in-game strings exactly as shipped, so the manual matches the screen. The script reads the
  menu labels and values (`strings_sv.tsv` rows `f`, `c`, `d`, `e`) and the hours (`b`) from the TSV
  and stops if they no longer match the sentences written around them. The prologue page is
  `translation/pergamino1_sv.txt`, unwrapped. The title word is "Användarmanual", as in the file name
  the brief gives; the README says "manual" for both the Swedish and the original manuals. A line on
  the copyright page, and one under KONTAKT, say that the Swedish translation is an unofficial
  personal-use version that the original authors did not make.
- **Pictures:** Swedish game frames from `screenshots/runtime_sv/`, with the numbered callouts drawn
  with Pillow in the English style. The menu picture is `49_menu_no_dialogue.png`, captured for the
  manual (`tools/drivers/manual_menu.sh`): every tour menu frame (24–41) has a dialogue box under the
  menu scroll. The monk sprites, the authors' photo and the Retroworks logo come unchanged from the
  English PDF (`pdfimages`).
- **Format:** `.docx` made with python-docx in a `uv` inline script, converted with
  `soffice --headless --convert-to pdf` (private profile in `work/phaseF/lo_profile/`); never opened
  in a viewer. The PDF is the reference layout. Two things are added after python-docx:
  - LibreOffice 7.3 drops every `.docx` hyperlink on PDF export, so the script adds the link
    annotations to the PDF with PyMuPDF: each printed address (and `www.java.com`) becomes a URI
    link, the footer address on every page included. The script checks the counts and that the
    section headings are whole words in the PDF text layer.
  - The `.docx` embeds Junicode regular and bold (obfuscated `word/fonts/*.odttf`, fsType 0 allows
    it), so Word on a machine without Junicode keeps the font and the page breaks. Verified with
    LibreOffice under a fontconfig that hides Junicode: Junicode is still used; without the embedded
    fonts it falls back to DejaVu Sans. The template's thumbnail, its 2013 dates and its
    "Microsoft Macintosh Word" `app.xml` are replaced.
- **Placement:** `tools/build.py` wipes and recreates `game/`, and `check_out_dir` refuses to wipe a
  `game/` that holds anything besides the files the build writes and `savedata.bin`. So the manual is
  not dropped into `game/` by hand: when `manual/Användarmanual.pdf` exists, the build copies it into
  `game/` as `User's manual (Swedish).pdf` (named like the originals, on the build's list of game
  files, and always allowed by `check_out_dir`). The `.pdf`, the `.docx` and the page images taken
  from the original manuals stay out of git (D14); the generator and its driver are tracked.
- **Reason:** the build owns `game/`; a manual that disagrees with the shipped strings would
  mislead; and the art in the original manuals is the same kind of derived material as in D14.

## D16. The two JOptionPane save-error texts stay Spanish
- **What:** `w` shows `Los datos guardados están corruptos. ` (reading a corrupt `savedata.bin`)
  and `Error al grabar el fichero. ` + the exception text (writing fails), both with the title
  `ERROR GRAVE` (`w.java:127`, `w.java:220`). The Swedish build leaves them as they are. The other
  untranslated texts in FORMAT §1.10 (`v1.3e`, the `d` debug overlay, the stdout line `Caracter:`)
  are not player text.
- **Reason:**
  - They are not language-indexed: they are plain constants, and every shipped language shows the
    same Spanish (FORMAT §0.2, §1.10).
  - Translating them in place would change the dialog for every language, not only for slot 4.
    Making them per-language would need a new code patch of `w.class` for two dialogs that a
    player normally never sees.
  - They appear only when `savedata.bin` is corrupt or cannot be written.
- **Where it is said:** the project `README.md` tells the player that these two dialogs stay
  Spanish, as in every shipped language.

## D17. Translation review record: which passes ran, and what they found
- **Why this entry:** the brief's definition of done requires every string and both parchments to
  pass "the editor, back-translation and consistency passes". `work/phaseC/` keeps only the
  resulting chunk files (`{array, index, sv, note}`). The verdicts went back to the workflow and
  are in its journals, which are Claude Code session files outside the project, not in git, and
  may be cleaned up: `~/.claude/projects/-home-ran-the-abbey-of-crime-extensum-swedish/8dfa1262-e7c1-4492-8c56-1b182a40f8ec/subagents/workflows/<wf>/journal.jsonl`
  (one JSON result per line; the step is named by its `label`). The full record, every pass,
  issue and rejection, is `docs/TRANSLATION_REVIEW.md` (generated by `tools/review_record.py`);
  this entry summarises it. The counts below were re-read from those journals for this entry.
  VERIFIED.
- **Phase C, per chunk (`wf_4a0ebacc-9c0`).** Chunks c01–c12 hold the 143 used `g` rows and u01
  the 20 dead ones; each parchment was its own unit.
  - Every unit got an editor pass (`edit:<chunk>:rN`: correctness, idiom, glossary use, length,
    markers), a blind back-translation (`backtr:…`) and a meaning check (`meaning:…`), followed by a
    revision. The back-translator was a separate agent given only the Swedish lines and told to
    read no files, run no commands and use no web. The meaning check compared its output with
    es, and with en/fr/it where they helped.
  - The loop repeated until neither pass had a must or should issue. A last pass then applied the
    remaining nits.
  - Rounds: 1 for c01, c02 and u01; 2 for c03–c06, c08, c09, c12 and both parchments; 3 for c07
    and c10; 4 for c11.
  - The final editor and meaning rounds of every unit had no must or should, with one exception:
    c11's last editor rounds kept one should, a `check_glossary.py` false positive (the comment
    `(g127)` in the `FINIS AFRICAE` row's note was read as an index). It was cleared at the end
    (`finalfix:c11`) by naming `FINIS AFRICAE` in g127 as an apposition.
  - **Back-translation language:** the brief asks for a back-translation into Spanish. In this loop
    (and in the Phase F re-review and unit x01) the back-translator wrote literal English, with NI
    and DU marked, and the meaning check compared that with the Spanish. The Spanish
    back-translation now exists for every unit: Phase F2 (below) made it from the final text. The
    English back-translations stay documented as an extra pass.
- **Phase C, the whole game.**
  - Two game-order consistency passes over the merged TSV (`consistency:r1`, `r2`): one nit each
    (g96, g95), no must or should.
  - Two read-throughs of every used message in game order plus both parchments, as a player would
    meet them (`player:r1`, `r2`): 1 must, 30 should and 32 nits in round 1; 1 must, 17 should and
    33 nits in round 2.
  - Per-chunk fixers (`fix:<chunk>:cr1`, `cr2`) applied or rejected each issue, giving a reason for
    each rejection. They rejected 59 in all, both musts among them: g75's ERA is the documented
    switch to NI (GLOSSARY §2), and g24's MÖRDAD is what es says (its clash with g93 is in the
    original game).
  - Final check (`final-check-2`): lint 0 errors, `check_glossary.py` 0 errors, both parchments
    within the 244-px edge (240 and 238).
- **Not in the per-chunk loop: the `ui` chunk**: `a c d e f` (21 of the 185 strings),
  `g[0] = ""`, the 7 HUD hours, `w.t`, `w.u` and `E.h`. It was copied from GLOSSARY §5.1 and §6.
  Those sections went through the Phase B glossary loop (`wf_cb1d7e9e-f32`: three rounds of a
  Swedish-language critic and a constraints critic), D8 and D9 settle NATTBÖN and `f[5]`, and the
  Phase E language critic read every row rendered and live. Phases B to E made no back-translation
  of these rows, and the game-order consistency pass read only `g`. The Phase F final verification
  closed that gap (unit x01, below), and Phase F2 back-translated them into Spanish.
- **After the whole-game passes:** the g127 apposition (`finalfix:c11`, above) was the last Phase C
  edit. No Phase C pass saw it; the Phase E language critic did.
- **Phase E (`wf_dcee03f1-9e3`).** The language critic read every string, both parchments and all
  rendered pages, in three rounds (`critic:language:r1`–`r3`; working notes in
  `work/phaseE/critic_language_r{1,2,3}/`). The 17 `g` rows that the Phase E fixers changed (g52,
  g54, g61, g64, g75, g77, g85, g114, g118, g122, g125, g131, g143, g149, g150, g155, g163) were
  checked by the next critic round and the harness render, and g54 also live in run 4. They got no
  editor or back-translation pass in Phase E.
- **Phase F (`wf_4230a7f1-04d`, `work/phaseF/e01.json`).** Those 17 rows went through the Phase C
  loop again: three rounds of editor, blind back-translation and meaning check (`rereview:*`).
  - Round 1: 1 should (g163) and 3 nits. Round 2: 3 should (g64 twice, g163) and 8 nits. Round 3:
    no must or should, 4 nits.
  - The revisions changed g54 (a page break only), g61, g64, g122, g131, g149, g150 and g163 (D13).
  - The round-3 nits (g61, g64, g149) were applied after the last review round. They were checked
    by the tools (`translate_tool.py check`, the lint, `check_glossary.py`) and by the render of
    the final jar `43846c9e…` in the Phase F final verification (`work/phaseF/render_r1.log`: 0
    errors, no line-2 warning). Unit x01 (next item) then gave their final text a language review.
- **Phase F final verification, unit x01 (`work/phaseF/ui_review/`).** One more Phase C round over
  the UI rows that have text (a0–a3, c0, c1, d0, d1, e0–e2, f0–f4, f6–f9, b0–b6, `w.t[4]`, `w.u[4]`;
  f5 is empty by D9, g0 is empty, `E.h[4]` keeps the Spanish title by D6) and the final g61, g64
  and g149.
  - The editor pass included consistency with the rest of the game: the hour names occur in no
    `g` message or parchment; DAG, GÅTAN and TRYCK match the HUD image, g144 and `pulsa`.
  - The blind back-translation (into English) was made by a separate Claude Code process started
    with every tool disabled (`claude -p --tools "" --safe-mode --no-session-persistence`). It saw only the Swedish
    lines and where each UI text appears on screen.
  - The meaning check compared that back-translation with es.
  - Result: editor 0/0/0 and meaning 0/0/0 must/should/nit. The back-translator flagged 7 segments
    (RIKTNINGSSTYRNING, INDIKATORER, I SKRIFTEN, the Latin OCULI, LABYRINTEN, SJUKHUSET and g64's
    DE SKA INTE FÅ VÄLJA FRITT). Each was judged no issue: it is the same in es, or it is a
    documented glossary decision. The loop was clean in one round and no row changed.
  - **Deviation:** the editor and the meaning checker were one agent; only the back-translator was a
    separate, blind reader. Details are in `docs/TRANSLATION_REVIEW.md` §3.4.
- **Phase F2, the Spanish back-translation (`wf_b66191f2-dd4`).** The back-translation into Spanish
  that the brief asks for, made from the final text (the TSV and parchments at commit `99c3661`)
  for all 16 units: c01–c12 and u01 as in Phase C, the 29 UI rows that have text (all but g0, f5
  and `E.h[4]`, as for x01) and both parchments. TRANSLATION_REVIEW §4 and Appendix C hold the
  whole record, including every back-translation.
  - Per unit: `read:<unit>` returned the unit's Swedish unchanged (`translate_tool.py extract`; a
    parchment's paragraphs with the hand-wrapping undone). `es-backtr:<unit>` was a separate agent
    given only those lines and told to read no files, run no commands and use no web; it translated
    them into Spanish (NI as vos, DU as tú) and listed what read as unclear. `es-meaning:<unit>`
    compared that with the original Spanish and judged every flag. A unit with a must or should
    would have gone to a fixer (`fix:`) and an editor check of the fix (`fixcheck:`).
  - Result: 225 lines back-translated, 94 segments flagged, meaning 0/0/1 must/should/nit. The one
    nit (g110: EN FÖRFÖRD MUNK makes the monk more passive than UN MONJE QUE SE HA DEJADO SEDUCIR)
    went to no fixer, by the pass's rule. No fix step ran and no row or parchment line changed.
  - Gap: the ui back-translator returned its 7 flags in one list beside its lines, and the meaning
    check was given only the lines, so it did not judge them. They concern TOM, AV, the hour names
    and widths, NATTBÖN, NATT, the end-screen split and the empty f5, all settled in GLOSSARY §5–§6
    and D8/D9, and the meaning check's row-by-row verdict covers each of those rows.
  - `tools/review_record.py` cross-checks that the read text equals the TSV and parchments at
    `99c3661`, that the units cover every row but g0, f5 and `E.h[4]`, and that each
    back-translation answers its lines one for one. After the pass: lint 0 errors,
    `check_glossary.py` 0 errors, BUILD OK (jar `43846c9e…`, unchanged), `render_strings.py` and
    `regress.py` RESULT: OK.
- **Where the outcome lives:** the texts are `translation/strings_sv.tsv` (each row's note records
  its decisions) and `translation/pergamino{1,2}_sv.txt`; the rendered pages are in
  `screenshots/strings/de/`.

## D18. Java 11's two startup stack traces are accepted, not patched
- **What:** on Java 11 every run prints two stack traces at startup, from `abadia.c.b.a(String)`: a
  ClassCastException (AppClassLoader → URLClassLoader), then a NullPointerException (FORMAT §7.7).
  The Swedish build leaves them as they are.
- **Reason:**
  - The pristine game prints the same two traces on Java 11, so the translation does not cause
    them. The code is a `/lib/*.jar` classpath hack that casts the application class loader to
    URLClassLoader, which only Java 8 allows; on Java 8 the log stays empty.
  - They are harmless: the game starts, plays and sounds normally, and the vorbis SPI it looks for
    is already in the jar.
  - The brief says "the run's stdout/stderr must show no exceptions". This is read as "no exception
    caused by the Swedish build". Hiding these two would mean patching `abadia/c/b.class`, a class
    shared by every language, to suppress a message the original also shows. The other option was
    to tell players to use Java 8, but the launchers run whatever `java` is installed.
- **Checks:** any other exception, or a `Caracter:` line, is still a failure (FORMAT §7.7).
- **Evidence:** every Phase E `game.log` holds exactly these two traces and no `Caracter:` line, in
  the Swedish runs and in the pristine en/es/pl runs alike (`work/phaseE/runs/run1/game.log`,
  `work/phaseE/runs/en-pristine/game.log`; `screenshots/runtime_sv/INDEX.md`). VERIFIED.

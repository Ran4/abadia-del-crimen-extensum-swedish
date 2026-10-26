# DECISIONS.md

The four decisions in `implementation_prompt.md` hold: Swedish takes over the `de` slot; `abadia.k` is
regenerated from source; the logo is the Spanish one; translation is made from es. This file records
only what Phase A showed must **change or be added**, with the reason for each. Details and evidence
are in `docs/FORMAT.md`.

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
- **HUD hour names:** these can use only precomposed glyphs placed in blank cells
  (2, 46, 72–74, 76–79 = bytes 47, 91, 117–119, 121–124). The hour bytes in `k.b` reference
  them. Example: the glossary's `NATTBÖN` uses a squashed Ö in cell 74, byte 119.
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
  - If a Swedish title is wanted instead, add a word from it to `TITLE_RE` in **both**
    `tools/run_headless.sh` and `tools/headless_lib.sh` first. Otherwise every Swedish runtime run
    times out finding the window.
- **Reason:** replacing `k` alone would leave Spanish words in the save/load menu and a German
  window title.

## D7. New: parchment å ä ö Å Ä Ö as a data-only `res/letras` extension
- **Placement:**
  - Append six precomposed glyphs to `letras` (first free address 0xBC93).
  - Point six **empty** table slots at them: Ä `0x5B`, Ö `0x5C`, Å `0x5D` (drawn red like all
    capitals), å `0x60`, ä `0x7B`, ö `0x7C` (drawn black).
- **Text files:** the Swedish `res/de/pergamino1|2` are written as raw bytes using those slot bytes.
  The byte map is in FORMAT §4.7. Lines end with CR, the file ends with `1A`, and no byte outside
  the whitelist is allowed.
- **No change** to `y.class`.
- **Glyph design:**
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

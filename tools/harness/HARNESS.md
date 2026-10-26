# Phase A: headless text-rendering harness

> **This copy (`tools/harness/`, Phase D)** differs from `work/phaseA/harness/` in two ways:
> `build.sh` builds into a content-addressed dir `work/harness_build/<key>` (printed on stdout,
> published atomically, never deleted, so concurrent renders and `tools/build.py` cannot pull the
> classes away mid-run; `render.sh` uses it, or `$HARNESS_BUILD`), and with `--ref-lang` an empty
> label `f[3..7]` is a warning, not an error (the row is `f[i] + value`; Swedish `f[5]` is `""`,
> GLOSSARY §6.3). The paths below are the Phase A originals.

The harness draws every string of a language with the game's own code. It writes contact sheets
upscaled 3x (nearest neighbour), writes 1x raw PNGs and a machine-readable `layout.json`, and exits
non-zero when a character has no glyph or a layout would crash or hang the game.

All paths below are relative to `/home/ran/the_abbey_of_crime_extensum_swedish/work/phaseA/harness/`
unless they are absolute.

Legend: **VERIFIED** = I checked it in bytecode, data or a run. **INFERRED** = reasoning only.

---------------------------------------------------------------------------------------------------

## 1. Usage

```sh
H=/home/ran/the_abbey_of_crime_extensum_swedish/work/phaseA/harness

# build (javac --release 8, compiled against a copy of the pristine jar in lib/)
$H/build.sh                       # optional arg: another reference jar

# all strings of a language, any jar, optional res/ overlay directory
$H/render.sh --jar $H/lib/game-pristine.jar --lang es --out $H/out/es --ref-lang en
$H/render.sh --jar PATCHED.jar --lang de --out OUT/de --ref-lang es      # later: Swedish in slot 'de'
$H/render.sh --jar PATCHED.jar --res NEW/res --lang de --out OUT/de       # res files override the jar's

# validation only (no PNGs), about 1.5 s
$H/render.sh --jar X.jar --lang de --out OUT --no-images

# preview draft text before patching anything (UTF-8 input files, '#' lines ignored)
$H/render.sh --jar $H/lib/game-pristine.jar --lang de --out $H/out/sv_probe --only-custom \
    --msgfile $H/samples/sv_probe_messages.txt \
    --textfile $H/samples/sv_probe_text.txt \
    --parchfile $H/samples/sv_probe_parch_utf8.bin
```

| option | meaning |
|---|---|
| `--jar F` (required) | the game jar. Every `abadia.*` class comes from this jar. |
| `--res DIR` | a directory that replaces `res/` file by file. `/res/NAME` is served from `DIR/NAME` if it exists, otherwise from the jar. Each resolved URL is printed under "resources used". |
| `--lang C` | one of `es en it fr de pl`. It sets `Abadia.a` to that index of `Abadia.u`. |
| `--out DIR` (required) | the output directory |
| `--ref-lang C` | checks array sizes against language C, and checks that every `g[i]` has the same `@N` speaker-marker sequence and the same "starts with @" flag. A mismatch is an error. |
| `--msgfile F` | each line is one message in `g[]` syntax (`@N ` prefix, `_`, `*`). It is paginated and boxed by the game code. |
| `--textfile F` | each line is drawn centred with `j.a(s,-1,y)`, like the menu and end-of-game strings |
| `--parchfile F` | a raw byte file in `pergamino1` format (CR line breaks, 0x1A end). It is run through the real parchment state machine. |
| `--only-custom` | skips the built-in language arrays and the parchments |
| `--no-parchment`, `--no-images`, `--no-raw`, `--per-sheet N` | self-explanatory |

**Exit codes:** 0 = OK. 2 = at least one ERROR (missing glyph, or a layout the game would crash or
hang on). 1 = usage error or harness crash. Offenders are listed in `report.txt` and in
`layout.json.errors`, and the `MISSING GLYPH` lines are repeated on stderr.

**Safety:** `render.sh` runs `env -u DISPLAY -u WAYLAND_DISPLAY java -Djava.awt.headless=true`.
`harness.Launch` refuses to start without `java.awt.headless=true`. **VERIFIED** with
`-verbose:class`: neither `abadia.E` (the game's Frame) nor `java.awt.Frame` nor `java.awt.Window`
is ever loaded. The game thread, the sound classes (`abadia.c.a.*`, `javax.sound`) and the music are
never touched either. `sun.awt.X11.XToolkit` gets loaded, because `HeadlessToolkit` wraps it, but
with no DISPLAY it never connects to an X server.

**VERIFIED:** Java 11 and Java 8 (`JAVA=/usr/lib/jvm/java-8-openjdk-amd64/bin/java $H/render.sh ...`)
produce pixel-identical output: 725/725 raw PNGs match (`scripts/cmp_png_dirs.py`). Two runs are
pixel-identical as well. One language takes about 3 s.

## 2. Files

| path | role |
|---|---|
| `src/harness/Launch.java` | Bootstrap with no game dependency. It builds `OverlayLoader(URLClassLoader)` over `[build/gameside, --jar]` with the platform loader as parent, and overrides `getResource()` so that `res/*` comes from `--res` first. It records every resource used and calls `abadia.TextHarness.run()`. |
| `src/abadia/TextHarness.java` | The harness. It sits in package `abadia` so it can call package-private game methods directly, and uses reflection (`setAccessible`) for private ones. No variable has a one-letter name, because a local `i` would hide class `abadia.i`. |
| `build.sh`, `render.sh` | compile and run (see above) |
| `lib/game-pristine.jar` | Copy of `original/TheAbbeyOfCrimeExtensum.jar`, sha256 `1bc6b3fc…1a36f0`, used for compiling and as the pristine target. |
| `samples/sv_probe_*` | Swedish probe inputs (section 7) |
| `out/{es,pl,en}/` | Sheets for the pristine jar. `out/sv_probe/` holds the probe. |
| `../scripts/font_cells.py` | uv script that dumps the 80 cells of `fuente.png` as ASCII |
| `../scripts/cmp_png_dirs.py` | uv script that compares two PNG directories pixel by pixel |

Outputs per run (`--out DIR`):

- `report.txt`: summary, resources used, WARNINGS, ERRORS and RESULT.
- `layout.json`, schema:
  - `messages[]`: `{array, index, raw, pages:[{speaker, lines:[...]}], errors:[...]}`. `lines` are the
    exact strings `j.f()` draws, including the trailing space and `_`.
  - `endgame[]`: `{array:"a", index, raw, x, y}`
  - `menu[]`: the `f`, `c`, `d`, `e` raw strings, plus `w.t[lang]` and `w.u[lang]`
  - `hours[]`: `{index, bytes}`, with `bytes` decoded as ISO-8859-1
  - `parchment.{intro,ending,custom*}`: `{pages, steps, maxLineWidthPx, rightmostInkX, lines:[{page, widthPx, text}]}`
  - `resources{}`, `errors[]`, `warnings[]`
- `coverage.txt`: every code point for which the game's glyph routine produces ink.
- Sheets (3x): `glyphs.png`, `messages_NN.png` (16 pages per sheet), `menu.png`, `endgame.png`,
  `hours.png`, `parchment_{intro,ending}.png` (6 pages per sheet; `_NN` suffixes only when a sheet set has more than one file, as for `messages`), and `custom*.png`, `text*.png`,
  `parchment_custom*.png`.
- `raw/` (1x, for pixel comparison against real screenshots):
  - `msg_g%03d_p%d.png`: 320x30, the screen region (0,146)-(320,176)
  - `endgame_pct{5,95,100}.png`: 320x176
  - `menu_state{0,1,2}.png` and `slots_set{0,1}.png`: 320x176
  - `hud_hour{0..6}.png`: 320x32, the screen region y=176..208
  - `parch_{intro,ending}_pNN.png`: 320x208

## 3. How each surface is produced, and which parts are game code

The initialisation in `initGame()` sets `Abadia.a = langIdx` and then calls, all **VERIFIED**
headless:

- `v.a()` loads `<lang>/marcador.png` → `v.j`, `numRoman.png` → `v.k` and `fuente.png` → `v.c`, sets
  `v.b = v.c`, and sets `v.d = b.a("fuente.png")`. The last one is the PLTE-tinted copy using
  `Abadia.az = {0,0,0}`, so the menu font is black. It also sets `v.a = <lang>.b` (the hour bytes)
  and fills the 56x8 buffer `v.h` with 0x275947.
- `j.a()` loads `caras.png` → `cx` and `dialog.png` → `cy`, sets `Abadia.ae`, `j.b = bS[lang] = <lang>.g`
  and `j.a = bT[lang] = <lang>.a`.
- `w.a((Abadia)null)` sets `l=<lang>.f`, `m=.d`, `n=.c`, `o=.e`, `j=w.t[lang]` and `k=w.u[lang]`.
  Then `w.b = i.b("pergamino2.png")` is set, as `Abadia.a()` does at `Abadia.java:202`.
- `y.a()` loads `letras` → `p`, `<lang>/pergamino1` → `c`, `<lang>/pergamino2` → `d` and
  `pergamino.png` → `q`.

`abadia.i` loads everything through `i.class.getResource("/res/"+name)`, using `ImageIcon` for images
and `getResourceAsStream` for bytes (**VERIFIED**, `i.java`). That is why the `--res` overlay works
through the class loader. All the static initialisers that run (`Abadia`, `c`, `c.b`, `j`, `v`, `w`,
`y`, `D`, the language classes) only build data tables (**VERIFIED** with `javap`).

| surface | what runs | replicated (not game code) |
|---|---|---|
| Message box | `j.c(int)`, private, via reflection: `cm=b[i]; cm=cm.replace("@"," _ @").substring(3); cs=cm.split(" "); e(); f()`. Then the private `e()` and `f()` are called repeatedly while `ct < cs.length`. That is exactly the page sequence `j.b()` produces, because it calls `e();f()` whenever `cu<=0`. Each page is composited by the game's own `j.c()` (package-private) onto a 320x208 black screen: `cz` at (0,146), face from `caras.png` at (6,153) clip 20x20 offset (−20·co, −20·cF), continue-marker glyph 95 at (306,164). | `cu` is temporarily set to 0 before `j.c()` so that `cF=0` (closed mouth, no randomness). `Abadia.ak=0` so the blinking marker is visible. The background is black instead of the game view. |
| Pause menu | The private `w.a(int,int)` with `(190, l.length*10+20)` and `w.v` = composed items. Before it, `v.b=v.d` and `Abadia.al.setClip(0,0,320,208)`, as `w.a()` does. | The suffix concatenation of `w.a(int,int)` cases 3–7 (`f[3]+e[J]`, `f[4]+c[H]`, `f[5]+d[c?0:1]`, `f[6]+c[fullscreen]`, `f[7]+c[w.i]`). Case 6 reads `Abadia.s.a`, a field of the Frame object, so the composed array is passed instead (`v != l` skips the switch). Three states show every c/d/e string. |
| Save/load list | Private `w.e` is set to slot bytes, then the private `w.c()` builds `h[]` = `w.t[lang]+day+" "+7 hour bytes`, or `w.u[lang]`. Then `w.a(120,100)`. | the choice of sample slots |
| End of game | `Abadia.q()` (black 320x176), then the 4 calls from `E.java:378-381`: `j.a(a[0],-1,32)`, `j.a(pct+a[1],-1,48)`, `j.a(a[2],-1,64)`, `j.a(a[3],-1,128)`. | pct values 5, 95 and 100 |
| HUD hour | `D.l=7*h; v.e=9;` (= `D.c()`), then `v.c()` ×9 (2 blank shifts + 7 chars), `v.e()` (marcador at (0,176) + window at (4,197)), and `v.b(day)` (roman numeral at (37,183)). | none |
| Parchment | The real state machine `y.a(Graphics ad, Graphics al)` with `Abadia.ac`/`ad` = a 320x208 RGB back buffer, `y.b = text`, `y.a = 0` and `y.e = -1` (no music call). It is stepped until `y.a == -1`, and the back buffer is snapshotted whenever the state enters 3 (page full) or −1 (end). Sound calls are no-ops because `c.b.G` is false. | A static decoder that replicates `y.a()` case 1, used only for diagnostics (section 5.3). It is authoritative only when `y.class` and `letras` are byte-identical to pristine (sha256 checked). Otherwise its findings become warnings, and the real run decides. |

## 4. Text-layout facts (all VERIFIED in bytecode/decompile and by rendering)

### 4.1 `j.a(String s, int x, int y, Graphics g)` (`j.java:599-618`)

- `x == -1` gives `x = 160 - s.length()*4` (bytecode offsets 1–13: `sipush 160 … iconst_2 ishl`). The
  whole length counts, line breaks included. A centred string needs ≤ 40 chars or it starts at x<0.
- Every char advances 8 px, including chars that draw nothing.
- `'_'` (95) and `'%'` (37) are line breaks: x returns to the start, y += 10, and `'%'` adds +4
  (offsets 31, 42, 59).

### 4.2 Glyph routine `private static void a(int ch,int x,int y,Graphics)` (`j.java:620-797`)

- A `lookupswitch` with 36 cases (offset 19) maps code points to a base code plus at most one accent
  overlay. The full table is in `TextHarness.staticMap()`:
  - `! ' ,` → 93, 97, 60
  - `x`(120) and `Ê`(202) → E + circumflex
  - `¡`→92, `¿`→64, `Ç`→106 (y+1), `Ñ`→94, `ß`→62, `Ł`→114, `Œ`→107
  - `ÀÁÂÄ ÈÉ ÌÍÎ ÒÓÔÖ ÙÚÛÜ` → base letter + grave / acute / circumflex / diaeresis
  - `Ą Ę` → + ogonek
  - `Ć Ń Ś Ź` → + acute
  - `Ż` → + dot
- Accent overlays are drawn with the same routine: acute = 96 at y−2, grave = 104 at y−2,
  circumflex = 105 at y−2, diaeresis = 61 at y−1, ogonek = 116 at y+2, dot = 115 at y−2
  (offsets 649–724).
- After the switch: `if (c != 32 && c < 45) return;` (offsets 602–615). Otherwise the font image is
  drawn at `x − (c−45)*8` inside an 8x8 clip at (x,y). So code c shows cell c−45 of `fuente.png`.
  Cells exist for 45..124 (640 px / 8 = 80). For c ≥ 125, or for an empty cell, nothing is drawn.
- **Empty cells in the pristine `fuente.png`** (**VERIFIED**, `scripts/font_cells.py`): 47 `/`,
  91 `[`, and 117–124 `u v w x y z { |`.
  - Lowercase ASCII letters are **not** letters. They select special cells: `'`=apostrophe, `` ` ``
    acute, `h` grave, `i` circumflex, `s` dot, `t` ogonek, `_` continue-marker, and the HUD
    ligatures `b c d e f g m n o p` (for example es hour 5 = `VgPERAS`, where `g` = "ÍS"; es hour 6 =
    `COMdefg`, en = `COMbcNE`).
  - `@` (64) draws `¿`. `\` (92) draws `¡`. `]` (93) draws `!`.

**The has-glyph rule** (implemented in `staticHasInk()`):

> (base, accent) = switch(cp). Valid iff base == 32, or 45 ≤ base ≤ 44+fontGlyphs and cell base−45
> is not empty. (An accent alone never occurs in the pristine table.)

The harness does **not** rely on this rule. It computes the authoritative table empirically: it calls
the private glyph routine for all 65536 BMP code points on a transparent 24x24 image and records
whether any pixel got alpha > 0. On the pristine jar, the static rule and the empirical table agree
for all 65536 code points (`static-rule mismatches: 0`, **VERIFIED**). Result: 106 code points have
ink.

- **Non-ASCII:** ¡ ¿ À Á Â Ä Ç È É Ê Ì Í Î Ñ Ò Ó Ô Ö Ù Ú Û Ü ß Ą Ć Ę Ł Ń Œ Ś Ź Ż.
- **ASCII with ink:** `!'` `,-.0-9:;<=>?@A-Z\]^_` and `` ` ``, `a-t`, `x`.
- **ASCII without ink:** `"#$%&()*+/[` and `{|}~u-w y z`.
- **`Å` (U+00C5) has NO glyph. `Ä`/`Ö` work (A/O + diaeresis). `å ä ö` (lowercase) have none.**
- If a patched jar changes the switch or widens `fuente.png`, the empirical table follows
  automatically. Mismatches with the pristine static rule are reported as warnings only.

Validation contexts (`checkChars`):

- space, `_` and `%` are always allowed.
- `*` is allowed only inside messages (message line-end marker; it draws nothing).
- Every other char must be in the empirical table, or it is an error: `MISSING GLYPH <where> pos N: U+XXXX`.

### 4.3 Message pagination `j.e()` (`j.java:434-483`)

- **2 lines per page.** A line takes words while `line.length() + word.length() <= 35` (offset 35,
  `bipush 35`). The line buffer includes the trailing space, so a line holds **at most 35 visible
  chars**.
- `f()` draws line i at (32, 5+12i) into the 320x30 box (offsets 57–61). On screen the box is at
  y=146.
- A word that **contains `*`** ends the line. A word that **contains `_`** ends the page. The `*`
  then draws as a blank cell and the `_` as a harmless line break at the line's end.
- A word starting with `@` is a speaker marker: `co = Integer.parseInt(word without '@')`.
  - `co` selects the face (`caras.png` is 340x80 = 17 faces x 4 mouth frames).
  - `co` also indexes `j.ck[]` (15 voice sounds) in `j.b()`, so co must be 0..14.
  - `@x` with a non-digit gives a NumberFormatException.
  - `"@"` in the middle of text becomes `" _ @"`, so every marker also starts a new page.
- `c(int)` does `.substring(3)` after the replace. **A message that does not start with `@` loses
  its first 3 characters.** Pristine `g[2]`, `g[3]`, `g[45]` and `g[46]` (es/en/fr/pl/de) have no
  `@`. The harness only warns, because there is no named `j` constant for indices 2, 3, 45 or 46
  (dumped all 143 `public static final int` of `j`). INFERRED: these four messages are probably never
  shown; it was not proved.
- **A trailing space** in a message makes `split(" ")` drop the empty tail. `cu` then runs out on
  the last char and `j.b()` calls `e()` past the end of `cs[]` (ArrayIndexOutOfBounds). The harness
  reports an ERROR. INFERRED from the arithmetic: Σ(len+1) = cm.length()+1 normally.
- **A word longer than 35 chars** never fits. `e()` returns two empty lines without advancing, so the
  game shows empty pages forever. The harness reports an ERROR ("no progress at word …").
- Line 2 of a page with 35 visible chars is overlapped at x=306..313 by the blinking continue-marker
  (`j.c()` draws glyph 95 at (306,164); line 2 is at y=163). It is a WARNING only, because pristine
  es has 20 such pages, en 24, pl 26 and fr 33.

### 4.4 Pause menu (`w.java:296-325`)

- The background is `pergamino2.png` (220x136), centred at x=50..269, y=20..155.
- The highlight bar is `fillRect(160-95, 88-60+4+f*12, 190, 9)` in colour 0xC05050.
- Items are centred (`j.a(s,-1,32+12*i)`) for i=0..9, in the **black** font `v.d`.
- **Rules:** an item+suffix wider than the parchment (centred x < 50, that is > 27 chars) is an
  ERROR. Wider than the 190 px bar (> 23 chars) is a WARNING.
- Pristine longest: es "PANTALLA COMPLETA: NO" 21 chars, pl 22, it 22, fr "CONTRÔLES: DIRECTIONNEL"
  23 = 184 px.
- The save/load list uses `w.a(120,100)` (bar 120 px, y = 42+12i). Each line is `w.t[lang]` +
  day digit + `" "` + the 7 hour bytes drawn through the glyph switch, or `w.u[lang]`.
- **`w.t`/`w.u` are hard-coded in `w.class`, not in the language classes.** **VERIFIED** with javap
  `w.<clinit>` offsets 218–281: t = {"DÍA ","DAY ","DIE ","JOUR ","DÍA ","DZIEŃ "} and
  u = {"VACÍO","EMPTY","VUOTO","VIDE","VACÍO","PUSTE"}. Slot 4 ('de') reuses **the same
  constant-pool entries as Spanish** (#7 "DÍA ", #15 "VACÍO"). A Swedish "DAG "/"TOM" therefore
  needs new CP entries; editing #7/#15 would also change Spanish.

### 4.5 End-of-game screen (`E.java:378-381`)

The four strings are centred (≤ 40 chars each, with the percentage digits prepended to `a[1]`) at
y = 32, 48, 64 and 128 on black. Pristine maximum: fr 29 chars.

### 4.6 HUD hour window (`v.c()`, `v.java:136-155`, `D.c()`)

- Each `v.c()` call shifts the 56x8 buffer left 8 px, fills x=48..55 with 0x275947 and draws **raw**
  `(byte-45)*8` from `v.b`, **without the glyph switch**.
- **Rule:** an hour byte must be 32, or 45..124 with a non-empty cell. A byte ≥ 0x80 is negative in
  Java and draws nothing. The harness checks the ink of each 8x8 cell in `v.h` after the scroll.
- The same bytes also appear in the save/load list **through** the switch. So 33 `!`, 39 `'`,
  44 `,` and 120 `x` would look different there. The harness warns about these; pristine uses none.
- The window is drawn at (4,197). There are 7 hours × 7 bytes = 49 bytes.

## 5. Parchment (`abadia.y`): driven offscreen, feasible and implemented

### 5.1 Mechanics (**VERIFIED**: `y.java`, javap offsets in brackets)

- Page geometry:
  - `pergamino.png` (190x190) is drawn at ((320−190)>>1, (208−190)>>1) = (65,9).
  - Text starts at x=76, y=18 [117, 122]. CR (13) gives x=76, y+=16 [246], and a page break when
    y > 178 [263]. So there are **11 lines per page**.
  - LF (10) forces a page break. 0x1A ends the text. A space advances 8 px [291].
- Glyph lookup:
  - `idx = (f-32-12)*2` [1116–1119], `g = LE16(letras[idx]) − 42711` [1153].
  - Glyph bytes encode one pixel each, at `(i + lo nibble, j + hi nibble)`.
  - A byte `0xF?` ends the glyph and advances i by its low nibble.
  - Colour is `0xC0000000 | (((f & 96) == 64) ? 0xD00000 : 0)` [1096–1104, 1358]: **uppercase is
    red**.
  - The game draws one pixel per frame.
- `letras`: the offset table covers **only chars 44..124** (81 entries). Valid entries are
  `, - . / 1 2 3 7 : ; A–Z a–z`. `/` is the `ñ` glyph. **Digits 0 4 5 6 8 9, `?` and `!` have no
  glyph.** `'` is not a glyph either: it is a modifier that draws an apostrophe stroke on the next
  char.
- Decoding (case 1):
  - 39/0x92/0xB4 (an apostrophe-like byte) consumes the next byte and draws it with an apostrophe
    stroke.
  - 0xC0 is À.
  - Latin-1 àáçèéìíñòóùú and âêîôû are handled.
  - 0xC3/0xC4/0xC5 are treated as UTF-8 lead bytes, but **only the 2nd byte is looked at**:
    82 ł, 84 ń, 85 ą, 87 ć, 99 ę, 9B ś, A1 á, A9 é, AD í, B1 ñ, B3 ó, BA ź, BC ż.
- Failure modes:
  - A decoded char < 44 makes `letras[negative]` throw, uncaught in case 1, so the parchment never
    advances.
  - A char in 44..124 with table entry 0 throws in case 2. The game catches it, prints
    `Caracter: N` [1917] and repeats every frame. **It hangs, and the ending cannot be skipped**
    (skip only works when `b != d`).
  - A char > 124 reads glyph data as an offset, which is garbage.

### 5.2 Results for the pristine jar (**VERIFIED** runs)

| lang | intro pages / lines / widest | ending pages / lines / widest | rightmost ink x (intro / ending) |
|---|---|---|---|
| es | 8 / 85 / 169 px | 8 / 88 / 166 px | 243 / 241 |
| pl | 8 / 86 / 171 px | 7 / 77 / 167 px | 245 / 242 |
| en | 8 / 83 / 171 px | 7 / 77 / 171 px | 246 / 246 |
| it | 8 / 84 / 177 px | 7 / 77 / 176 px | 252 / 250 |
| fr | 9 / 95 / 177 px | 8 / 88 / 179 px | 252 / 254 |

- Widths are cursor advance minus 76. The parchment bitmap ends at x=254.
- Recommended line budget for translators: **≤ 171 px of advance** (en/pl maximum, ink ≤ 246). The
  hard limit is the parchment edge (fr reaches 254).
- The static-decoder page count equals the real run's page count for all 10 texts.
- The images were checked visually: red capitals, accents, ñ, Polish UTF-8 ąęłśźż and the credits
  pages all look right. See `out/es/parchment_intro.png` and `out/pl/parchment_intro.png` (`_01`, `_02` ... when a text has more than 6 pages).

## 6. Pristine validation results (**VERIFIED**, `--ref-lang es`, or en for es)

| lang | messages / pages | missing glyphs | other errors | notes |
|---|---|---|---|---|
| es | 163 / 694 | **0** | 0 | 4 "no @" warnings, 20 marker-overlap warnings |
| pl | 163 / 695 | **0** | 0 | 26 overlap warnings |
| en | 163 / 683 | **0** | 0 | 24 overlap warnings |
| fr | 163 / 753 | **0** | 0 | 33 overlap warnings |
| it | 163 / 733 | **3**: U+008F in g[124] p1, g[156] p2, g[157] p3 | 4 ref-diffs: it g[2], g[3] carry `@0` where es has none | 27 overlap warnings |
| de (spare slot) | 163 / 703 | **1**: `Ë` U+00CB in g[1] (`"@3 ÄËÜß WILLKOMMEN…"`, a test string) | 0 | |

- The Italian U+008F is an encoding slip in the original data (probably meant È). In the shipped game
  it draws as a blank cell. This is consistent with the rule, not a sign that the rule is wrong: 143
  is not in the switch, and 143−45 = 98 ≥ 80.
- The speaker-marker sequences of es, en, fr, pl and de are identical. Only it differs, at g[2]/g[3].
- Visual checks I looked at:
  - `out/es/messages_01.png`: Á/Í/Ó/É accents sit above the capitals, ¿ ¡ and the comma glyph are
    right, the face matches `@3`/`@0`, and g[1] page 4 shows the marker overlapping the "E" of NOCHE.
  - `out/es/menu.png` (black font on `pergamino2`, highlight bar), `out/en/menu.png`,
    `out/es/hours.png` (NOCHE…COMPLETAS incl. the ligatures), `out/es/endgame.png`,
    `out/pl/endgame.png` (Ł Ą Ę Ć Ś) and `out/pl/messages_01.png`.

## 7. Swedish probe on the pristine jar (`out/sv_probe/`, **VERIFIED**)

- Messages and centred text: `Ä` and `Ö` render as A/O + diaeresis. **`Å`, `å`, `ä` and `ö` are
  missing** and show as gaps, for example "V RT", "N GOT".
- Parchment, UTF-8 input:
  - `Å` (C3 85) is **silently drawn as `ą`**, because only the 2nd byte counts.
  - `ä` (C3 A4 → 164), `ö` (C3 B6 → 182) and `å` (C3 A5 → 165) fall past the 81-entry table. The
    real run **hangs** at the first `ä` ("stuck drawing char 164").
- Parchment, Latin-1 input:
  - 0xC5 (`Å`) is taken as a UTF-8 lead byte and swallows the next byte.
  - `ä`=228, `ö`=246 and `å`=229 are not decoded, so they hit `> 124` and the run hangs.
- Conclusion for phase B: Swedish needs at least the following:
  - a new `Å` case in the `j.a(int…)` switch, plus a ring glyph or a new cell in `fuente.png`;
  - an uppercase-only message style (lowercase letters are glyph codes);
  - either new `letras` glyphs plus a `y.class` decode patch for åäöÅÄÖ, or parchment text without
    them.
- The harness reports all of these as MISSING GLYPH errors (exit 2).

## 8. Caveats

- INFERRED: the harness output is identical to the live game, because it is the same code drawing
  into the same 320x208 buffers. It was **not** compared with a live screenshot, because only the
  runtime task may run the game.
  - In the game the 320x208 frame is scaled by `Abadia.d=4` for the window.
  - To compare: crop the live frame region (0,146,320,30)·4 against `raw/msg_*.png`, after a 4x
    nearest-neighbour upscale.
- Backgrounds behind the message box, the menu and the HUD are black instead of the game view.
  `dialog.png` and `pergamino2.png` are drawn with their own alpha.
- The face is always drawn with mouth frame 0, and the blinking marker is always shown.
- The menu suffix composition is replicated (section 3). The background highlight colour and layout
  come from the game's own `w.a(int,int)`.
- The static parchment decoder is a replica, used only for diagnostics, and it is gated by pristine
  sha256 (`y.class` 8bb617b5…, `letras` 047ebed0…). For a patched `y.class`/`letras` its findings
  become warnings, and only the real run (exception or no-progress) produces errors.
- Message pages are reported with the speaker in effect after `e()` on that page. That is what
  `j.c()` uses for the face.

## 9. Claims

- **H1**: The harness renders with the game's own code, headless. It uses `j.c(int)`/`e()`/`f()`/`c()`,
  `w.a(int,int)`/`w.c()`, `j.a(String…)`, `v.c()`/`v.e()`/`v.b(int)` and `y.a(Graphics,Graphics)`.
  No Frame or Window is loaded. Java 8 and 11 output is pixel-identical.
- **H2**: The glyph rule is (base, accent) = switch(cp). A char is valid iff base == 32 (a blank), or
  45 ≤ base < 45+glyphs and the cell base−45 is non-empty. It is confirmed for all 65536 BMP code points (0 mismatches).
  106 code points have ink. `Å`/`å`/`ä`/`ö` are not among them; `Ä`/`Ö` are.
- **H3**: Empty `fuente.png` cells are codes 47, 91 and 117–124.
- **H4**: Messages have 2 lines per page and ≤ 35 visible chars per line. `*` ends the line, `_` ends
  the page. `@N` sets the speaker (0..14), and a message must start with `@`. A trailing space makes
  `e()` run past the end. A word > 35 chars stalls forever.
- **H5**: Pristine es/pl/en/fr have 0 missing glyphs. it has 3 (U+008F). de has 1 (Ë, test string).
- **H6**: `w.t`/`w.u` (DAY/EMPTY) are hard-coded in `w.class`, and slot 4 shares CP #7/#15 with
  Spanish.
- **H7**: The parchment can be driven offscreen. Its rules: 11 lines/page, start x=76, glyph table
  44..124, red capitals, no 0/4/5/6/8/9/?/!. A missing glyph hangs the game.
- **H8**: Pristine parchment widths: max advance 179 px (fr), en/pl 171 px. Ink reaches x=254 at most.
- **H9**: The pristine parchment cannot render Swedish åäö in either encoding. UTF-8 Å becomes ą.
- **H10**: The HUD draws hour bytes raw, without the switch. The save list draws them through the
  switch.
- **H11**: The menu font is black (`v.d`). An item must fit the parchment (≤ 27 chars) and should fit
  the bar (≤ 23 chars).

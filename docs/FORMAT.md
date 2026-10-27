# FORMAT.md: data formats and constraints for the Swedish build

Checked reference for every later phase (glossary, translation, glyphs and images, build tooling,
verification). It merges the seven Phase A reader notes and two independent adversarial reviews of
each, plus re-checks done for this synthesis wherever a reviewer disputed a claim.

Labels: **VERIFIED** means checked in bytecode, decompile or data, or by running the real game code
headlessly. **INFERRED** means reasoned and not executed. **UNCERTAIN** means still open; each one
says what would settle it. "glyph" means one 8-px cell of the in-game font, i.e. one UTF-16 char
in a string. Offsets are `javap -c -p -constants` code offsets. `X.java:NNN` is a Vineflower line in
`work/decompiled_vf/abadia/`.

Source notes (read these for depth): `work/phaseA/text.md`, `font.md`, `parchment.md`,
`deslot.md`, `images.md`, `runtime.md`, `harness.md`. Reviewer evidence is in
`work/phaseA/refute_<reader>_{0,1}/`.

**Updated after Phases C–F** (2026-10-27; Phase E's final jar was sha256 `0ad2bbf0…a2a260`;
after the Phase F string edits the jar is `43846c9e…0c60c`, which differs from it only in
`abadia/k.class` (entry CRC diff, Phase F final verification). That jar was built, rendered and
regressed in the Phase F final verification: `work/phaseF/build_final_r1.log`, `render_r1.log`,
`regress_r1.log` (3711 frames OK), with `manifest_game.json` = `manifest_det1.json` =
`manifest_det2.json` (sha256 `d3da74a2…f236d`). After the dependency pins of that round the same
jar was rebuilt and re-checked (`build_final_r2.log`, `render_r2.log`, `regress_r2.log`;
`manifest_game_r2.json` = `manifest_det3.json`, which differ from `d3da74a2…` only in the
`image_inputs` key). `work/build/manifest.json` always holds the current hashes). Facts that the
built Swedish game proved, at runtime or with the game's own code, are marked VERIFIED with their
evidence path. Settled open questions are closed in §9. The project's own tools are in `tools/`
(`tools/README_tools.md`); the `work/phaseA/…` tools named below are the Phase A originals.
Evidence paths under `work/` are git-ignored scratch: the tracked summaries are the `INDEX.md`,
`report.txt` and `SUMMARY.txt` files under `screenshots/`.

---

## 0. Provenance

| item | value | status |
|---|---|---|
| download `original/LaAbadiaDelCrimenExtensum.rar` | 19,934,302 B, sha256 `d8335c45d479dc4f160400ce09ec04434a19e968b11ec2ef686e1c4ab16e442c` | matches the prompt |
| `original/TheAbbeyOfCrimeExtensum.jar` | 17,944,815 B, sha256 `1bc6b3fcbaf6116bd0e4a92b96193be54e72686a00c1208ba909b7bd961a36f0` | matches the prompt |
| `work/jar/` | extracted jar; byte-identical to the original (diff -rq empty) | VERIFIED |
| launchers | `.sh` (90 B): `#!/bin/bash` + LF + ``cd "`dirname "$0"`"`` + LF + `java -Xms256M -Xmx256M -jar TheAbbeyOfCrimeExtensum.jar <code>`, **no trailing LF**. `.bat` (58 B): the java line alone, no cd, no trailing newline. es, en, fr, it, pl only. The Swedish `game/TheAbbeyOfCrimeExtensum(Swedish).sh`/`.bat` are the English ones with ` en` → ` de`, the same 90/58 B (`tools/build.py` step 10). | VERIFIED (`od -c`) |
| JVMs | `java` = OpenJDK 11.0.32 (what the launchers use here); OpenJDK 8 = `/usr/lib/jvm/java-8-openjdk-amd64` (1.8.0_504). Game classes are major 51. | VERIFIED |
| jar | not signed. META-INF = `MANIFEST.MF` (`Main-Class: abadia.Abadia`, CRLF) + `services/javax.sound.sampled.spi.{AudioFileReader,FormatConversionProvider}`. The services entries are required for OGG audio. | VERIFIED |

Pristine fingerprints, for "only my patch changed" checks (sha256 prefix / size):
`abadia/j.class 79729f57317f67d1 12022`, `k.class 57df78b2654f5bd9 35553`,
`w.class ef7f3a737765b88a 6384`, `E.class 5d8fecda65d038ce 15649`,
`y.class 8bb617b59d28b7af 4853`, `v.class 664a36f5a3a53357 2791`,
`Abadia.class 477ae72687bbf724 23643`, `res/fuente.png f10a02e03cd0ed9e 2448`,
`res/letras 047ebed09a422ebf 5564`.

### 0.1 Corrections to the implementation prompt's assumptions

1. **The 185 strings are not all in `a`.** Each text class has `a` (4, end-of-game screen),
   `c` (2), `d` (2), `e` (3), `f` (10, pause menu) and `g` (164, in-game messages):
   4+2+2+3+10+164 = 185. `g[0]` is `""` in every language, so 184 are non-empty. Only **143** `g`
   entries are ever shown; 21 are dead (§1.6).
2. **`b` is not a char→glyph map.** It is 49 bytes = the 7 HUD canonical-hour names × 7 raw
   `fuente.png` cell codes (§2). The char→glyph map is a single `lookupswitch` in the private
   `static void j.a(int ch, int x, int y, Graphics)`, shared by all languages (§3.2). There is no
   per-language glyph map.
3. **So Å cannot be "wired up through the Swedish `b` map".** Å (U+00C5) is not in the switch and
   draws nothing. It needs a bytecode patch of `abadia/j.class` plus a new ring glyph (§3.4,
   DECISIONS D5). `b` matters only for HUD hour names, which can use precomposed glyphs (§2.4).
4. `abadia.j` picks `g` (messages, `j.bS`) and `a` (end screen, `j.bT`). `v` picks `b`; `w` picks
   `c d e f`. The language **index** `Abadia.a` is read in E, j, r, v, w, y. The **code array**
   `Abadia.u` is read in `Abadia.main`, r, v, y (§5).
5. Ä/Ö/Ü handling is not a de-slot feature. The shared switch draws Ä, Ö, Ü as A/O/U plus a
   diaeresis overlay for every language. `k.g[1]` starts with the glyph test `"@3 ÄËÜß …"`; Ë does
   not draw.
6. The `de` class `k` is not "mostly Spanish": `a c d e f` and the hour bytes are German; `g` has
   48 German entries and 116 still byte-identical to Spanish.
7. **Per-language text also lives outside `k`.** `w.t[4]` = `"DÍA "` and `w.u[4]` = `"VACÍO"`
   (save/load menu) and `E.h[4]` = `"Die Abtei Des Crime Extensum"` (window title). `w.t[4]`/`w.u[4]`
   share constant-pool entries with Spanish (§1.10, §5).
8. **The parchment reader does no charset decoding.** It is a byte switch: some cp1252 single
   bytes plus 13 UTF-8 two-byte pairs, whose lead byte is ignored. Every encoding of
   å ä ö Å Ä Ö hangs or mis-draws. Swedish needs new `letras` glyphs in free table slots, written
   as those slot bytes (data only, no code change, §4.7). The files also need a `0x1A` terminator.
9. "Intro images luna/monje/niebla/ventana are language-neutral" is true for their content, but the
   code loads all 11 intro files from `res/<lang>/intro/`. `res/de/intro/` already holds identical
   copies; keep them.
10. **Runtime recipe.** On a 1280×800 Xvfb the 1296×871 window is placed at (−8,−35), partly
    off-screen; use 1920×1080. `xdotool key` (12 ms press) and `xdotool --window`
    (XSendEvent) are not reliable. Keys must go by XTEST (`keydown`/`keyup`, held ≥ 1 frame,
    0.2–0.25 s used) while X focus is on Java's 1×1 `FocusProxy` child window. A null sink
    alone is not proven silent: the game opens the first mixer that accepts 44.1 kHz/16-bit/stereo,
    which could be real hardware. All of this is implemented in `tools/run_headless.sh` (§7).
11. **"Markers identical to source" applies to the `@N` speaker sequence**, which must be
    identical. `_` (page break) and `*` (line break) are layout choices; their counts already
    differ between shipped languages.
12. **The first in-game message is Remigio's `g[49]`, not the abbot's welcome.** The abbot's long
    welcome `g[1]` needs the player to follow Remigio to the cell; the automated tour does not
    reach it. **VERIFIED reachable in Phase E:** following Remigio within his ±8-unit box and then
    stepping into the cell starts `g[1]` (24/24 pages in runs 1, 2 and 4), then `g[5]`. Route in
    §7.8; evidence `screenshots/runtime_sv/opening/INDEX.md`,
    `work/phaseE/runs/run{1,2,4}/agent/events.log`.
13. Parchment files need the `0x1A` terminator and CR-only line breaks. LF is a forced page
    break, so CRLF puts one line per page.
14. `translation/strings_sv.tsv` must be keyed by **(array, index)**, not by a flat 0..184 index.
    `work/phaseA/context.tsv` uses that key (§1.11).

### 0.2 Disputed claims and how they were resolved

Each row below was re-checked for this synthesis (`work/decompiled_vf/abadia/{j,y}.java`, javap
greps, `work/phaseA/scripts/format_checks.py`, `text_sim.py`) or settled by two independent
reviewer measurements that agree.

| topic | first claim | resolved truth |
|---|---|---|
| message without leading `@` | speaker stays from the previous message | first 3 chars lost **and speaker = 0** (Guillermo): `c(int)` sets `co = 0` (j.java:418-432) |
| `_` edge cases | a leading `_ ` line is always dropped; consecutive `_` never give empty pages | only a first line **exactly** `"_ "` is dropped (`equalsIgnoreCase("_ ") && cw==0`). `" _ "` (an empty token before `_`) is kept → **blank page** (~41 ticks). A standalone `_` as the **last** token that falls at a page start → **AIOOBE** in `e()`. `_` in the middle of a token (`A_B`) draws the rest 10 px lower. |
| trailing space | always crashes | crashes **only if `bR==0`** when the last char is consumed. That happens when the last page cost ≥ 40, or for a single-page message after one that left `bR=0`. It is a one-off exception on the EDT, after which the message closes. Still a hard error. |
| word > 35 chars | the game "stalls forever" (harness) | **no hang**: blank page(s), the rest of the message is never shown, and the message ends after its remaining chars are counted (+17 ticks). `cq++` runs every tick. Still a hard error. |
| page timing | page ≥2 shows max(P,40); `bR` normally 0 | `bR` is **never reset** by `c(int)`. A multi-page message whose last page has P<40 leaves `bR = 40−P_last`, which is added to the first page of the next multi-page message. Middle pages ≈ max(P,41) ticks; last page = (P_last−1)+17 (§1.3) |
| `j.bP` references | 81 reads outside `j` | **79 getstatic + 2 putstatic** (b.java@245 load, E.java@774 restart). Re-counted. |
| menu row limit | 27 glyphs on every row | opaque paper allows **27,26,26,25,25,25,27,27,27,27** for rows 0..9 (`format_checks.py`, alpha≥128 over the glyph rows) |
| JOptionPane texts | language-indexed | **not** indexed: fixed Spanish for every language, optional |
| `Abadia.a` reads | 19 sites | **14** getstatic `Abadia.a` (E1 j2 r1 v2 w6 y2) + 5 getstatic `Abadia.u` |
| `k` class shape | flags must match exactly | the JVM only needs non-private static fields with the same names and descriptors and class version ≤ target (≤52 for Java 8). Keep the original flags and version 51 anyway (§1.12). |
| parchment Latin-1 `0xC4`/`0xC5` | "swallows the next byte" | the **lead byte vanishes** and the next byte is drawn (through the 13-entry trail table, else as itself): `"Fr\xC5ga"` → `Frga` |
| parchment prefix + control byte | permanent freeze | apostrophe/lead byte followed by space/CR/LF/1A → **one** uncaught AIOOBE, then recovery: `m` already points at the control byte (y.java case 1). Only a **plain byte < 44** or a **missing 0x1A** freezes permanently. |
| letras glyph count / page count | 64 glyphs, 91 pages | **62** populated table entries, 19 empty; shipped texts = **93** pages (re-counted) |
| letras size cap | file ≤ 22824 B | the u16 table caps the glyph **start** offset at 22824 (addr 0xFFFF); the file may be longer |
| parchment line 11 | not given | paper edge **245** on body rows; the bottom of line 11 has a dark notch (x≈98..111) and curves in (§4.5) |
| in-game font after the Å patch | `}` draws blank | with the ring font, `}` (125) draws **a bare ring**; forbid it |
| hour bytes to avoid | 33 39 44 120 | also **37 `%` and 95 `_`** (line breaks in the save-slot label) |
| ASM frame check | `CheckClassAdapter.verify` catches bad frames | it **accepted** a broken-frame class. Use `ClassReader.accept(new CheckClassAdapter(cw, true), 0)` **and** load/link under `-Xverify:all` on JDK 8 and 11. |
| temp files | 7 files, 247 MB | **10** `abbey*.tmp` (one per bgm track, `c/a.java:18-28`), 258,056,288 B = 246 MiB |
| es intro timings | same plateau starts as en | es plateau **starts** are 2.60/10.30/16.94/24.05/30.55/37.09/41.97/46.31 s; en and es differ by up to ~0.85 s |
| idle game over | deterministic at ~630 s | the sequence is reliable; the timing varies between runs (the unseeded `java.util.Random`, or start timing: §7.4): 258.6 s (es) vs 274.2 s (en) after play start |
| image corrections | (several) | applied in §6: fraktur has only capitals A C D E I J L M N P R T U; pulsa outline = 1 px opaque + 1 px semi-transparent black; existing moon-window intrusions; per-language baselines |

---

## 1. Text tables (`abadia.m l o n k p`) and the message system (`abadia.j`)

### 1.1 Classes and fields (VERIFIED: reflection dump, raw constant pool, javap)

Language index → class: 0 es=`m`, 1 en=`l`, 2 it=`o`, 3 fr=`n`, **4 de=`k`**, 5 pl=`p`.
Each class (`abadia.m l o n k p`) is `public final` (flags 0x0031), major 51, with **only `<clinit>`**
(no constructor, no SourceFile). Each of the 185 `String` constants has its own Utf8 entry.

| field | descriptor / flags | entries | read by | meaning |
|---|---|---|---|---|
| `a` | `[Ljava/lang/String;` 0x19 public static final | 4 | `j.<clinit>` → `j.bT` → `j.a` → `E` | end-of-game screen lines |
| `b` | `[B` 0x18 static final | 49 | `v.<clinit>` → `v.g` → `v.a` | HUD hour names, 7×7 raw cells |
| `c` | `[Ljava/lang/String;` 0x08 static | 2 | `w.<clinit>` → `w.r` → `w.n` | OFF/ON (shown as NO/YES) |
| `d` | same 0x08 | 2 | `w.q` → `w.m` | control mode CLASSIC/DIRECTIONAL |
| `e` | same 0x08 | 3 | `w.s` → `w.o` | sound mode |
| `f` | same 0x08 | 10 | `w.p` → `w.l` | pause-menu rows |
| `g` | `[Ljava/lang/String;` 0x18 static final | 164 | `j.<clinit>` → `j.bS` → `j.b` | in-game messages |

`k` is referenced by exactly 7 getstatics (j.<clinit> 31 `k.g`, 75 `k.a`; v.<clinit> 105 `k.b`;
w.<clinit> 66 `k.f`, 110 `k.d`, 154 `k.c`, 198 `k.e`). None of the arrays is a compile-time
constant, so nothing is inlined elsewhere.

Canonical dump of all six languages: `work/phaseA/strings_all.json` (UTF-8; `b` as unsigned ints;
C1 controls escaped). Check it against the raw pool with
`uv run work/phaseA/scripts/text_javap_check.py work/phaseA/strings_all.json work/phaseA/dump/javap work/jar`
(expected `ALL OK`). javap's text output trims trailing spaces (`"SONIDOS: "` prints as
`SONIDOS:`); the pool has them.

**Sizes must not change** (VERIFIED from code). `f` must be exactly 10, in order: `w.a()` switches
on 0..9, wraps the cursor at `f.length`, and sizes the box `f.length*10+20`. `e` must be exactly 3:
`c.b.J = ++J % e.length` drives `switch` 0/1/2. `c` and `d` are indexed 0/1. Only `a[0..3]`,
`b[0..48]` and `g[0..163]` are ever read, so larger `a`/`b`/`g` would be harmless, but keep them exact.

### 1.2 Message start (`j.java:394-432`, VERIFIED)

- `j.a(int i)`: if a message is showing (`bP`), it **returns false and drops the request**;
  otherwise it calls `c(i)`. `j.b(int i)` **interrupts** (`bP=false; d(); c(i)`). `j.a(int[])` is a
  queue, used only with 1-element arrays via `abadia.b.d.a`.
- `c(int i)`: `bQ=false; cn=i; cl=false; bP=true; cm=b[i]; co=0; cq=0; cp=0;`
  `cs = (cm = cm.replace("@"," _ @").substring(3)).split(" "); ct=0; cu=0; e(); f();`
  It does **not** reset `bR` (see §1.3).
  - **Every displayed `g[i]` must start with `@N`.** The replace turns the leading `@` into
    `" _ @"`, and `substring(3)` removes exactly that prefix. Without it the first 3 real chars are
    lost and the speaker is 0. A string shorter than 3 chars with no `@` throws
    StringIndexOutOfBounds. `g[0]=""` would throw; it is never shown.
  - Every `@` inside the text also becomes `" _ @"`, so **every `@N` starts a new page**.

### 1.3 Pagination `e()`, drawing `f()`/`c()`, scrolling `b()` (j.java:434-591, VERIFIED)

**`e()`** fills up to **2 lines** (`cv = new String[2]`). For each token `cs[ct]`:
- if `len(line so far) + len(token) <= 35` (`bipush 35`): a token starting with `@` sets
  `co = Integer.parseInt(token without "@")` and adds `len+2` to the page budget `cu`. Any other
  token is appended as `token + " "` and adds `len+1`.
- after each token: if the line contains `*`, the line ends. If the line contains `_`, or no tokens
  remain, the line **and the page** end.
- if the token does not fit, the line ends and the token starts the next line.
- a first line exactly equal to `"_ "` is dropped and the page restarts.
- Because the line buffer includes each word's trailing space, a line shows **at most 35 visible
  glyphs**. 35 fits; 33+1+2 does not.

**`f()`**: a new 320×30 ARGB image; draw `dialog.png` (320×30), then line k with
`j.a(cv[k], 32, 5+12k)`. **`c()`** (every frame while `bP`) blits it at screen (0,146). Text cells
are therefore x 32..311, line 1 y 151..158, line 2 y 163..170, with accents 1–2 px above. The face
is drawn from `caras.png` (340×80 = 17 columns × 4 mouth frames of 20×20) at clip (6,153,20,20),
column = speaker id. The blinking "more" glyph 95 (▶▶) is drawn at (306,164) only while
`!abadia.b.i.c` (scripted scenes). It overlaps the 35th glyph of line 2 (x 304–311). In the
shipped languages that is cosmetic: pristine es already has 20 such pages, en 24, pl 26, fr 33.
**Swedish rule: the visible part of line 2 is ≤ 34 glyphs on every page** (trailing `_` and
spaces do not count; DECISIONS D13). Whether ▶▶ shows depends on `b.i.c` at runtime, not on the
string, so the rule covers every page, exactly as the harness warning does
(`line 2 has 35 chars; char 35 … is overlapped by the blinking continue-marker`). A page whose line 1
fills 35 glyphs may end in a `_` that leaves line 2 empty (`NU ÄR DE UPPTAGNA MED SINA SYSSLOR.@0`
in g159: line 1 is exactly 35 glyphs, and the `_` that the game inserts for `@0` falls alone on
line 2; never type a `_` before `@`, §1.4). VERIFIED: the Swedish render has no such warning
(`screenshots/strings/de/report.txt`), and live play confirmed that Space advances and ▶▶ shows only in scripted messages (g1, g53,
Severinus's tour), not in g49, the walk, g54 or g145 (`screenshots/runtime_sv/opening/INDEX.md`).

**`b()`** runs once per logic tick (odd frames, E.java:207) and acts only when
`Abadia.ak % 3 != 0`, i.e. **one tick per 3 frames**. The frame period is 33 ms, so 1 tick ≈ 0.1 s
and text runs ≈ 10 chars/s. `C.h`/`C.k` (fast/slow modes) are never set true: dead code.
- Each tick: if `cu==0 && bR!=0` then `bR--`. Otherwise consume one char (`cq++`, `cu--`; random
  voice blip `ck[co]` for non-space, non-`@`; `*` counts as a space). When `cq == len(cm)`, set
  `cl=true, cp=17` (a **17-tick linger**). When `cu<=0 && bR==0`, build the next page (`e(); f()`)
  and set `bR = cu<40 ? 40−cu : 0`. After the linger, `bP=false; Abadia.am=true`.
- **Durations** (ticks): single page = `len(cm)+17`. First page ≈ P₁ + carried-over `bR` (+1).
  Middle pages ≈ max(P,41). Last page = (P_last−1)+17. A multi-page message with P_last<40 leaves
  `bR = 40−P_last` for the next multi-page message; single-page messages pass it through unchanged.
  Measured: es g[158] lasts 93 ticks alone but 120 right after g[157] (leftover 27).
  Use `scripts/text_sim.py` `simulate(text, bR0=<previous leftover_bR>)` for exact numbers.
  Frame counts depend on the `ak` phase (±3 frames); compare **ticks**.
- **Space** (`C.e`) skips to the end of the current page only if `!abadia.b.i.c` (Guillermo under
  script control). It sets `bQ=true, bR=0`. In free play `b.i.c` is true, Space is the action key,
  and messages advance on their own.
- `j.b()` and `y.a()` run inside `E.a(Graphics)`, called from `F.paint` on the Swing EDT. An
  exception there aborts one paint and is logged; it does not kill the game (INFERRED; consistent
  with every runtime log).

### 1.4 Markers and hazards in `g` (VERIFIED with the real `abadia.j` driven headlessly)

| construct | effect | rule |
|---|---|---|
| `@N` at index 0 | speaker N (0..14): face column N, voice `j.ck[N]`; not drawn; costs `len+2` ticks | required on every used message |
| `@N` mid-string | becomes `" _ @N"`: ends the page, then changes speaker | glue it to the preceding text (`…ASÍ.@0 YA`), **no space before `@`** (at a full line a space gives a blank page) and **never `_` right before `@`** (`_ @0` gives a blank `" _ "` page) |
| `@` + non-digits (`@0HOLA`, `@1_4`, `@3<TAB>`) | `NumberFormatException` (Java `parseInt`) | `@` + ASCII digits 0..14 + (space or end of string) |
| `@15`, `@16` | `ArrayIndexOutOfBounds` on `ck[co]` **every tick**: the message never ends (freeze) | speaker ≤ 14 |
| `@14` | works, but face column 14 is empty and the voice is Adso's | unused; avoid |
| `_` | in `e()`: ends line and page; in `j.a(String)`: line break (+10 px), invisible | only at the **end** of a token (`HERMANO._`) or as a standalone token; never mid-token |
| `*` | ends the line (the page continues); draws an empty 8-px cell | only at the end of a token (`MURIÓ.*`) |
| runs of spaces | each empty token = 1 tick pause, **and** counts toward the 35-glyph line width (can indent the next line) | keep the source's deliberate 8-space runs (es g[126], g[138]); otherwise single spaces |
| `%` | not handled by `e()`; `j.a(String)` draws it as a line break +14 px mid-line | never in any string |
| trailing space | conditional AIOOBE in `e()` (see §0.2) | never |
| final standalone `_` | AIOOBE when it lands at a page start | never end with `_`, `*` or a space |
| token > 35 chars | blank pages, rest of the message lost | every word ≤ 35 (shipped max 22) |
| lowercase a–z | raw special glyphs (§3.3); `x` draws Ê | UPPERCASE only (en g[152] `SEVERINUS's` is an original bug: its `s` draws a floating dot) |

The `@N` sequence of every used index is identical in all six languages; the only differences
are dead indices 2/3, where it has `@0` (VERIFIED, `scripts/text_markers.py`). **Swedish must copy
the es `@N` sequence exactly.** `_`/`*` counts may differ.

### 1.5 Speaker ids (VERIFIED: `j.ck`, `caras.png`, texts)

| id | speaker | voice | `@N` occurrences (es, used msgs) |
|---|---|---|---|
| 0 | Guillermo (William) | vozguillermo | 140 |
| 1 | Adso | vozadso | 33 |
| 2 | Severino | vozseverino | 24 |
| 3 | Abad (Abbot) | vozabad | 34 |
| 4 | Malaquías | vozmalaquias | 4 |
| 5 | Berengario | vozberengario | 9 |
| 6 | Bernardo Gui | vozbernardo | 14 |
| 7 | Jorge | vozjorge | 14 |
| 8 | Remigio | vozremigio | 15 |
| 9 | (unused; hat face) | vozguillermo | 0 |
| 10 | Salvatore | vozsalvatore | 7 |
| 11 | Aldeano (villager, g[66]) | vozmalaquias | 1 |
| 12 | Ubertino | vozubertino | 8 |
| 13 | Nicola | voznicola | 17 |
| 14 | (unused; empty face) | vozadso | 0 |

`caras.png` column 16 holds a face and the voice `vozchica` exists, but neither can be reached
(`ck` has 15 entries).

### 1.6 Used and dead indices (VERIFIED independently three times with ASM data flow)

The 143 `public static final int` fields `j.c … j.bO` (computed in `j.<clinit>`; values in
`work/phaseA/j_consts.json`) are the only indices that reach any display call (`j.a(I)`, `j.b(I)`,
`j.a([I)`, `b.d.b(I)`, `b.d.a(IIZI)`, `g.a(II)`, through `b.a.e` and arrays `b.a.h/i`, and the saved
`j.cn`). No index is computed arithmetically.
**Dead (never shown): 0, 2, 3, 13, 16, 25, 26, 27, 28, 29, 30, 32, 38, 40, 41, 42, 44, 45, 46, 47, 48**
(21 indices; leftovers of the 1987 table, e.g. 16 "¿DORMIMOS?", 48 "S : SÍ * N : NO").
`g[2] g[3] g[45] g[46]` have no leading `@` (in it only 45/46).

Rules for Swedish:
- **`g[0]` stays `""`**, as in every shipped language. `b.a.e` is reset to the literal 0, so index 0
  is statically reachable in `b/a.java:547,635`, but every language would break there identically;
  INFERRED unreachable in practice.
- Translate the other dead entries anyway (harmless, and it keeps the "no leftover Spanish" check
  clean), but **keep the es shape**: the same `@N` sequence and the same "starts with `@`" flag
  (`render.sh --ref-lang es` treats a mismatch as an error).
- Message ids worth knowing: `j.c=1` (abbot's welcome), `j.E=49` (Remigio's welcome, the first
  message of a new game), `j.F=50`, `j.G=51`, `j.bI=157`, `j.bJ=158`, `j.bK=159`. **g[16] "¿DORMIMOS?"
  is dead; g[17] is the lamp message `j.o`.** runtime.md §3 had this off by one, and `b.i.e(17)` sets
  an orientation, not a message.

### 1.7 Length limits (glyphs = chars; each char advances 8 px)

| array | limit | why (VERIFIED) |
|---|---|---|
| `g` (used) | **≤ 35 glyphs per line** (automatic greedy wrap at spaces); **every word ≤ 35**; 2 lines/page; **no total limit** | `bipush 35` in `e()`. Longest shipped: es g[122] 2305 chars, it g[122] 2504. The class-file limit is 65535 bytes of modified UTF-8 per string. |
| `g` line 2 | **≤ 34 visible glyphs** on every page | the ▶▶ marker covers glyph 35 in scripted scenes (§1.3, D13) |
| `g[157]` | **≤ 215 ticks** (isolated, `text_sim`; = 645 frames) | Remigio's day-1 walk: the measured window is 220–223 ticks (§1.8, D12) |
| `g[158]` | **≤ 96 ticks** isolated (≤ 129 when chained after 157) | §1.8 (measured window 187) |
| `g[159]` | **≤ 211 ticks** | §1.8 (measured window 319) |
| `g[51]` | **≤ 77 ticks** | §1.8 |
| `a[0]`, `a[2]`, `a[3]` | **≤ 40** | centred `x = 160 − 4·len` on 320 px (E.java:378-381) |
| `a[1]` | **≤ 37**, and **must start with a space** | drawn as `String.valueOf(pct) + a[1]`; pct is 0..104 (`7·(day−1) + hour + g.c()` (+5), 0 if < 5; `g.H` = 51 flags) |
| `f[i]` (+ value) | recommended **≤ 23** (inside the 190-px highlight bar, x 65..254); hard **27, 26, 26, 25, 25, 25, 27, 27, 27, 27** for rows 0..9 | rows at y = 32+12i, centred, on `pergamino2.png` 220×136 at (50,20); hard limits from the opaque paper (`scripts/format_checks.py`). Shipped max: fr 23 (`CONTRÔLES: DIRECTIONNEL`, `MONTRER LES EXTRAS: NON`). |
| `f[3]` + `e[*]`, `f[4]`/`f[6]`/`f[7]` + `c[*]`, `f[5]` + `d[*]` | the **combination** obeys the row limit | row 3 = `f[3]+e[c.b.J]`, row 4 = `f[4]+c[music?1:0]`, row 5 = `f[5]+d[Abadia.c?0:1]`, row 6 = `f[6]+c[fullscreen]`, row 7 = `f[7]+c[extras]`. Labels must end with their own separator (`": "` or `" "`; es `"CONTROL "` has no colon). |
| `b` | **exactly 7 cells per hour** | §2 |
| `w.t[4]` | **≤ 6** including its trailing space | save label = `t + day digit + " " + 7 hour cells` ≤ 15 glyphs (120-px bar); pl `"DZIEŃ "` gives exactly 15 |
| `w.u[4]` | **≤ 15** | the same 120-px bar |

Menu/end/save strings go through `j.a(String)`: `_` and `%` are line breaks there, and centring
counts every char.

### 1.8 Where length changes gameplay (VERIFIED in code)

- **The game clock never advances mid-message.** The `D.e` hour advance is deferred while `j.bP`
  (E.java:393-400), and the `D.c` countdown re-arms while `bP` (D.java:37-45). Scripts poll `!j.bP`
  before their next step (79 reads outside `j`). The end screen and the Q+R mirror trigger require
  `!bP`. Longer text only delays the next event; nothing is skipped.
- **Saves** store only `writeBoolean(bP)` + `writeInt(cn)`. Load calls `j.b(cn)` on the **current**
  language's table. A save is therefore language-neutral, provided `k.g` keeps the 164-entry order.
- **Remigio's day-1 walk** (`b/m.java:141-167`): 157 starts with `j.b` at the start of the walk to
  waypoint 8. On **arrival** at waypoints 8, 9 and 10, `j.b(158)`, `j.b(159)` and `j.b(51)` start
  **interrupting** (no `!bP` wait), so unread pages are cut. 51 is in turn interrupted by the abbot's
  `j.b(1)` once he sees Guillermo. The block runs only while `Abadia.t.v()`; otherwise Remigio's
  40-tick counter fires `j.b(50)`. Shipped and Swedish ticks (`text_sim`, isolated / leftover
  `bR`), and the walk windows measured in Phase E:

  | idx | es | en | it | fr | pl | sv (built) | window, runs 1 / 2 / 4 | cap for Swedish |
  |---|---|---|---|---|---|---|---|---|
  | 157 | 221 / 27 | 205 / 0 | **232** / 33 | 212 / 32 | 194 / 0 | 194 / 0 | **220 / 223 / 223** (until 158) | **≤ 215** |
  | 158 | 93 (120 after 157) | 94 | **96** (129 after 157) | 91 (123) | 86 | 88 (88 after 157) | 187 / 187 / 187 (until 159) | ≤ 96 isolated, ≤ 129 chained |
  | 159 | 192 / 17 | 185 / 14 | 183 / 17 | **211** / 3 | 182 / 9 | 177 / 18 | 319 / 319 / 319 (until 51) | ≤ 211 |
  | 51 | 68 | 63 | **77** | 74 | 55 | 67 | ends on its own; the abbot's `g[1]` waits for the player | ≤ 77 |

  **Walk timing (VERIFIED, Phase E).** The window is the time from a message's `MSG_START` to the
  next one's (`ak` frames / 3): g157 6351 → 7011 (run 1), 1233 → 1903 (run 2), 1263 → 1931 (run 4).
  Remigio never paused (one step per 8 frames, 14-frame turns at corners), so these are the
  natural pace and the shortest windows. Live durations are within 1 tick of `text_sim` (g157
  shown 580 frames = 193 ticks in all three runs, `text_sim` 194), and so are the page starts. So es
  (221) and it (232) lose part of their 17-tick linger at waypoint 8; the old cap "≤ 232" (the
  longest shipped) was too long. **The g157 cap is 215**: the whole message, linger included, ends
  ≥ 5 ticks before the shortest window. 158/159/51 keep the shipped caps, far inside their
  windows. Enforced by `tools/lint_strings.py` (`TICK_CAPS`). Evidence:
  `work/phaseE/runs/run{1,2,4}/agent/events.log`, `screenshots/runtime_sv/opening/INDEX.md`.
  Also keep the last page of 157 long (≥ 40 budget), so it leaves no `bR` that delays 158 (the
  Swedish leaves 0; the lint warns otherwise). **The 215 cap assumes that g49 leaves `bR` = 0.**
  g157 starts right after g49 and `bR` is never reset (§1.3), so a g49 whose last page has a
  budget under 40 would add up to 39 ticks to g157's first page, and the lint (which simulates
  g157 alone, `bR0 = 0`) would not notice. Keep g49's last page at a budget of 40 or more: the
  Swedish g49 (145 ticks) leaves 0, its last page `JAG BER ER ATT FÖLJA MIG. ABBOTEN VÄNTAR PÅ
  ER.` having a budget of 48 (`text_sim`).
- **Dropped messages:** fire-and-forget `j.a()` calls (abbot 68 at b/a.java:255, 94, 116, 78/79,
  Adso 33/34, Guillermo 89) are lost if another message is showing. Longer ambient text widens that
  window slightly. State machines continue (no soft-lock; INFERRED). French already ships at +12 %
  overall (single messages up to 2.32× es) without problems.
- **Message 127** (and 125) name QUATUOR. The mirror opens only when `!bP`, flag D set, flag E not
  set, Guillermo at (o≤34, p=108, floor 24, facing 2) and **keys Q (81) and R (82) both held**
  (E.java:334-345). **Swedish must keep the word QUATUOR**, with Q as its 1st and R as its 7th letter.

### 1.9 Characters drawable on the `j.a` paths (messages, menu, end screen, save labels)

VERIFIED by rendering all 65536 BMP code points through the private glyph routine: 106 draw ink.
**Allowed for Swedish:** space, `A–Z`, `0–9`, `. , : ; ? ! ' -`, `Ä Ö É` (plus the rest of the
switch set: `À Á Â Ç È Ê Ì Í Î Ñ Ò Ó Ô Ù Ú Û Ü ß Ą Ć Ę Ł Ń Œ Ś Ź Ż ¡ ¿`), and **`Å` only after the
j.class patch (§3.4)**. Markers `@ _ *` in `g` only.
**Forbidden:** lowercase (a–t, x draw special glyphs; since the Swedish font, `w` (119) draws the
precomposed HUD Ö of cell 74 (§2.4); u v y z draw blank), `" # $ % & ( ) + / [ { | } ~`,
`< = > @ \ ] ^ _` and the backtick (0x60) as literal text (they draw comma, diaeresis, ß, ¿, ¡, !, Ñ, ▶▶, acute),
`Å` before the patch, `Æ Ø Ë Ï Õ Ã`, typographic quotes/dashes/ellipsis (`’ “ ” – — … « »`),
NBSP, TAB. Use `...` (three periods) and `'` (ASCII apostrophe).
VERIFIED on the built jar: the harness's empirical ink map lists `w` and `}` among the inked
ASCII codes and Å among the drawable code points (`screenshots/strings/de/report.txt`).

### 1.10 Text outside the text classes (VERIFIED: string constants of every non-text class)

| where | value per language index 0..5 | slot 4 today | patch |
|---|---|---|---|
| `w.t` (save label prefix) | `DÍA `, `DAY `, `DIE `, `JOUR `, `DÍA `, `DZIEŃ ` | Spanish, **shares CP #7 with es** (ldc at w.<clinit> 218 and 238) | new constant for index 4 only (ASM, `ldc_w`); never edit #7 |
| `w.u` (empty slot) | `VACÍO`, `EMPTY`, `VUOTO`, `VIDE`, `VACÍO`, `PUSTE` | Spanish, **shares CP #15** (ldc 256 and 276) | same |
| `E.h` (AWT window title, system font) | `La Abadía del Crimen Extensum`, `The Abbey of Crime Extensum`, `L'Abbazia del Crimine Extensum`, `L'abbaye du crime Extensum`, `Die Abtei Des Crime Extensum`, `The Abbey of Crime Extensum` | German; String #7 → Utf8 #775, referenced only there | in-place or ASM |
| `w` JOptionPane | `Los datos guardados están corruptos. `, `Error al grabar el fichero. ` + exception, title `ERROR GRAVE` | the same in **every** language (not indexed) | none: kept Spanish (DECISIONS D16) |
| not player text | `d` (Spanish debug overlay), `r` `v1.3e` (AWT TimesRoman 12 at (10,10) on the loading screen), `y` `Caracter:` (stdout debug) | | none |

`w.class` has 464 CP entries (new constants need `ldc_w`; ASM handles it). Proven tool:
`work/phaseA/refute_deslot_1/scripts/PatchTW.java` (usage `PatchTW <in.class> <out.class> 4 '<old>' '<new>' [4 '<old>' '<new>' …]`;
it replaces the LDC after `ICONST_4` in `<clinit>`, needs exactly 1 hit per pair, and uses
`ClassWriter(reader, 0)` to keep the pool). VERIFIED on JDK 8 and 11 with `-Xverify:all`:
`t=[DÍA ,DAY ,DIE ,JOUR ,DAG ,DZIEŃ ]`, `u=[…,TOM,…]`, Spanish unchanged. The same tool works on
`E.class` (`4 'Die Abtei Des Crime Extensum' '<title>'`, VERIFIED, only `h[4]` changes).
`w.<clinit>` and `E.<clinit>` have no branches, so no frames are involved. The build runs the
maintained port `tools/java/PatchStrings.java` (same method; replacements come from a spec file,
`work/build/patch_w.spec` and `patch_E.spec`), and `tools/java/VerifyClasses.java` checks the result
(step 9b). Note that `tools/run_headless.sh` finds the window by the title regex
`Abad|Abbey|Abbaz|abbaye|Abtei` (line 56, hard-coded), so a new title must match it, or the regex
must be extended in all three copies (§7.6).

### 1.11 Per-index context table: `work/phaseA/context.tsv`

Built by `uv run work/phaseA/scripts/make_context_tsv.py work/phaseA` from `strings_all.json` and
`text_index.json`. 195 rows: `g` 0..163, `a` 0..3, `b` 0..6 (as 7-char cell strings, lowercase =
raw special glyphs), `c`, `d`, `e`, `f`, plus `w.t` 4, `w.u` 4, `E.h` 4.
Columns: `array index context speaker max_len es en`. `context` holds used/dead, trigger
class, call kind (a = dropped if busy, b = interrupts, d.b = conversation, d.a = proximity
once, g.a = one-shot flag, hot = location hotspot), the condition (day/hour/place), es pages and
ticks, and flags (QUATUOR, pause runs, length-sensitive). `speaker` is the `@N` sequence with names.
**Fields are raw: trailing spaces are significant** (e.g. `f[3]` `SONIDOS: `). Fuller per-index
metadata, including INFERRED trigger conditions: `text_index.json` and `text.md` §9.
The project keeps a byte copy as `tools/data/context.tsv`, the lint's `--ref` table, and
`translation/strings_sv.tsv` starts with the same columns. Their `context` and `max_len` cells are
the Phase A notes and are not kept current: for g157 they say `keep <=232 ticks` (only the TSV's
`max_len` cell was changed, to `keep <=215 ticks (DECISIONS D12)`), and the `g` rows say
`35 glyphs/line` with no line-2 rule. The limits in force are those of §1.7 and §1.8 (g157 ≤ 215
ticks, D12; visible line 2 ≤ 34 glyphs, D13), enforced by the lint and the render (§1.13). Against
the reference table the lint checks only the row keys and their order and the `es` and `en`
columns.

### 1.12 Regenerating `k` (Decision 2)

VERIFIED on JDK 11 (`javac 11.0.32.1`): `javac --release 7 -encoding UTF-8` of
`package abadia; public final class k { public static final String[] a = {…}; static final byte[] b = {…};
static String[] c, d, e, f = …; static final String[] g = {…}; }` gives major **51**, class flags
**0x0031**, fields `a` 0x19, `b` 0x18, `c d e f` 0x08, `g` 0x18, in source order a..g. The only
difference from the original is an extra **`public abadia.k()` default constructor** (javac
always emits one; nobody instantiates `k`). So the `javap -p -s` proof compares the
**fields** (name, descriptor, flags), the class flags and the major version, and allows the extra
`<init>` (DECISIONS D2a). Byte literals > 127 would need a `(byte)` cast; Swedish hour bytes are
all ≤ 124. Java version limits (reviewer-tested): `--release 8` (v52) also links on JDK 8 and 11;
`--release 11` fails on JDK 8; private fields → IllegalAccessError; wrong `b` type → NoSuchFieldError.

### 1.13 Lint checklist for every Swedish string (Phase C/E)

`harness/render.sh` (§8) is the authoritative checker: it runs the real `e()`, so `parseInt`
behaves exactly as in the game. It does **not** reject lowercase or unknown-but-inked chars, so the
build lint must add:
1. sizes a=4, b=49, c=2, d=2, e=3, f=10, g=164; `g[0] == ""`.
2. each `g[i]` (i≠0) starts with `@` exactly when es does; `@N` sequence == es; every `@` matches
   `@(?:[0-9]|1[0-4])(?= |$)` (ASCII digits).
3. charset whitelist (§1.9); no lowercase; no `%`; no `_`, `*` or `@` outside `g`; `_`/`*` only at
   token ends; no space before `@`; no `_ @`; no leading/trailing whitespace; no NBSP or TAB; spaces
   single, except runs that es also has (the lint matches them by count and length, not by
   position; keep them at the same place by hand).
4. every word ≤ 35; `render.sh` reports no missing glyph, crash or no-progress.
5. length limits §1.7 (menu combinations, end screen, `w.t`/`w.u`), Remigio tick caps §1.8
   (`text_sim.simulate`; g157 ≤ 215).
6. QUATUOR present wherever es has it (g[125], g[127]).
7. visible line 2 ≤ 34 glyphs on every page (§1.3): `render_strings.py` passes the harness
   warning through, and the Swedish report must have none.

Items 1–6 are `tools/lint_strings.py` (run by `tools/build.py` before anything is built); item 4's
render and item 7 are `tools/render_strings.py`. VERIFIED on the final TSV (jar
`43846c9e…0c60c`, Phase F final verification): lint 0 errors (1 warning, the space before g126's
second marker, as in es), render 0 errors and no line-2 warning (`work/phaseF/render_r1.log` and,
after the rebuild, `render_r2.log`; `screenshots/strings/de/report.txt`).

---

## 2. HUD hour names (`k.b`)

### 2.1 Format (VERIFIED)
49 bytes = 7 hours × 7 cells, hours 0..6 = NOCHE, PRIMA, TERCIA, SEXTA, NONA, VÍSPERAS, COMPLETAS.
Each byte is a **raw `fuente.png` cell code**: glyph = cell `byte−45`, drawn **without** the
char switch and without overlays. Byte 32 = blank cell. Java bytes are signed: only 45..127 can
paint (cells 0..82), and ≥ 128 draws nothing.

### 2.2 Rendering
`D.c()` sets `D.l = 7·D.b` and `v.e = 9`. Each logic tick `v.c()` shifts the 56×8 `TYPE_INT_RGB`
buffer (background 0x275947) 8 px left and draws one cell at x 48: 2 blank cells, then the 7
bytes. `v.e()` blits it at **screen (4,197)**, on `marcador.png` at (0,176).

### 2.3 Second use: save/load labels
`w.c()` builds `w.t[lang] + day + " " + (char)v.a[k+7·hour]` and draws it through
`j.a(String)`, i.e. through the switch **and** the `_`/`%` line breaks. The save file stores only
`day<<4 | hour`, never the names. Hence:
- **allowed bytes:** 32 and 45..124 with a non-empty cell, **excluding 120** (HUD: blank cell 75;
  label: Ê), **95** (label line break; HUD ▶▶), and switch keys **33 39 44** (blank in the HUD,
  `! ' ,` in the label). 37 `%` is <45 and is a label line break; exclude it too.
- the same cell renders identically in both places for every other code.

### 2.4 Special glyphs
Shipped ligature slices (lowercase codes): es `VgPERAS` (g=103 "IS"), `COMdefg` (d e f g = "PL" "E" "TA" "S");
en `COMbcNE`; it `COMbETA`; fr `VlPRES` (l=108 precomposed Ê); pl `mnSZPqR`, `KOMopTA`
(q=113 precomposed Ó). de: plain ASCII ` NACHT  PRIMA TERTIA  SEXTA  NONA  VESPER KOMPLET`.
All shipped hour bytes are ≤ 113.

**Å/Ä/Ö in an hour name need a precomposed glyph** (accent inside the 8×8 cell, letter squashed into
rows 2–7 like cells 63 Ê and 68 Ó) in a **free cell reachable as a byte**: cells 2, 46, 72, 73, 74,
76, 77, 78, 79 (bytes **47, 91, 117, 118, 119, 121, 122, 123, 124**). Cell 75 (byte 120) is
unusable; cells 81/82 (bytes 126/127) only exist if the image is widened further (80 = ring, §3.4).
The glossary (`translation/glossary.tsv`, GLOSSARY §5.1) chooses ` NATT  `, ` PRIM  `, ` TERS  `,
` SEXT  `, `  NON  `, `VESPER `, and `NATTBÖN` with a precomposed Ö at **byte 119 (cell 74)**. That fits
these rules. A demo of precomposed Å/Ä/Ö in cells 72–74 rendered legibly
(`proto_font/out/*/a_dy2_demo_hud.png`). Plain names (NATT, PRIM, TERS, SEXT, NON, VESPER, KOMPLET)
need no new glyph.

**Built (Phase D; DECISIONS D8).** Cell 74 of `res/fuente.png` holds the precomposed Ö
(`assets_sv/glyphs/fuente_add.json`): row 0 = the cell-16 diaeresis dots (palette 37 + 1), row 1
empty, rows 2–7 = the O body, pixel-identical to the O of the shipped HUD Ó (cell 68). `k.b[42..48]`
= `78,65,84,84,66,119,78`. The build takes the bytes from the sv cell (`lint_strings.hud_bytes`:
Ö → 119, A–Z and space as themselves), never from a note. The lint allows only `A–Z`, space and Ö
in a `b` row and checks a `bytes=` note against the cell when one is present (none is; the
reference byte lists are the `hour_hud` rows of `translation/glossary.tsv`). VERIFIED: the HUD
strip and the save label render it with the game's code (`screenshots/strings/de/hours.png`, `raw/hud_hour6.png`, `raw/slots_set*.png`), and
`tools/regress.py` finds fuente cells 0..79 identical except the filled blank cell 74
(`work/phaseF/regress_r1.log`, `regress_r2.log`). Still free for later HUD glyphs: cells 2, 46, 72, 73, 76–79 (bytes 47,
91, 117, 118, 121–124).

---

## 3. In-game font `res/fuente.png` and the glyph routine

### 3.1 Image (VERIFIED)
640×8, 8-bit **colour type 3**: PLTE 54 entries (chunk at 0x21, tag at byte 37), tRNS 54 bytes,
pHYs, IDAT. Index 53 = #ffffff alpha 0, the only transparent entry (all background). Index 0 #000000
is unused. Index 1 #ffffff; 2–47 near-white greys #d1..#fe; 48–52 (#b9 #a5 #89 #83 #81) occur only in
the bottom rows of ¡ and !. Cell i = char code 45+i, 8×8. Capitals use rows 1–7, cols 0–6. Accent
cells use exactly palette 1 + 6 (#dadada); the diaeresis uses 37 + 1.

**Hard constraints:**
- Only `v.a()` loads it, twice. `v.c = i.b("fuente.png")` (ImageIcon, white). `v.d =
  abadia.b.a("fuente.png")` scans the **first 1000 bytes** for `PLTE`, multiplies every palette RGB by
  `Abadia.az = {0,0,0}`, recomputes the CRC and keeps tRNS → the black pause-menu font.
- **It must stay indexed, with PLTE before byte 1000 and tRNS kept.** An RGBA file throws
  `ArrayIndexOutOfBoundsException: arraycopy: source index -4` at startup. A truecolour file with a
  PLTE leaves the menu font white. No tRNS gives solid boxes. Do not let optimisers change the colour
  type, reorder chunks or merge palette entries 1 and 53. New pixels use existing **opaque** palette
  indices. The same loader recolours `tiles.png` and `sprites.png` (keep those palette PNGs untouched).
- **Width is free.** No code reads its width or height, and nothing is sized 80. Appended cells at
  x ≥ 640 only affect codes ≥ 125 that reach the default path. Regression VERIFIED: all 1128 shipped
  strings plus hour labels render pixel-identically, in white and black, with a 648-, 664- and
  1224-px font. A 2000-px poisoned font changes exactly the 4 known out-of-range chars (it U+008F
  ×3, de Ë).

### 3.2 `j.a(int ch, int x, int y, Graphics)` (private static, 737 bytes, stack 5, locals 10; VERIFIED)
Locals 4..9 = flags acute, grave, circumflex, diaeresis, ogonek, dot. `lookupswitch` at offset 19,
**36 keys**:

| key → base code (cell) + overlay | |
|---|---|
| `! 33`→93(48), `' 39`→97(52), `, 44`→60(15), `¡ 161`→92(47), `¿ 191`→64(19), `Ñ 209`→94(49), `ß 223`→62(17), `Ł 321`→114(69), `Œ 338`→107(62), `Ç 199`→106(61) drawn at y+1 | precomposed |
| `x 120` and `Ê 202` → E(69) + circumflex | |
| `À Á Â Ä` 192 193 194 196 → A(65) + grave / acute / circumflex / **diaeresis** | |
| `È É` 200 201 → E + grave / acute; `Ì Í Î` 204–206 → I + grave/acute/circ | |
| `Ò Ó Ô Ö` 210–212, 214 → O(79) + grave/acute/circ/**diaeresis** | |
| `Ù Ú Û Ü` 217–220 → U(85) + grave/acute/circ/diaeresis | |
| `Ą 260` A + ogonek; `Ę 280` E + ogonek; `Ć 262` C + acute; `Ń 323` N + acute; `Ś 346` S + acute; `Ź 377` Z + acute; `Ż 379` Z + dot | |

Common path (601-736): `if (ch != 32 && ch < 45) return;` `ch = (ch−45)<<3; setClip(x,y,8,8);
drawImage(v.b, x−ch, y)`. Overlays are recursive calls with char codes that are not switch keys:
acute 96 (cell 51) at y−2, grave 104 (59) at y−2, circumflex 105 (60) at y−2, **diaeresis 61 (16) at
y−1**, ogonek 116 (71) at y+2, dot 115 (70) at y−2 (Ż via a tail loop). Each overlay sets its own
8×8 clip. Nothing in the original reaches above y−2. Codes not in the switch and ≥ 125 (Å 197, å, ä,
ö, Ë, U+008F) fall outside the 640-px image: **blank cell, pen still +8**. The clip is never
restored; callers set their own.

`j.a(String s, x, y, g)`: `x == −1` → `x = 160 − 4·len`. `_` and `%` → x = start, y += 10 (`%`
+4 more). Every other char → `a(ch,…)`, then x += 8. Callers: `E` (end screen), `j.f()` (dialogue),
`w.a(int,int)` (menu/save list, with `v.b = v.d`, black).

**Ä and Ö already work** (A/O + cell 16 dots on row y−1, gap row y, letter rows y+1..y+7). VERIFIED
by rendering. É works. **Å does not.**

### 3.3 Cell inventory (VERIFIED, `font_sheet.png`, `font_glyphs.txt`, `glyph_usage.txt`)
| cells (code) | content |
|---|---|
| 0 `-`, 1 `.`, 3–12 `0–9`, 13 `:`, 14 `;`, 18 `?`, 20–45 `A–Z` | normal glyphs |
| **2 `/`, 46 `[`, 72 `u`, 73 `v`, 75–79 `x y z { \|`** | **blank, used by nothing** (75 = `x` is unreachable through `j.a`: switch → Ê) |
| **74 `w`** (Swedish build) | precomposed HUD Ö, hour byte 119 (§2.4); was blank in the original |
| **80 (code 125 `}`)** (Swedish build, appended at x 640..647) | the Å ring overlay (§3.4); the image is 648×8 |
| 15 `<` comma, 16 `=` diaeresis, 17 `>` ß, 19 `@` ¿, 47 `\` ¡, 48 `]` !, 49 `^` Ñ, 50 `_` ▶▶ (more marker), 51 `` ` `` acute, 52 `a` apostrophe, 59 `h` grave, 60 `i` circumflex, 61 `j` Ç, 62 `k` Œ, 69 `r` Ł, 70 `s` dot, 71 `t` ogonek | glyphs reached through the switch or as overlays |
| 53–58 `b–g`, 63 `l` (precomposed Ê), 64–67 `m–p`, 68 `q` (precomposed Ó) | HUD-only slices; 53, 55, 66 are pixel-identical |

### 3.4 Chosen Å mechanism: patch `abadia/j.class` + ring glyph (prototype VERIFIED)

**Patch** (Phase A tool `work/phaseA/proto_font/src/PatchJ.java`, args `<in> <out> 125 -2 1`; the
build runs its maintained port `tools/java/PatchJ.java` with the same args and asserts the same
output md5):
1. `ClassReader(flags 0)` → `ClassWriter(reader, 0)`. Every method except
   `a(IIILjava/awt/Graphics;)V` is copied verbatim; the constant pool is unchanged (`#265` = this method).
2. Sanity checks: one `lookupswitch`, 36 keys, contains 196/214, not 197/229/125; maxs 5/10.
3. Append after the final `return`:
   `F_FULL [TOP, I, I, java/awt/Graphics, I, I, I, I, I, I] []`;
   `bipush 65; iload_1; iload_2; aload_3; invokestatic abadia/j.a(IIILjava/awt/Graphics;)V;`
   `bipush 125; iload_1; iload_2; iconst_2; isub; aload_3; invokestatic …; return`
   (an A, then code 125 = cell 80 = ring at y−2).
4. Switch keys (sorted): **197 → ring block, 229 → ring block, 228 → Ä target, 246 → Ö target** (40 keys).
5. Explicit F_FULL frame, **no COMPUTE_FRAMES**. The class is v51, so StackMapTable frames are
   mandatory and HotSpot does not fall back to the old verifier: a deliberately broken frame is
   rejected even with default flags.

Result: 12022 → **12092 B**, md5 **`f197f5a3e4b9d1c553ede4194efc75af`** (rebuilt byte-identically by
two reviewers). `javap -v` diff: only this method changes (switch `// 40`, old targets +32, new
block at 769–787, 45 frames). dy −3 variant md5 `58e35cedf6c2da1084aef580652445dc` (one byte at
code offset 781 / file 11713).

**Ring glyph = new cell 80 (code 125, x 640..647); `fuente.png` becomes 648×8.** Provisional art
(`proto_font/fonts/fuente_ring.png`, md5 `cd4e691875cd262cabbda0a7e1b5162f`, PLTE/tRNS
byte-identical, cells 0–79 identical, pHYs dropped):
```
row0 . . . W G . . .     W = palette 1 (#ffffff), G = palette 6 (#dadada), rest palette 53
row1 . . W . . G . .
row2 . . . W G . . .
```
With **dy = −2** the ring occupies rows y−2..y, the envelope of the circumflex, touching the A apex.
dy −3 is crisper but pokes 2 px into `dialog.png`'s top border (rows 0–2) on dialogue line 1
(VERIFIED render). Keep **dy −2**.

**Final art (Phase D)**, `assets_sv/glyphs/fuente_add.json` cell 80, replaces the provisional one
above: a 4×3 ring on cols 2–5 that sits on the A apex, accent palette only, lit from the top right:
```
row0 . . . W W . . .     W = palette 1, G = palette 6, rest palette 53
row1 . . G . . W . .
row2 . . . G G . . .
```
VERIFIED: the built `abadia/j.class` is 12092 B, md5 `f197f5a3…` (= the prototype patch);
`tools/build.py` writes the font with PLTE/tRNS copied verbatim; Å draws in every rendered and
live page that has one (e.g. g49 `VÅRT`, `screenshots/runtime_sv/opening/pages/001_g049_p01.png`);
`tools/regress.py` renders es, en, it, fr and pl pixel-identically to the pristine jar (3711
frames, `work/phaseF/regress_r1.log`, `regress_r2.log`).

Side effects: `}` now draws a bare ring (forbid it); lowercase å/ä/ö draw Å/Ä/Ö (insurance only;
the lint still rejects lowercase). Every other language renders pixel-identically (regression above).

**Verification protocol:** `ClassReader.accept(new CheckClassAdapter(cw, true), 0)` (plain
`CheckClassAdapter.verify` accepted a broken-frame class). Load and link under `-Xverify:all` on
JDK 11 and JDK 8 (`proto_font/src/VerifyJ.java`, `proto_font/run_harness.sh`). Render through the
real code (`harness/render.sh --res`). Regression of all languages
(`proto_font/src/abadia/RegressAll.java`, `refute_font_1/src/abadia/Regress.java`).

Rejected alternatives (all VERIFIED-rendered, `proto_font/aao_compare.png`): a precomposed Å in a
widened image at cell 152 (no code change, but the ring must squash into rows 0–1 over a 6-row A);
a free code with a precomposed glyph (same quality, hidden transliteration); redrawing the
grave/circumflex overlay (breaks French). Putting the ring in blank cell 72 (code 117) instead of
appending cell 80 would also work if the image must stay 640 px; the patch would then use
`bipush 117`.

---

## 4. Parchment: `abadia.y`, `res/letras`, `res/<lang>/pergamino1|2`

### 4.1 Loading and states (VERIFIED)
`y.a()`: `p = i.a("letras")`, `c = i.a(u[a]+"/pergamino1")` (intro), `d = …/pergamino2` (ending),
`q = pergamino.png` (190×190, drawn at (65,9)). `i.a` sizes its buffer from `available()`; a larger
`letras` loads in full from a deflated jar entry on JDK 8 and 11 (VERIFIED). A missing file returns
null → NPE later. `Abadia.a` is used only for these paths; there is **no language branch**.
States: 0 = draw the parchment and set pen (76,18); 1 = read a byte; 2 = draw **one pixel per
tick** (then overlay and advance); 3 = page-turn animation (190 ticks); 4 = redraw; −1 = done.
Intro: started after "Press to start". Ending: when `Abadia.L` (solved); afterwards the intro restarts.

### 4.2 Byte decoding (state 1, VERIFIED; y.java case 1)
| bytes | effect |
|---|---|
| `0D` CR | new line: x=76, y+=16; if y > 178 → page turn (so **11 lines per page**; blank lines count) |
| `0A` LF | forced page turn (no shipped file has one; **CRLF = one line per page**) |
| `1A` | end of text; the page waits for Space; **bytes after it are ignored**. Required. |
| `20` | x += 8 (no ink) |
| `27 '`, `92 ’`, `B4 ´` | apostrophe flag; the **next byte** is used as the glyph (only the â ê î ô û remap still applies) |
| `C0` À → A+grave; `E0 E1 E2` à á â; `E7` ç; `E8 E9 EA` è é ê; `EC ED EE` ì í î; `F2 F3 F4` ò ó ô; `F9 FA FB` ù ú û | base letter + overlay |
| `F1` ñ | code 47 (the `/` table slot holds ñ) |
| `C3`/`C4`/`C5` + T | **lead ignored**; T ∈ {82 ł, 84 ń, 85 ą, 87 ć, 99 ę, 9B ś, A1 á, A9 é, AD í, B1 ñ, B3 ó, BA ź, BC ż}; any other T is used raw |
| any other byte B | table lookup of B |

Lookup: `idx = (code−44)·2`, `addr = LE16`, `g = addr − 42711`. Colour: `(code & 0x60) == 0x40`
→ red 0xD00000, else black; ink alpha 0xC0. So **all capitals A–Z (and `@ [ \ ] ^ _`) are red
everywhere** (e.g. "Melk", "William"). A glyph with zero pixels would inherit the previous colour.
Repeated pixels darken (alpha compositing).

Shipped byte inventory: es E1 E9 ED F1 F3 FA (ends `0D 1A`); en=de E1 E9 ED F1 + one B4 (ends
`1A 20`); it 92 + E0 E1 E8 E9 EC ED F1 F2 F9 (two 1A); fr 92, one 27, C0 E0 E1 E2 E7 E8 E9 EA ED
EE F1 FB, `92 EA` ×3 (shows "dêtre": only the circumflex is drawn); pl strict UTF-8 (C5 BC, C4 85, C4 99,
C5 82, C3 B3, C4 87, C5 9B, C5 84, C5 BA, C3 A9/A1/AD/B1). No file has LF, `! ?`, or digits other
than 1 2 3 7.

### 4.3 `res/letras` (5564 B; VERIFIED)
A memory image of the Amstrad CPC game starting at Z80 address **0xA6D7 (42711)**. Bytes 0..161 are
the LE16 table: entry k = code 44+k, **81 entries (codes 44 `,` .. 124 `|`)**. Bytes 162..1523 are
unreferenced (they look like Z80 code; INFERRED). Glyph data runs from 1524 to EOF.
**62 populated:** `, - . / 1 2 3 7 : ;` A–Z a–z (`/` = ñ). **19 empty (0x0000):**
`0 4 5 6 8 9 < = > ? @ [ \ ] ^ _ { |` plus the backtick = codes 48, 52, 53, 54, 56, 57, 60–64, 91–96, 123, 124.
Glyph data: one byte per pixel, `dx = b & 0x0F`, `dy = b >> 4` (0..14), relative to the pen, drawn in
byte order (this order is the handwriting animation). A byte `0xF?` ends the glyph; its low nibble is
the advance (0..15). The u16 address caps a glyph's **start** offset at 22824; first free address
for appended data = **0xBC93** (offset 5564).
Metrics: lowercase body rows 4..12, ascenders from row 0 (b d f h l t) or 1 (i j), descenders to
row 14. **Rows 0..3 above lowercase are free.** Capitals start at row 0 (A–H, J–Q, S, T, Y), 1 (I R Z)
or 2 (U V W X, reaching row 14): **no free row above A or O.**
Advances (px): `, . : ;` 4, `-` 8, ñ 8, `1` 5, `2 3 7` 8, space 8; a8 b8 c8 d7 e8 f7 g7 h7 i5 j8 k9 l5
m12 n8 o7 p8 q7 r8 s8 t6 u8 v8 w11 x8 y8 z8; A14 B15 C14 D14 E14 F15 G14 H14 I8 J12 K15 L14 M14 N15
O12 P14 Q15 R15 S14 T14 U14 V14 W15 X14 Y14 Z12. Ink can reach pen+14. Accents and apostrophes
add 0. Full table: `work/phaseA/letras_metrics.json`; sheet `letras_sheet.png`.

### 4.4 Overlays (composed with drawLine, at most one per glyph; VERIFIED)
Precedence acute > grave > circumflex > apostrophe > cedilla > ogonek > dot > stroke. Pixels relative
to the pen (×2 = hit twice): acute (3,0)(4,0)×2(5,0)(2,1)(3,1); grave (2,0)(3,0)×2(4,0)(4,1)(5,1);
circumflex (1,0)(2,0)×3(3,0)×2(0,1)(1,1)×2(2,1)(3,1)(4,1)(0,2)(1,2)(4,2)(5,2); apostrophe
(1,1)(2,1)(0,2)(1,2)(0,3)(1,3); cedilla (2,13)×2(3,13)×2(0,14)(1,14)×2(2,14)(0,15)(1,15); ogonek
(3,13)(4,13)(3,14)(4,14)(5,14); dot (3,1)(4,1)(3,2)(4,2); stroke (3,6)(4,6)×2(5,6)(1,7)(2,7)×2(3,7)(0,8)(1,8).
**There is no diaeresis and no ring overlay.**

### 4.5 Layout and the line-width limit
Pen origin **x=76, y=18**; line height 16; lines at y = 18, 34, …, 178. **The code never wraps**:
lines come only from CR, so translators hand-wrap (shipped texts hyphenate with `-`). Leading spaces
indent 8 px each (paragraphs start with one space). Nothing clips to the paper.
Paper right edge per line (luminance ≥ 170, re-measured by `scripts/format_checks.py`):

| line | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| right edge x | 246 | 248 | 247 | **245** | 249 | 248 | 247 | 250 | 249 | 249 | **245** (body rows) |

Line 11's lower rows curve in: y 191 paper ≈ x 106..244, y 192 ≈ 110..207, y 193 ≈ 146..206, with a dark
notch at x ≈ 98..111. Keep line-11 descenders and cedillas (g j p q y ç ą ę) between x ≈ 110 and 206,
or avoid them there (fr1 already has descender pixels on the border).
**Rule: ink right edge ≤ 244 on every line.** Widest shipped (ink edge, intro/ending): es 243/241,
en=de 246/246, pl 245/242, it 252/250, fr 252/254 (it/fr visibly overflow; not a reference).
Swedish: **240/238** (VERIFIED with the real `y.a()`, `screenshots/strings/de/report.txt`;
`tools/build.py` step 7 rejects any line > 244).
Measure: `uv run tools/letras.py width "<line>" --letras game/TheAbbeyOfCrimeExtensum.jar`
(prints pen advance and ink right edge; ÅÄÖåäö are mapped to the slot bytes of §4.7, as the build
does; it measures only the first line of its argument). `uv run tools/letras.py check FILE --text
--letras game/TheAbbeyOfCrimeExtensum.jar` gives the edge of every line of a whole file. The Phase A
original was `work/phaseA/scripts/letras_render.py width "<line>" --sv --letras <letras>`.
Do **not** end with CR after the 11th line of a page: the CR turns the page and the text ends on a
blank parchment. Simplest: no CR before the final `1A`.

### 4.6 Failure modes (VERIFIED with the real `y.a`)
- **Empty slot or out-of-range address** (e.g. raw ä E4, å E5, ö F6, Ö D6, UTF-8 C3 A4/A5/B6/96,
  `? @ [ { ~`, a BOM `EF`): an exception inside state 2's try. It prints `Caracter: N` to stdout every
  tick and never advances. Intro: Space still skips it. **Ending: permanent soft-lock.**
- **Plain byte < 44** (`! " # $ % & ( ) * +`, TAB, any control except 0A 0D 1A) or **missing 1A**:
  uncaught AIOOBE in state 1 on every paint; nothing can skip it.
- Prefix (`27 92 B4 C3 C4 C5`) + control byte: **one** uncaught AIOOBE, the prefix is dropped,
  then the text continues. Reject it anyway.
- `C4`/`C5` (Latin-1 Ä/Å) + letter: the Ä/Å **vanishes** and the letter is drawn. UTF-8 Å (C3 85)
  draws ą, UTF-8 Ä (C3 84) draws ń.
- Bytes 0x8A and 0x9F happen to resolve into the dump region and draw an `n` and half an `R`.
  `letras_render.py` crashes on them (KeyError), so validators must whitelist bytes.

### 4.7 Swedish å ä ö Å Ä Ö: data-only `letras` extension (prototype VERIFIED; DECISIONS D7)
Put six new precomposed glyphs in **empty table slots** and write those slot bytes in the Swedish
pergamino files. No code change; no used table entry or existing glyph changes; other languages
never emit these bytes (VERIFIED: all 12 shipped texts give byte-identical drawLine logs with a
modified `letras`).

| letter | byte (slot) | table bytes | colour (from code) | prototype base |
|---|---|---|---|---|
| Ä | `0x5B` `[` | 94–95 | red | A |
| Ö | `0x5C` `\` | 96–97 | red | O |
| Å | `0x5D` `]` | 98–99 | red | A |
| å | `0x60` `` ` `` | 104–105 | black | a |
| ä | `0x7B` `{` | 158–159 | black | a |
| ö | `0x7C` `\|` | 160–161 | black | o |

Build: copy `letras`, append each glyph stream at EOF (pixels `dy<<4|dx` in drawing order, then
`0xF0|advance`), and write `0xA6D7 + offset` (LE16) into the slot. Prototype
`scripts/proto_swedish.py` → `proto/res/letras` (5987 B; only bytes 94–99, 104–105, 158–161 change)
rendered with the real code, no hang, pixel-identical to the emulator (`proto/java_pages/page1.png`).
**Design status (the Phase A requirement):** lowercase prototypes (a/o + two i-style dots in rows
1–2; a + ring in rows 0–2) read well. **Capitals are placeholders**: marks at row 0 merge into A/O
ink. Å Ä Ö need a shorter capital body in rows 2..14 (like U V W X) with the mark in rows 0–1. Keep
the same advance as A (14) and O (12). Optional: a `?` glyph in slot 0x3F (black) the same way; it
needs a matching entry in `tools/letras.py` `SV_SLOTS` (which also feeds `TEXT_MAP`) as well as
`letras_add.json`, because `apply_add` refuses any slot outside the six Swedish ones. `!`, `"`, `(`,
`)` are impossible (codes < 44).
**Built (Phase D):** the six final glyphs are `assets_sv/glyphs/letras_add.json` (advances Ä 14,
Ö 12, Å 14, å 8, ä 8, ö 7); the capitals got the shorter body with the mark above (final: bodies in
rows 3..14, the Ä/Ö dots in rows 0–1, the Å ring in rows 0–2), and the built `res/letras` is
5949 B. VERIFIED: `tools/regress.py` finds the original bytes identical except the 12 slot-pointer
bytes and all 62 original glyphs identical; both Swedish parchments run through the
real `y.a()` with no `Caracter:` line (`screenshots/strings/de/parchment_*.png`), and the intro
parchment was written live with å ä ö and red capitals (`screenshots/runtime_sv/INDEX.md`, files
11–19). No ü slot was added, so `München` stays impossible (DECISIONS D10).

**Swedish pergamino byte map (the build writes bytes, not text in an encoding):** ASCII letters,
digits 1 2 3 7, `, - . : ;` and space as-is; å→`60`, ä→`7B`, ö→`7C`, Å→`5D`, Ä→`5B`, Ö→`5C`;
é→`E9`, í→`ED`, ñ→`F1` (credits: "Menéndez", "Celemín", "Cañadas"), other accents per the §4.2 table;
lines end with `0D`; the file ends with `1A`. No BOM, no TAB, no `? ! " ( ) /`, no digits
0 4 5 6 8 9. `translation/pergamino*_sv.txt` can express neither LF (each text line ends with CR) nor
an apostrophe (`'` is not in `TEXT_MAP`); a forced page break or an apostrophe (which must precede a
plain letter) would need a `TEXT_MAP` change in `tools/letras.py`. The build checks every file
(step 7) and `tools/render_strings.py` runs both through the real `y.a()`; by hand, use
`uv run tools/letras.py pages FILE OUTDIR --text --letras game/TheAbbeyOfCrimeExtensum.jar --res
<dir with pergamino.png>` (without `--res` it reads `work/jar/res/pergamino.png`, the Phase A
extraction; `work/inputs/<key>/jar/res/`, which every build recreates, holds the original file)
and the real code (`harness/render.sh --res`, or `refute_runtime_1/src/abadia/ParchHarness.java`, or
`harness/src/PergHarness.java`), and grep stdout for `Caracter:`.

### 4.8 Timing
Every call sets `Abadia.e = 6` ms; space 33, CR 66, end of page turn 132. Per glyph 1 + pixels + 1
ticks; page turn ≈ 1278 ms. Nominal ≈ 38–48 s per full page, 266–310 s per parchment. Measured: en
intro 279 s, es 299 s (8 pages each). Pages (intro/ending): es 8/8, en=de 8/7, it 8/7, fr 9/8, pl 8/7,
**sv 8/8** (live intro 292 s, `screenshots/runtime_sv/INDEX.md`).
Space skips **only the intro**, only in state 2 (`C.e && y.b != y.d`); Enter does not. The ending
cannot be skipped. At `1A` the page waits for Space, then fades. A whole parchment's credits block
(names, "In memoriam …") is inside `pergamino1`.

---

## 5. The `de` slot (index 4): safe for Swedish (VERIFIED)

- `Abadia.a` (default **1 = en**, `<clinit>` `iconst_1` at file offset 0x1db7) is set by `main`: for
  every argv, `equalsIgnoreCase` against `u = {es,en,it,fr,de,pl}`; **the last match wins**, unknown
  args are ignored (VERIFIED by probe: `[]`, `[sv]` → 1; `[de]`, `[DE]` → 4; `[de,es]` → 0).
- All 14 reads of `Abadia.a` are followed directly by `aaload`. It is never compared, switched on or
  used in arithmetic; nothing special-cases 4 or `"de"`. The codes exist only in `Abadia.<clinit>`.
- Language-indexed data, complete list: `Abadia.u`, `j.bS` (g), `j.bT` (a), `v.g` (b), `w.p/q/r/s`
  (f/d/c/e), `w.t`, `w.u`, `E.h`, and the resource paths `res/<lang>/marcador.png`,
  `res/<lang>/intro/*` (11 files), `res/<lang>/pergamino1|2`. Nothing else: no per-language
  positions, timings or box sizes.
- Disk: only `savedata.bin` (in the parent directory of `Abadia`'s code source = the jar's
  directory; for an exploded class dir, its parent) and 10 temp audio files. No language is
  stored; there is no config, Preferences, Locale or getenv.

**To take over slot 4:** replace `abadia/k.class`; replace `res/de/marcador.png`,
`res/de/intro/{loading,logo,manuydani,novela,pacoyjuan,pelicula,pulsa}.png` (logo = es copy) and
`res/de/pergamino1|2`; keep `res/de/intro/{luna,monje,niebla,ventana}.png` (already identical
copies); patch `w.t[4]`, `w.u[4]`, `E.h[4]` (§1.10); ship a launcher passing `de`. Shared changes
needed whatever the slot: `j.class` (Å), `fuente.png` (ring, any HUD glyphs), `letras` (å ä ö Å Ä Ö).
Optional: make Swedish the default by changing byte 0x04 → 0x07 at `Abadia.class` file offset
0x1db7 (same length, no frames; VERIFIED on JDK 8 and 11). Not needed with a launcher.

Risks: a missing `res/de` file → null → NPE in `r`/`y`; a stale `w`/`E` leaves Spanish
"DÍA"/"VACÍO" and the German title; a Swedish title that does not match the harness regex
(§7.6); saves made in another language reload by index (harmless if `g` order is kept).
Java 9+ always prints two harmless startup traces (§7.7).

**Applied by the Swedish build (VERIFIED).** The patched jar differs from the original in exactly
16 entries: `abadia/{E,j,k,w}.class`, `res/fuente.png`, `res/letras` and 10 `res/de/**` files (7
images, `logo.png` as the es copy, both pergaminos), so every es/en/it/fr/pl resource is
byte-identical (entry CRCs of `game/` against `original/`, re-checked for this update).
`tools/regress.py` renders es, en, it, fr and pl pixel-identically to the pristine jar (3711 frames,
`work/phaseF/regress_r1.log`, `regress_r2.log`), and live en/es/pl tours of both jars match at every deterministic state
(`screenshots/runtime_regress/INDEX.md`). The launcher passes `de`; `Abadia.class` (the default
language) is not patched.

---

## 6. Images

### 6.1 What needs a Swedish version (VERIFIED: md5, pixel diffs, transcriptions)
`de/*` == `en/*` byte for byte. Groups: logo en=fr=de=pl (it pixel-identical; es unique); pulsa
en=it=fr=de (es, pl unique); luna, monje, niebla, ventana identical in all 6.

| file (`res/de/…`) | base for Swedish | text to replace (boxes inclusive, = screen coords for intro) | font | current de (=en) format |
|---|---|---|---|---|
| `marcador.png` (HUD 320×32, drawn at (0,176)) | de/en "Day" | day word in [1,0,39,20]; "Dag" = keep D (x 1..17) + a (18..29), new **g** | hud | indexed, 26-entry PLTE, tRNS idx 0 (#b7bece) |
| `intro/loading.png` | **es** title art (y < 175; alpha bbox [79,28,239,169]) + a new bottom line | one line in rows **181..193** (en ink [102,181,232,190], es [82,181,253,193]); centre ≈ x 160–168 | loadline | RGBA |
| `intro/logo.png` | **es byte copy** (indexed, 129 PLTE + 4-entry tRNS, alpha bbox [92,4,249,94]) | – | title art | RGBA (en) |
| `intro/manuydani.png` | es or en (same name pixels; es has the í in "Celemín" at [227..233,137..140]) | conjunction only: "och" ≈ x 47..82, ending ~11–12 px before "Daniel" (x≈94); en "and" [50,143,81,157] | script | RGBA |
| `intro/pacoyjuan.png` | es/en | line 1 (es "inspirado en la obra de" [28,93,246,118]); conjunction before "Juan Delcán" (en "and" [47,158,78,172], only 6 px before J); names reusable as blocks | fraktur + script | RGBA |
| `intro/novela.png` | es/en | 3 lines (es "en la novela" / "“El Nombre de la Rosa”" / "de Umberto Eco") | fraktur | RGBA |
| `intro/pelicula.png` | es/en | es "y" + "en la película de" / "Jean Jacques Annaud" (no hyphen) / "del mismo nombre"; en "and" / "in Jean-Jacques Annaud’s" / "film of the same name" | fraktur + script | RGBA |
| `intro/pulsa.png` | en | "Press to start" [101,166,219,185], centred ≈ x 160 | pulsa | indexed, 52 PLTE + 36-entry tRNS (33 partial) |

Full transcriptions for all languages: `images.md` §2. Code-drawn, not in images: `v1.3e` on the
loading screen.

**Swedish result (Phases D and E).** The seven Swedish images are built by
`tools/images/build_*.py`; the wording is GLOSSARY §8 (`Dag`, `LADDAR: var god vänta...`,
`och Daniel Celemín`, `efter spelet av / Paco Menéndez / och Juan Delcán`, `efter romanen /
”Rosens namn” / av Umberto Eco`, `och / Jean-Jacques Annauds / film med samma namn`, `Tryck för att
starta`; DECISIONS D11). They are derived files: git-ignored (`assets_sv/res/`) and rebuilt by every
`tools/build.py` (step 8a, D14). VERIFIED live: every credit screen, the HUD word and the press-to-start
line, compared with the same moments in `screenshots/pristine_{en,es}/`
(`screenshots/runtime_sv/INDEX.md`).

**Builder-and-critic loops (Phase D; the brief allows at most 6 rounds per image).** Read from the
Phase D workflow journals `wf_c780c609-029` (intro images and the two shared kits; every round had
two critics, a visual and a technical one) and `wf_dd9b103f-201` (HUD, font glyphs; one critic per
round). A round is a build plus its critique; the loop ended at the first round that both critics
passed. A builder-only nits pass then applied the agreed nits. No critic re-read that pass in
Phase D, but the Phase E visual critic reviewed every final image and glyph in three rounds and found
no defect. All seven shipped images are byte-identical to their Phase D final builds. `logo.png` had
no loop: it is a byte copy of the es logo (DECISIONS D3a).

| image or glyph set | rounds used (of 6) | final critic verdict | residual notes |
|---|---|---|---|
| `marcador.png` (`Dag`) | 1 | pass, 2 nits | Not applied (no builder round followed): the g's top-left touches the tip of an ivy leaf (visible at 4×, barely at 1×), and a builder comment overstates the bowl's stroke width. |
| `intro/loading.png` | 1 + nits | pass (visual and technical), 7 nits | All 7 applied (comments and builder checks); the image bytes did not change. |
| script `och` kit (`script_och.py`; manuydani, pacoyjuan, pelicula) | 1 + nits | pass, 7 nits | All 7 applied (the c's overshoot, the o's lower right, output guards). |
| `intro/manuydani.png` | 1 + nits | pass, 5 nits | 4 technical nits applied. The visual nit is open: o, c and h do not join, where the shipped script joins its letters. Its fix belonged to the `och` kit and was not taken up. |
| Fraktur kit (`fraktur.py`; novela, pacoyjuan, pelicula) | 5 + nits | pass in round 5 | The technical critic failed rounds 1–4 (round 1 with a must); the visual critic passed from round 2. All 8 final nits were handled. The `le` and `om` gaps in `efter spelet av` and `efter romanen` are 1 px looser than most shipped pairs but within the shipped range. The composed å ring is unused, since no image has an å. |
| `intro/novela.png` | 1 + nits | pass, 5 nits | 4 applied; 1 (the kit's selftest output folder) left to the kit. |
| `intro/pacoyjuan.png` | 1 + nits | pass, 4 nits | All 4 applied: the kept letters of `Paco` are restored to the es bytes. |
| `intro/pelicula.png` | 1 + nits | pass, 4 nits | All 4 handled. The interpreter pin was answered with the critic's alternative: the builder prints the pixel hash and the zlib version, and zlib 1.2.11 and 1.3.1 gave identical bytes. |
| `intro/pulsa.png` | 3 + nits | pass in round 3 | Round 1: the technical critic failed it with 3 should. Round 2: a must from the visual critic and a should from the technical one. Of the 6 final nits, 5 were applied, the word-internal joins only in part: T-r, y-c and f-o stay unjoined on purpose. The first r's flag ends 1 px short (left by agreement). |
| fuente glyphs (Å ring, HUD Ö; §3.4, §2.4) | 1 | pass, 3 nits | No builder round followed. Two nits concern the previews: a wrong caption, and Å never shown in the menu font or on the end screen (the critic rendered both and found them fine). The third, documenting the new cells, is done in §1.9 and §3.3. |
| `letras` glyphs (Ä Ö Å ä ö å; §4.7) | 2 | round 1 fail (must: the left dot of ä/ö merged with a preceding f, F, J, P, S, T or O); round 2 pass, 3 nits | Not applied: Ä Å Ö sit 1 px lower than A and O, Ö touches a following s diagonally, and Ä and Å look slightly lighter than A. All are visible only side by side. |

No image ran out of rounds. The longest loop was the Fraktur kit's, which used 5 of 6; pulsa used
3, the letras glyphs 2, and everything else passed in round 1.

### 6.2 Fonts (inventory `index.json`: 871 glyph crops + masks, 22 marks)

Where the inventory lives: Phase A wrote it to `work/phaseA/images/glyphs/`. The image builders
do **not** read that, nor `work/jar/`. They read `work/inputs/<key>/` (`jar/res/**.png` + `glyphs/`),
which `tools/images/inputs.py` derives from `original/TheAbbeyOfCrimeExtensum.jar` alone with the
Phase A inventory scripts copied into `tools/images/inventory/` (key = sha256 of the jar, those
scripts and `inputs.py`; published by an atomic rename, never changed). The regenerated tree is
byte-identical to the Phase A inventory (1803/1803 files, VERIFIED in Phase E; see
`tools/README_tools.md`). The Phase F final verification pinned the scripts' dependencies to the
builders' `pillow==11.3.0`, `numpy==2.3.2` and `scipy==1.16.1`, because unpinned they now resolve
to newer releases. The tree they produce is byte-identical to the Phase E one (VERIFIED: all files
but `DONE.json`). Paths below that start `images/glyphs/` mean `work/inputs/<key>/glyphs/`.
No image font has a diaeresis or a ring. ä/ö = a/o + two copies of the font's own dot; å = a +
a hand-drawn ring.
- **fraktur** (credits es/en/it/fr): chars `" - A C D E I J L M N P R T U a b c d e f h i k l m n o p q r s t u v w y z à á é ê í œ ’ “ ”`.
  **Capitals only A C D E I J L M N P R T U** (no B F G H K O Q S V W X Y Z); lowercase lacks g j x.
  Colour model: every pixel's RGB lies on the line from G=(29,8,27) to F=(253,246,231). The core is
  opaque cream; edge pixels are partial-alpha cream→G blends (alpha mostly 128..254); then a G glow
  with median alpha ≈ 226, 153, 91, 51, 24, 11, 3, 0 at 1..8 px from the opaque core. Build new glyphs
  as AA cream glyphs composited over a blurred G glow layer. x-height 17, cap/ascender top 21 above
  the baseline, **line pitch 30**. Baselines es/en 114/144/174 (it novela 129/159/189, fr ≈ +7/8;
  free per image). Word gap 10–12 px. Lines are left-aligned with hand indents. i-dot tick 3×4 ink
  (es manuydani [140,137,142,140]); acute 7–8×4, grave 7×4, circumflex 7×4.
- **fraktur_pl**: a different drawing (x-height 14, glow (28,2,21), fill (255,246,231)); reference
  only, never mix.
- **pulsa**: chars `N P a c e i j l m n o p r s t u z ę ś`; fill (253,246,231) (pl 255,246,231) with grey
  AA, then **1 px opaque black outline + 1 px semi-transparent black fringe** (alpha ≈ 15–218);
  x-height rows 171..182, caps from 166, descenders to 185. It is drawn over `monje.png` and
  `logo.png`, so the outline is visible. `Tryck för att starta` needs T, y, k, f and ö, which
  were hand-drawn (DECISIONS D11).
- **loadline**: 1-bit, 1-px joined handwriting, colour (252,254,252) (pl #ffffff). Chars
  `, . : A C D E G H I L M N O P R T W Y Z a c d e f i k l n o p r s t u v w z ć ę`. Missing
  B F J K Q S U V X and b g h j m q x y. Rows: ascenders 181, caps 182..189 (round caps to 190),
  x-height 184..189, baseline 189, descenders to 193. 1-px dots.
- **script** (conjunctions): `a d e i n t y` only; cream with partial alpha, no glow. "och" must be
  composed (o from a/d bowl, c from e, h from d's ascender + n's arch). Placement: es/en/it end
  10–12 px before the name; fr/pl ≈ 19–20 px. Use en/es spacing.
- **hud**: greys #ecebec #d7d8d8 #abb2b3 #9ca2a4 + blood band #96020a #6d0211 #54020c on #050204 with
  ivy. es/en/it share an identical D (x 1..17); pl's D is narrower (x 1..13); fr has another style.
  Chars `D J a e i o r u y z í ń`. **No g.**

### 6.3 Placement constraints (VERIFIED from code)
- **HUD:** `v.b(int)` paints **black** over image x 37..60, y 7..14 every frame (day numeral box). So
  the Swedish word must stay at **x ≤ 36 on rows 7..14** and **x ≤ 38 elsewhere** (x ≥ 39 is the
  numeral frame). With en's D and a, a `g` gets only x 30..36 on rows 7..14 (7 px), which needs a
  condensed g (model: en a-bowl + y-descender; the y descender reaches row 18). The hour strip covers
  image (4..59, 21..28); the obsequium bar covers (265..309, 17..22) (fr's grey fill [267,17,308,22]
  sits under it). A clean word-area background: `work/inputs/<key>/glyphs/hud/BACKGROUND_reconstructed_x0-41_y0-21.png`
  (majority vote; it differs from each language's ivy by 3–62 px, so starting from de/en
  `marcador.png` and editing only the word keeps en's ivy).
- **Moon window:** from manuydani on, `r` draws luna/niebla/ventana opaque in the clip
  **(250,0,70,100)**, under the text. Keep new credit ink **and its glow (~6–8 px)** out of x ≥ 250 for
  y < 100. Shipped intrusions exist (pl novela ink [250..270, 92..99], es pacoyjuan glow, en logo
  column x=250); the es logo stays at x ≤ 249.
- **Intro images stay 320×208** (drawn centred; monje and logo at (0,0) underneath later screens).
  logo and pulsa must stay transparent outside their text.

### 6.4 Format
Images load via `new ImageIcon(getResource("/res/"+name)).getImage()`. On JDK 8 and 11, AWT decodes
indexed+tRNS, RGBA8, RGBA16, LA and gAMA files pixel-identically to PIL `convert("RGBA")`
(VERIFIED, `refute_images_1/java/AwtDecode.java`), so PIL previews predict the game. Shipped
variants of the same image mix only indexed+tRNS and RGBA. Keep each de file's mode (prompt rule):
marcador indexed (its 26 colours suffice for a g); pulsa indexed (new AA shades → append palette
entries, ≤ 256); others RGBA. loading.png, logo.png and the loadline are strictly 1-bit alpha. Write
no gAMA/iCCP chunks. A missing intro file → null → NPE in `r` (all 11 must exist).

### 6.5 Other images (keep, VERIFIED by viewing every file and GIF frame)
"OBSEQUIUM" (Latin, HUD); numRoman.png 24×7 (blank, V, I); the monje.png signature "Manuel Pazos /
Daniel Celemín ©" [1,177,85,207] and "Q", "R" on the chair (the QUATUOR hint); illegible plaques in
tiles.png; cipher symbols in anim/pergamino.gif; "Juan Delcán" in laberinto.bin (an 800×800 JPEG
shown after the ending). The parchments pergamino/pergamino2/pergamino_mapa are blank.

---

## 7. Runtime testing (`tools/run_headless.sh`)

### 7.1 Usage (VERIFIED)
```sh
cd /home/ran/the_abbey_of_crime_extensum_swedish
PARCH_FULL=1 SHOT_DIR=screenshots/<set> RUN_DIR=work/runs/<name> \
  tools/run_headless.sh <gamedir> <es|en|it|fr|de|pl> tools/drivers/pristine_tour.sh
PHASES="play menu" tools/run_headless.sh <gamedir> de tools/drivers/pristine_tour.sh   # partial
tools/run_headless.sh <gamedir> de tools/drivers/interactive.sh 1200 &                   # manual
source work/runs/<run>/env.sh; tap space; shot name; touch work/runs/<run>/stop
kill -TERM $(cat <RUN_DIR>/run_headless.pid)                                            # stop
```
`<gamedir>` contains `TheAbbeyOfCrimeExtensum.jar` (refused under `original/`). Env:
`XVFB_BIN` (default `tools/xvfb-root/usr/bin/Xvfb`), `XVFB_SCREEN` (1920x1080x24), `XVFB_EXTRA`
(extra Xvfb arguments), `JAVA_BIN`, `JAVA_MEM`, `JAVA_EXTRA`, `JAR_NAME`, `RUN_DIR`, `SHOT_DIR`,
`WINDOW_TIMEOUT` (120 s), `DRIVER_TIMEOUT` (1800 s), `ALLOW_NO_BWRAP` (0; 1 runs without hiding
`/dev/snd`, with a WARNING), `XVFB_AUTOREPEAT` (0: X key autorepeat is turned off with `xset -r`
when `xset` exists, so a held key is one press and one release; 1 keeps autorepeat on).
Prerequisites, none in git: Xvfb unpacked into `tools/xvfb-root/`
(git-ignored; there is no system Xvfb here): `(cd tools && apt-get download xvfb && dpkg-deb -x
xvfb_*.deb xvfb-root)`, or point `XVFB_BIN` at one; `bwrap`; `pactl` and `parec` (PulseAudio or
PipeWire); `xdotool`, `xwininfo`, `xwd`; ImageMagick 6 (`convert`, `identify`); coreutils
`realpath` and `timeout`. The script stops with `missing tool: …` if `xdotool`, `xwd`, `convert`,
`pactl`, `xwininfo`, `realpath` or `timeout` is absent (line 73), and without `bwrap` unless
`ALLOW_NO_BWRAP=1`; `parec` (`audio_level`) and `identify` (`png_hash`) are needed only by those
helpers, and `xset` is optional. Tour knobs: `PHASES` (default `intro parchment
play menu walk gameover`), `PARCH_FULL`, `GAMEOVER`, `INTRO_SECS` (52). Per run: `game.log`,
`evidence.log`, `driver.log`, `xvfb.log`. Helpers in `tools/headless_lib.sh`: `shot`, `burst`, `tap
KEY [hold]`, `hold KEY s`, `wait_s`, `wait_stable`, `frame_hash`, `png_hash`, `check_invisible`,
`check_audio`, `audio_level`, `game_geom`. Avoid the `keys` helper (12 ms presses). `audio_level`
computes peak and RMS of the null-sink monitor with `parec | od | awk` only: since Phase E it no
longer calls `python3` (the project runs Python only through `uv`); the first run of the fixed
version logged `samples=263366 peak=15649 rms=2725.0` (`work/phaseE/fixer_r1/tour-sv/evidence.log`).
Invisibility and silence: private Xvfb via `-displayfd`; null sink `abbey_mute_$$` + `PULSE_SINK`;
a private ALSA config (`pcm.!default` = pulse → null sink); `bwrap --dev-bind / / --tmpfs /dev/snd`
(only the `default` mixer remains); an audio watchdog; `DISPLAY=:0 xdotool search` before and after;
cleanup by PID in a trap. Every run logged `INVISIBLE OK` and the java sink-input on the null sink
(peak 13419 recorded there).

### 7.2 Geometry
Window 1296×871 at +312+104 (no WM, no decorations; `Abadia.v = 320·4+16`, `w = 208·4+39`). The
320×208 frame is drawn at window offset (8,19), scaled **exactly ×4 nearest-neighbour**, so the
native PNGs from `shot` are the framebuffer. Frame layout: play area y 0..175; `marcador.png` y
176..207; dialogue box y 146..175 (text at x 32, y 151/163; face at (6,153); ▶▶ at (306,164)); hour
strip (4,197). F1 / menu FULLSCREEN destroys the window and maps a new one (1920×1080, ×5 at
(160,20)); the helpers re-find it. Map mode and the post-ending `abadia.e` scene do not follow this
mapping.

### 7.3 Input
XTEST `keydown`/`keyup` while X focus is on the frame's **`FocusProxy`** child (the launcher sets it).
With focus on the frame itself every key is dropped (VERIFIED in several runs). XSendEvent
(`--window`) was not properly tested (its focus state was not logged); do not use it. Hold each key
longer than one game frame (33 ms intro/play, 16 ms menu, 6 ms parchment); 0.2–0.25 s is the
margin. Space, Left and Right are edge-triggered (release between presses).
Keys (`abadia.C`): Enter 10 (map if available; also intro skip and menu select), Esc 27 (menu; in
the menu = CONTINUE), Space 32, Left/Right 37/39 (turn, classic), Up 38, Down 40, Q 81 + R 82 (held
together at the mirror), W 87 (directional walk), F1 112 (fullscreen). There are no yes/no keys.

### 7.4 Checkpoints (seconds since java start, Java 11, this machine)
| checkpoint | en | es |
|---|---|---|
| window mapped | 0.59–0.72 | same |
| loading plateau | 3.01–5.70 | 2.60–4.77 |
| manuydani / pacoyjuan / novela / pelicula | 11.13 / 17.74 / 24.13 / 31.00 | 10.30 / 16.94 / 24.05 / 30.55 |
| monje / logo / press-to-start | 37.61 / 42.55 / 47.01 (blinks, period ≈ 3.27 s) | 37.09 / 41.97 / 46.31 |

Timing varies by up to ~1 s per run on an idle machine (the music decode during loading), and by
~5 s under load (Phase E fixer tour: manuydani at 16.16 s against 10.85–11.67 s in the other tours,
the later steps at their normal spacing; `work/phaseE/fixer_r1/tour-sv/driver.log`), so **drivers
must detect screens by pixels**, not fixed times. Space/Enter skip credits 1..6 (taps on the loading screen and
during the 2.1 s press-to-start fade are swallowed). Space at press-to-start: fade 64 frames, then
the intro parchment (en 279 s, es 299 s; Space skips it during writing). Play starts outside the gate
(HUD "DAY I"/"TERCE"). `hold Up 3` (classic) walks into the courtyard → Remigio's `g[49]`: 3 boxes
of 1, 1 and 2 lines; later `g[157]`, `g[50]`. Esc → menu (all pages captured). Idling ends in the
abbot's `g[12]` and the 0 % end screen 258–293 s after play starts. The time varies between runs
(the idle path uses an unseeded `Random`), yet in Phase E a patched and a pristine run started in
the same second reached it within 0.03 s of each other in en, es and pl (630.78/630.80,
636.60/636.61, 647.39/647.41 s after java start; `work/phaseE/runs/{en,es,pl}-{patched,pristine}/driver.log`),
so start timing may explain most of the spread (INFERRED). Compare screenshots of static or text
frames, not long idle sequences.
Reference sets: `screenshots/pristine_en/` (319 PNG) and `screenshots/pristine_es/` (320 PNG).
Contact sheets are in `work/phaseA/images/runtime_sheets/`. PNGs carry a
tEXt comment with the window title, so compare pixels (`identify -format %#`), not file hashes.

### 7.5 Files the game writes
`savedata.bin` next to the jar (only on SAVE). 10 `abbey*.tmp` decoded-audio files, 246 MiB total,
in `java.io.tmpdir` (the launcher redirects it to `<run>/javatmp`; deleted on normal exit or
SIGTERM, **left behind on SIGKILL**). `~/.java/fonts/<jdk>/fcinfo…properties` (JDK font cache, once
per JDK). `/tmp/hsperfdata_<user>/<pid>` (removed at exit). The harness itself leaves WirePlumber
volume entries in `~/.local/state/wireplumber/restore-stream`.

### 7.6 Swedish-run caveat
`run_headless.sh` line 56 hard-codes `TITLE_RE='Abad|Abbey|Abbaz|abbaye|Abtei'`
(`headless_lib.sh` honours an env override; the launcher does not). If `E.h[4]` becomes a title
without one of these words, the launcher times out after 120 s and the `:0` check goes blind. Keep a
matching word, or extend the regex in all three copies before the Swedish runs:
`tools/run_headless.sh` (line 56, hard-coded), `tools/headless_lib.sh` (env default) and
`tools/lint_strings.py` (`TITLE_RE`, used for the `E.h[4]` warning).
**Resolved:** `E.h[4]` = `La Abadía del Crimen Extensum` (DECISIONS D6), which matches `Abad`;
`tools/lint_strings.py` warns if a future title stops matching. Every Swedish run found its window
and logged `INVISIBLE OK` (`screenshots/runtime_sv/INDEX.md`, `opening/INDEX.md`).

### 7.7 Expected log content
Java 11: exactly two startup stack traces from `abadia.c.b.a(String)` (ClassCastException
AppClassLoader→URLClassLoader, then NullPointerException; a `/lib/*.jar` classpath hack). They are
harmless, and the vorbis SPI is in the jar. Java 8: an empty log. Anything else (an exception,
`Caracter:`) is a failure. VERIFIED for the Swedish build: every Phase E `game.log` holds exactly
these two traces and no `Caracter:` line, as the pristine game does.

### 7.8 Day-1 route to the opening messages (VERIFIED, Phase E runs 1, 2 and 4)

Navigation notes for a driver that must reach the abbot's welcome and the day-1 meetings.
Coordinates are the character positions logged by the read-only Java agent
(`work/phaseE/agent/src/StateAgent.java`, loaded with `JAVA_EXTRA=-javaagent:…` through
`tools/run_headless.sh`; it writes `RUN_DIR/agent/state.txt` and `events.log`). The route was
driven by `work/phaseE/drivers/follow.py` (`uv run work/phaseE/drivers/follow.py RUN_DIR [--who 8]
[--gap 3] [--until-cn 51] [--goto o,p]`: it reads `state.txt` and steers Vilhelm with XTEST keys
on the run's private display), with `recorder.sh`, `skip_pages.sh` and `k.sh` from the same
directory. Agent and drivers live only in the git-ignored `work/phaseE/`; they are not part of
`tools/`. Full account: `screenshots/runtime_sv/opening/INDEX.md`.
1. **Remigio's walk.** Walk into the courtyard (`g[49]`), then follow Remigio 3–6 units behind him.
   He needs Vilhelm within ±8 units (`Abadia.t.v()`, §1.8); otherwise he waits and, 40 ticks later, says
   `g[50]` (which repeats and costs obsequium). Along the walk come `g[157]`, `g[158]`, `g[159]`,
   then `g[51]` at the cell door.
2. **The abbot.** Step around Remigio to the right, through the door at (169,31), and two steps
   toward the abbot: `g[1]` (24 pages; Space advances one page, because Vilhelm is under script
   control), then `g[5]`. Some time after `g[5]`, Adso asks who Ubertino is (`g[145]`).
3. **Back to the courtyard the long way.** The corridor door (141,127) → (138,127) that Remigio
   used is locked for Vilhelm.
4. **Order matters: Ubertino and Salvatore come after `g[5]` and before Severinus.** Ubertino's
   `g[53]` needs day 1 TERCIA, room 117, Vilhelm within ±2 (`b/q.java` case 2); Salvatore's `g[54]`
   needs TERCIA after flag `g.a`, within ±2, player control (`b/n.java` case 2). When Severinus's
   tour ends after `g[58]`, the hour becomes SEXTA (`b/o.java` case 6 sets `D.e`; Adso says
   `g[10]`), and both are unreachable that day.
   - Ubertino: round the low choir wall of the church, (141,67) → (141,80) → (149,80) → (149,73).
   - Salvatore patrols (88,155) → (67,81) → (191,167); meet him as he crosses near (168,145)
     (run 4 followed him from (168,137) and got `g[54]` at (189,166)).
5. **Severinus.** West to his beat near (115,182) → `g[55]`; the tour then runs by itself: `g[56]`,
   `g[57]` at the refectory, `g[58]` at the kitchen, then `g[10]`.

---

## 8. Harnesses and checkers

The project's maintained copies are in `tools/`: `tools/harness/` (this harness, self-contained),
`tools/text_sim.py`, `tools/letras.py` (port of `letras_render.py`), `tools/render_strings.py`,
`tools/regress.py`, and `tools/java/{PatchJ,PatchStrings,ClassDiff,VerifyClasses}.java` (the ASM
patchers and verifiers that `tools/build.py` runs: ports of `PatchJ` and `PatchTW`, the class
comparison, and the `CheckClassAdapter` + `-Xverify:all` check) (`tools/README_tools.md`). The
Phase A originals below stay as the reference.

**`work/phaseA/harness/render.sh`**: draws every string of a language with the game's own code,
headless (`env -u DISPLAY`, `-Djava.awt.headless=true`; no Frame or Window is loaded; Java 8 and 11
are pixel-identical).
```sh
H=/home/ran/the_abbey_of_crime_extensum_swedish/work/phaseA/harness
$H/build.sh
$H/render.sh --jar PATCHED.jar [--res OVERLAY/res] --lang de --out OUT/de --ref-lang es [--no-images]
$H/render.sh --jar $H/lib/game-pristine.jar --lang de --out OUT --only-custom \
   --msgfile M.txt --textfile T.txt --parchfile P.bin          # preview draft text
```
Exit codes: 0 OK, **2 errors** (missing glyph, crash or no-progress layout, `--ref-lang` mismatch in
sizes, `@N` sequence or "starts with @"), 1 usage or crash. Outputs: `report.txt`, `layout.json`,
`coverage.txt` (code points with ink, computed empirically, so it follows any patched j/font),
3× sheets, `raw/` 1× PNGs (`msg_g###_p#.png` 320×30 = screen (0,146); `menu_state*`, `slots_set*`,
`endgame_pct*`, `hud_hour*`, `parch_*`). Game code draws every pixel: `j.c(int)/e()/f()/c()`,
`w.a(int,int)`, `w.c()`, `j.a(String,…)`, `v.c()/v.e()/v.b()`, `y.a(G,G)`. Orchestration is
replicated: the page loop (`while ct < cs.length` instead of `j.b()` timing), the menu value suffixes,
the end-screen calls (pct 5/95/100, although 100 cannot occur there), and `D.c()`'s two assignments.
Known gaps: it accepts lowercase letters that have ink (add the §1.13 lint); its "word > 35 stalls
forever" text is wrong (the real effect is lost text), but rejecting it is correct; its
trailing-space error is correct to reject even though the real crash is conditional.

Other tools:
- `work/phaseA/scripts/text_sim.py`: Python port of `c/e/b`. It matches the real code on all 978
  shipped messages (pages, lines, speaker, ticks, leftover `bR`). Use it for **timing**
  (`simulate(text, bR0)`). Its `int()` is laxer than Java `parseInt`, it does not flag `@15`, `%` or
  undrawable chars, and it defaults to `bR0=0`.
- `work/phaseA/refute_text_1/java/Probe.java` (+ `run.sh`): drives the real `abadia.j` with optional
  `bR` carry-over, Space and `b.i.c`; modes dump/consts/seq/glyphs/render/save.
- `work/phaseA/scripts/letras_render.py`: parchment emulator (`pages`, `width --sv`, `dump`,
  `measure`, `sheet`); pixel-identical to the real code on the 93 shipped pages and the Swedish
  prototype. It crashes on 0x8A/0x9F, so whitelist bytes.
- Real parchment drivers: `work/phaseA/harness/src/PergHarness.java`,
  `refute_runtime_1/src/abadia/ParchHarness.java`
  (`java -Djava.awt.headless=true -cp classes:<jar> abadia.ParchHarness <langIdx> <intro|ending|file:PATH> <outPrefix> <maxFrames>`),
  `refute_parchment_0/java/Rec.java` (records every drawLine; END/UNCAUGHT/HANG).
- Font/patch: `proto_font/src/PatchJ.java`, `VerifyJ.java`, `scripts/make_font.py`,
  `proto_font/src/abadia/RegressAll.java`. w/E strings: `refute_deslot_1/scripts/PatchTW.java`
  (also `scripts/PatchProbeW.java`, `refute_deslot_0/scripts/PatchW.java`).
- Format re-checks: `scripts/format_checks.py` (menu limits, parchment edges, letras slots);
  `scripts/make_context_tsv.py`.

---

## 9. Open questions: status after Phases E and F

Questions 1–6 and 9 are **settled**; each keeps its number and says how. Questions 7, 8 and 10
stay open (UNCERTAIN or INFERRED); none of them blocks the translation.

1. **Remigio's walk timing: SETTLED (VERIFIED).** Measured live in Phase E runs 1, 2 and 4 with a
   read-only agent: g157 has 220–223 ticks until Remigio reaches waypoint 8 and g158 interrupts
   it, g158 has 187 and g159 319. Remigio never paused, so these are the shortest windows. The
   g157 cap is now **215** ticks (the old "≤ 232" was the longest shipped text, which the window cuts);
   the others keep their shipped caps (§1.8, DECISIONS D12). Evidence:
   `work/phaseE/runs/run{1,2,4}/agent/events.log`, `screenshots/runtime_sv/opening/INDEX.md`.
2. **Abbot's welcome `g[1]`: SETTLED (VERIFIED).** Reached at runtime by following Remigio and
   stepping into the cell: all 24 pages, in runs 1, 2 and 4 (run 1 untouched, 1265 ticks; runs 2
   and 4 advanced with Space, one page per tap). Route in §7.8; evidence as for question 1.
3. **Ending parchment: SETTLED (by the game's own code).** It still cannot be reached by an automated
   drive (the game must be solved). `pergamino2` was run through the real `y.a()` by the harness:
   8 pages, 87 lines, widest ink x = 238, no `Caracter:` line, and `tools/letras.py` is
   pixel-identical to the real code on it (`screenshots/strings/de/parchment_ending_*.png`,
   `raw/parch_ending_p01..08.png`, `report.txt`). The build's byte whitelist stays mandatory, because
   a bad byte there is an unskippable soft-lock.
4. **Final pixel designs: SETTLED (Phase D builder/critic loop).** The fuente ring (cell 80,
   §3.4), the precomposed HUD Ö (cell 74, §2.4) and the six letras glyphs (§4.7) are final in
   `assets_sv/glyphs/{fuente_add,letras_add}.json`. Critic rounds: `work/phaseD/fuente_critic_r1/`,
   `letras_critic_r1/`, `letras_critic_r2/`; rounds and verdicts for these glyphs and for every
   Swedish image are in the §6.1 table (no image ran out of its 6 rounds). Rendered with the game's code
   (`screenshots/strings/de/`) and seen live (`screenshots/runtime_sv/`).
5. **Window title `E.h[4]`: SETTLED.** The Spanish real name `La Abadía del Crimen Extensum`
   (DECISIONS D6); it matches `TITLE_RE`, so the harness needed no change (§7.6).
6. **manuydani base: SETTLED.** es, with "Celemín"; "och" is set with the en/es spacing
   (`tools/images/build_manuydani.py`; GLOSSARY §8).
7. **Index 0 reachability** (`b.a.e = 0` reset): INFERRED unreachable. It would break every language
   alike. Keep `g[0] = ""`.
8. **Fire-and-forget collisions** (e.g. abbot 68 vs a hotspot message): inferred from control flow,
   not reproduced. No action needed beyond reasonable lengths.
9. **Live-vs-harness equivalence: SETTLED (VERIFIED).** The dialogue box of each live shot
   (crop 0,146,320,30; near-white text pixels; the animated face and the blinking ▶▶ masked) was
   compared with the harness render `screenshots/strings/de/raw/msg_gNNN_pK.png`: **277 of 277**
   shots from runs 1–3 had 0 differing pixels against the render of their jar, and **134 of 134**
   run-4 shots against the current render (about 600 text pixels per crop). Evidence:
   `screenshots/runtime_sv/opening/INDEX.md`, `work/phaseE/scripts/match_pages.sh`,
   `work/phaseE/fixer_r2/match_rec4.txt`. So a harness render stands for live play, which is how
   the later string edits were checked: the 16 Phase E edits not shown in the opening runs, and
   the Phase F edits (g54, g61, g64, g122, g131, g149, g150, g163), which are verified by harness
   render only. g54's live shots (run 4, jar `0ad2bbf0…`) show its text before Phase F added the page break
   after `DOMINE FRATE MAGNIFICENTISSIMO.`: against the Phase F render, run 4 still matches on 130 of
   its 134 shots, and the other 4 are g54 pages 4–5 in their earlier layout
   (`work/phaseF/match_rec4_phaseF.txt`). The current g54 pages 4–5 have not been seen live.
10. Object-bitmask meanings in `x.a(0,…)` were named from the message text, not from code. They do
    not matter for translation.

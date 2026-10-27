# Swedish opening at runtime

Phase E run of 2026-10-27. The game is the built `game/` in language slot `de`. It ran only
through `tools/run_headless.sh`: private Xvfb found via `-displayfd`, a null audio sink, and bwrap
hiding `/dev/snd`. Keys were sent with XTEST on that private display. Three runs:
`work/phaseE/runs/run1`, `run2` and `run3`, plus run 4 (`work/phaseE/runs/run4`, Phase E round 2),
which replayed run 2's route to re-capture g54 after its first line was reworded.

**Jars.** Runs 1-3 used jar sha256 `e9a95e0c…`. Run 4 used the current `game/` jar `0ad2bbf0…`.
The two differ only in `abadia/k.class` (entry CRC diff over all 445 entries), and within it only in
`g` strings: g52, g54, g61, g64, g75, g77, g85, g114, g118, g122, g125, g131, g143, g149, g150,
g155 and g163. g54 is the only one of these that the runs show, and run 4 re-captured it. The
other pages here are unchanged on the current jar: run 4's 134 shots of g49, g157-g159, g51, g1,
g5, g145, g53 and g54 all match the current harness render exactly.

## Result

- **Every message in the brief was reached at runtime:** g49, g157, g158, g159, g51, g1 (24
  pages), g5, g55, g56, g57, g58, g53 (17 pages) and g54 (9 pages). g50 was also triggered, on
  purpose, in run 3. Three other messages fired on the way and were captured too: g145 (Adso
  asks who Ubertino is), g102 (the well) and g10 (Adso at SEXTA).
- **92 pages, every page of every message.** The number of pages seen per message equals the
  game's page count (`text_sim`, which is the same as the harness).
- **Rendering.** Each recorded shot's dialogue box (320x30 at y=146) was compared with the harness
  render `screenshots/strings/de/raw/msg_gNNN_pK.png`. Only near-white text pixels were compared,
  because the live box is semi-transparent over the scene. The face (mouth animates) and the
  blinking ▶▶ glyph were masked. **277 of 277 shots from the three runs match exactly (0 differing
  pixels).** The sheets were also checked by eye: Å Ä Ö are correct, no glyph is missing, and no
  page is blank or a lone word. This settles FORMAT §9 question 9: live boxes equal the harness.
  (Measured on the harness render of the time. Against today's render, run 2 still matches on 130
  of its 134 shots. The other 4 are g54 pages 1-2, which show the old first line. Run 4 replaced
  all g54 pages, and **134 of 134 run-4 shots match the current render exactly**. See
  `work/phaseE/fixer_r2/match_rec2_now.txt` and `match_rec4.txt`.)
- **Remigio's walk.** g157, g158 and g159 each showed all their pages. Each ended on its own before
  the next one started, in both runs (table below).
- **Logs.** Every `game.log` has exactly the two Java 11 startup traces (FORMAT §7.7) and no
  `Caracter:` line. `evidence.log` says `INVISIBLE OK` at the start and end of each run. The
  game's audio went only to the null sink, and every run ended with `cleanup ... done rc=0`.

## Remigio's walk: timing (1 tick = 3 frames ≈ 0.1 s)

| msg | shown, run 1 / run 2 | text_sim | window until the next message is forced, run 1 / run 2 | margin |
|---|---|---|---|---|
| g157 | 580 / 580 frames = 193 ticks | 194 | 660 / 670 frames = **220 / 223 ticks** (arrival at waypoint 8 → g158) | 27–30 ticks |
| g158 | 262 / 262 = 87 | 88 | 560 / 560 = 187 (waypoint 9 → g159) | ~99 |
| g159 | 528 / 530 = 176 | 177 | 958 / 956 = 319 (waypoint 10 → g51) | ~143 |
| g51 | 200 / 198 = 66 | 67 | ended on its own; the abbot's g1 starts when Vilhelm steps into the cell | – |

- **No pauses.** Remigio never stopped during either walk: one step every 8 frames, plus
  14-frame turns at corners. So these windows are the natural pace, the shortest possible.
  Remigio only ever waits for Vilhelm; he never hurries.
- **Page boundaries** matched `text_sim` to within 1 tick:
  - g157 pages started at 0 / 69.3 / 121.3 ticks (sim 0 / 70 / 122);
  - g159 pages started at 0 / 56.7 / 97.3 / 138.7 (sim 0 / 57 / 98 / 139).
- **For FORMAT §1.8 and §9 question 1:** the measured g157 window is about 220 ticks, which is
  less than the "≤ 232" cap derived from Italian. Swedish g157 (194 ticks) fits with 27 ticks to
  spare. Any future edit of g157 should stay under about 215 ticks.

**Space.** In run 1, g1 played untouched: 3794 frames = 1265 ticks. In run 2, Space was tapped
once per g1 page, 1.8 s after the page appeared and after it had been shot. That was 24 taps, and
each advanced exactly one page (same `ct` sequence, all 24 pages captured). Space only works when
Vilhelm is under script control, which is also when the ▶▶ glyph is drawn: g1, g53, Severinus's
tour. Free-play messages advance on their own and have no ▶▶: g49, the walk, g54, g145.

## How each message was reached

- **Run 1.**
  - The intro and the parchment were skipped with Space.
  - A read-only Java agent logged positions and message state. It was loaded with
    `JAVA_EXTRA=-javaagent:...`, still through `run_headless.sh`, and its source is
    `work/phaseE/agent/src/StateAgent.java`.
  - `follow.py` steered Vilhelm along Remigio's trail, 3–6 units behind him. Remigio needs Vilhelm
    within ±8 units (`Abadia.v()`), or he waits and then says g50.
  - At the cell, Vilhelm stepped around Remigio to the right, went through the door at (169,31),
    and took two more steps toward the abbot. That started g1, then g5.
  - Then back to the courtyard. The corridor door at (141,127) that Remigio had used was locked
    for Vilhelm, so he went the long way round.
  - West to Severinus's beat near (115,182) → g55, after which the tour runs by itself: g56, then
    g57 at the refectory and g58 at the kitchen.
  - When g58 ends, the hour becomes SEXTA (Adso says g10). Ubertino's g53 and Salvatore's g54 need
    day 1 TERCIA, so they must come **before** meeting Severinus.
- **Run 2.**
  - The same opening, with g1 advanced by Space.
  - Then the church first: around the low choir wall, (141,67) → (141,80) → (149,80) → (149,73),
    to Ubertino in room 117 → g53.
  - Back to the courtyard, and Salvatore as he crossed at (168,145) → g54.
- **Run 3.**
  - g49, then Vilhelm walked back out of Remigio's ±8 box. g157 started, and ~43 ticks later g50
    interrupted it, as `b/m.java` does with `j.b(50)` after 40 ticks.
  - g50 repeats while Vilhelm stays away, and each repeat costs obsequium, so the run was stopped.
- **Run 4** (Phase E round 2, jar `0ad2bbf0…`). Run 2's route, replayed with the same tools:
  - `follow.py` behind Remigio until g51, then into the cell; g1 advanced with Space (24 taps), then g5;
  - the church route to Ubertino → g53 (17 pages, advanced with Space);
  - back to the courtyard at (168,137), then `follow.py --who 10 --gap 1` behind Salvatore on his
    loop past (168,145) → g54 at (189,166), all 9 pages shot.
  - `game.log` has only the two Java 11 startup traces and no `Caracter:` line; `evidence.log` says
    `INVISIBLE OK` at start and end, the audio went only to the null sink, and the run ended
    `done rc=0`.

Nothing was saved. `original/` and `game/` were not written. Each run was ended with
`touch RUN_DIR/stop`, and the launcher cleaned up by PID.

The agent only reads static fields, every 20 ms, from a low-priority daemon thread. The measured
message durations equal `text_sim` exactly, which shows it did not disturb the game's tick logic.

## Context frames (`context/`)

| file | shows |
|---|---|
| `01_start_of_play.png` | Vilhelm and Adso outside the gate, HUD "DAG I" / "TERS" |
| `02_cell_door_after_g51.png` | Remigio at the cell door after g51 |
| `03_cell_abbot_before_g1.png` | the abbot waiting in the cell, Vilhelm in the doorway |
| `04_cell_after_g5.png` | the abbot gone after g5 |
| `05_severinus_tour_start.png` | Severinus meets Vilhelm in the garden (g55 starts) |
| `06_church_choir_ubertino_in_nave.png` | the church: Vilhelm behind the choir wall, Ubertino in the nave |
| `07_salvatore_approaching.png` | Salvatore crossing the courtyard before g54 |
| `08_g50_remigio_waits.png` | g50 "KOM, BRODER. ABBOTEN VÄNTAR PÅ ER." (run 3) |

## Files

- `pages/`: one native frame per page. The native PNG is the game's exact 320x208 framebuffer.
- `sheets/gNNN.png`: the dialogue boxes of each message, stacked, at 2x.
- `pages.tsv`: which raw shot each page file comes from.
- Raw shots in `work/phaseE/sv_opening/`:
  - `rec/`: run 1, 130 shots;
  - `rec2/`: run 2, 134 shots;
  - `rec3/`: run 3, 13 shots;
  - `rec4/`: run 4, 134 shots (the source of the g54 pages);
  - `nav/`: navigation frames.

  Each page has a `_first` shot (+0.3 s) and a `_last` shot (re-shot every ~1 s while the page
  stays).
- Logs per run in `work/phaseE/runs/runN/`:
  - `game.log` and `evidence.log`;
  - `driver.log`, with `REC page` and `SKIP` lines;
  - `agent/events.log`, with MSG_START, PAGE and MSG_END events plus positions;
  - `follow*.log`.
- Tools:
  - `work/phaseE/agent/`: `state-agent.jar` for run 1, `state-agent2.jar` for runs 2–3 (all
    characters, plus page events);
  - `work/phaseE/drivers/`: `recorder.sh`, `follow.py`, `skip_pages.sh`, `k.sh`;
  - `work/phaseE/scripts/`: `match_pages.sh`, `curate.sh`, `strips.sh`, `expected_pages.py`,
    `gen_index.py`.

## Every page (one native 320x208 frame per page, story order)

`run` = which run the frame comes from. Text = the page as laid out by the game (`/` = line break).

| file | msg | page | speaker | text | run |
|---|---|---|---|---|---|
| [`001_g049_p01.png`](pages/001_g049_p01.png) | g49 | 1/3 | Remigio | VÄLKOMMEN TILL VÅRT KLOSTER, / BRODER. | 1 |
| [`002_g049_p02.png`](pages/002_g049_p02.png) | g49 | 2/3 | Remigio | JAG ÄR REMIGIO, KÄLLARMÄSTAREN. | 1 |
| [`003_g049_p03.png`](pages/003_g049_p03.png) | g49 | 3/3 | Remigio | JAG BER ER ATT FÖLJA MIG. ABBOTEN / VÄNTAR PÅ ER. | 1 |
| [`004_g157_p01.png`](pages/004_g157_p01.png) | g157 | 1/3 | Vilhelm | DETTA KLOSTER ÄR UNDERBART VACKERT, / BRODER. OCH SÅ KLOKT ANLAGT. | 1 |
| [`005_g157_p02.png`](pages/005_g157_p02.png) | g157 | 2/3 | Remigio | SÅ ÄR DET. KORET OCH ALTARET VETTER / MOT ÖSTER. | 1 |
| [`006_g157_p03.png`](pages/006_g157_p03.png) | g157 | 3/3 | Remigio | PÅ SÅ VIS VÄCKER SOLEN I GRYNINGEN / MUNKARNA I CELLERNA. | 1 |
| [`007_g158_p01.png`](pages/007_g158_p01.png) | g158 | 1/2 | Remigio | DETTA ÄR KORSGÅNGEN. | 1 |
| [`008_g158_p02.png`](pages/008_g158_p02.png) | g158 | 2/2 | Remigio | EN STILLA PLATS FÖR VANDRING OCH / BETRAKTELSE. | 1 |
| [`009_g159_p01.png`](pages/009_g159_p01.png) | g159 | 1/4 | Remigio | SENARE FÅR NI TRÄFFA DE ÖVRIGA / MUNKARNA I KLOSTRET. | 1 |
| [`010_g159_p02.png`](pages/010_g159_p02.png) | g159 | 2/4 | Remigio | NU ÄR DE UPPTAGNA MED SINA SYSSLOR. /  | 1 |
| [`011_g159_p03.png`](pages/011_g159_p03.png) | g159 | 3/4 | Vilhelm | JAG FÖRSTÅR. | 1 |
| [`012_g159_p04.png`](pages/012_g159_p04.png) | g159 | 4/4 | Remigio | SNART ÄR VI FRAMME. | 1 |
| [`013_g050_p01.png`](pages/013_g050_p01.png) | g50 | 1/1 | Remigio | KOM, BRODER. ABBOTEN VÄNTAR PÅ ER. | 3 |
| [`014_g051_p01.png`](pages/014_g051_p01.png) | g51 | 1/1 | Remigio | DETTA ÄR ER CELL. ABBOTEN VÄNTAR PÅ / ER DÄRINNE. | 1 |
| [`015_g001_p01.png`](pages/015_g001_p01.png) | g1 | 1/24 | Abboten | VÄLKOMMEN TILL VÅRT KLOSTER, / BRODER. | 1 |
| [`016_g001_p02.png`](pages/016_g001_p02.png) | g1 | 2/24 | Abboten | NÅGOT FRUKTANSVÄRT HAR HÄNT. | 1 |
| [`017_g001_p03.png`](pages/017_g001_p03.png) | g1 | 3/24 | Abboten | ADELMO, VÅR UNGE MINIATYRMÅLARE, / HITTADES NERE I RAVINEN. | 1 |
| [`018_g001_p04.png`](pages/018_g001_p04.png) | g1 | 4/24 | Abboten | HAN FÖLL TROLIGEN NATTETID FRÅN ETT / FÖNSTER I BYGGNADENS ÖSTRA TORN. | 1 |
| [`019_g001_p05.png`](pages/019_g001_p05.png) | g1 | 5/24 | Vilhelm | VAR HAR NI BEGRAVT KROPPEN? | 1 |
| [`020_g001_p06.png`](pages/020_g001_p06.png) | g1 | 6/24 | Abboten | PÅ KYRKOGÅRDEN, NATURLIGTVIS. | 1 |
| [`021_g001_p07.png`](pages/021_g001_p07.png) | g1 | 7/24 | Vilhelm | JAG FÖRSTÅR VAD SOM OROAR ER. | 1 |
| [`022_g001_p08.png`](pages/022_g001_p08.png) | g1 | 8/24 | Vilhelm | OM DEN OLYCKLIGE, GUD FÖRBJUDE, / HADE TAGIT SITT LIV, | 1 |
| [`023_g001_p09.png`](pages/023_g001_p09.png) | g1 | 9/24 | Vilhelm | SÅ HADE NI HITTAT ETT ÖPPET / FÖNSTER. MEN DET GJORDE NI INTE. | 1 |
| [`024_g001_p10.png`](pages/024_g001_p10.png) | g1 | 10/24 | Abboten | VEM HAR SAGT DET TILL ER? | 1 |
| [`025_g001_p11.png`](pages/025_g001_p11.png) | g1 | 11/24 | Vilhelm | NI SJÄLV. NI HAR BEGRAVT HONOM I / VIGD JORD. | 1 |
| [`026_g001_p12.png`](pages/026_g001_p12.png) | g1 | 12/24 | Vilhelm | DET HADE NI INTE TILLÅTIT OM HAN / HADE TAGIT LIVET AV SIG. | 1 |
| [`027_g001_p13.png`](pages/027_g001_p13.png) | g1 | 13/24 | Abboten | SÅ ÄR DET. ALLA FÖNSTER VAR / STÄNGDA. | 1 |
| [`028_g001_p14.png`](pages/028_g001_p14.png) | g1 | 14/24 | Abboten | DÄRFÖR FRUKTAR JAG ATT EN AV / MUNKARNA HAR BEGÅTT ETT BROTT. | 1 |
| [`029_g001_p15.png`](pages/029_g001_p15.png) | g1 | 15/24 | Abboten | JAG BER ER ATT FINNA HONOM INNAN / INKVISITORN BERNARDO GUI KOMMER, | 1 |
| [`030_g001_p16.png`](pages/030_g001_p16.png) | g1 | 16/24 | Abboten | TY JAG VILL INTE ATT VÅRT KLOSTERS / GODA NAMN SKA BEFLÄCKAS. | 1 |
| [`031_g001_p17.png`](pages/031_g001_p17.png) | g1 | 17/24 | Vilhelm | FÅR JAG STÄLLA FRÅGOR TILL DE ANDRA / MUNKARNA? | 1 |
| [`032_g001_p18.png`](pages/032_g001_p18.png) | g1 | 18/24 | Abboten | DET FÅR NI. | 1 |
| [`033_g001_p19.png`](pages/033_g001_p19.png) | g1 | 19/24 | Abboten | MEN NI MÅSTE ÅTLYDA MINA / BEFALLNINGAR OCH KLOSTRETS REGLER. | 1 |
| [`034_g001_p20.png`](pages/034_g001_p20.png) | g1 | 20/24 | Abboten | INFINN ER TILL TIDEBÖNERNA OCH / MÅLTIDERNA. | 1 |
| [`035_g001_p21.png`](pages/035_g001_p21.png) | g1 | 21/24 | Abboten | OM NATTEN MÅSTE NI VARA I ER CELL. /  | 1 |
| [`036_g001_p22.png`](pages/036_g001_p22.png) | g1 | 22/24 | Vilhelm | HAR UBERTINO REDAN KOMMIT? | 1 |
| [`037_g001_p23.png`](pages/037_g001_p23.png) | g1 | 23/24 | Abboten | JA, HAN KOM FÖR NÅGRA DAGAR SEDAN. / NI HITTAR HONOM I KYRKAN. | 1 |
| [`038_g001_p24.png`](pages/038_g001_p24.png) | g1 | 24/24 | Abboten | HAN TILLBRINGAR DET MESTA AV SIN / TID I BÖN OCH BETRAKTELSE. | 1 |
| [`039_g005_p01.png`](pages/039_g005_p01.png) | g5 | 1/1 | Abboten | NU MÅSTE JAG GÅ. | 1 |
| [`040_g145_p01.png`](pages/040_g145_p01.png) | g145 | 1/3 | Adso | MÄSTARE, VEM ÄR UBERTINO? | 1 |
| [`041_g145_p02.png`](pages/041_g145_p02.png) | g145 | 2/3 | Vilhelm | HAN ÄR EN AV VÅR ORDENS ANDLIGA / FÄDER. | 1 |
| [`042_g145_p03.png`](pages/042_g145_p03.png) | g145 | 3/3 | Vilhelm | FÖR MÅNGA ÄR HAN ETT HELGON, FÖR / ANDRA EN KÄTTARE SOM BÖR BRÄNNAS. | 1 |
| [`043_g053_p01.png`](pages/043_g053_p01.png) | g53 | 1/17 | Ubertino | VILHELM! KÄRASTE BRODER! | 2 |
| [`044_g053_p02.png`](pages/044_g053_p02.png) | g53 | 2/17 | Ubertino | SÅ LÄNGE SEDAN DET VAR! SÅ MYCKET / SOM HAR HÄNT! | 2 |
| [`045_g053_p03.png`](pages/045_g053_p03.png) | g53 | 3/17 | Vilhelm | UBERTINO, JAG ÄR GLAD ATT SE DIG. / STÅR ALLT VÄL TILL? | 2 |
| [`046_g053_p04.png`](pages/046_g053_p04.png) | g53 | 4/17 | Ubertino | VILHELM, SOM DU VÄL VET ÄR DET / SVÅRA TIDER. | 2 |
| [`047_g053_p05.png`](pages/047_g053_p05.png) | g53 | 5/17 | Ubertino | JAG HAR TVINGATS GÖMMA MIG I DETTA / KLOSTER UNDAN MINA FÖRFÖLJARE. | 2 |
| [`048_g053_p06.png`](pages/048_g053_p06.png) | g53 | 6/17 | Ubertino | MEN ONDSKAN FINNS ÖVERALLT, ÄVEN / INOM DESSA MURAR. | 2 |
| [`049_g053_p07.png`](pages/049_g053_p07.png) | g53 | 7/17 | Vilhelm | JAG VET. ABBOTEN HAR BERÄTTAT OM / DET. | 2 |
| [`050_g053_p08.png`](pages/050_g053_p08.png) | g53 | 8/17 | Vilhelm | HAN HAR BETT MIG OM HJÄLP ATT REDA / UT SAKEN. | 2 |
| [`051_g053_p09.png`](pages/051_g053_p09.png) | g53 | 9/17 | Ubertino | SÖK DÅ EFTER VÄLLUST OCH HÖGMOD. | 2 |
| [`052_g053_p10.png`](pages/052_g053_p10.png) | g53 | 10/17 | Ubertino | VÄLLUST, TY DET FANNS NÅGOT... / KVINNLIGT HOS YNGLINGEN SOM DOG. | 2 |
| [`053_g053_p11.png`](pages/053_g053_p11.png) | g53 | 11/17 | Ubertino | OCH DÄRMED NÅGOT DJÄVULSKT. | 2 |
| [`054_g053_p12.png`](pages/054_g053_p12.png) | g53 | 12/17 | Ubertino | MEN JAG NÄMNDE OCKSÅ HÖGMOD, / FÖRSTÅNDETS HÖGMOD. | 2 |
| [`055_g053_p13.png`](pages/055_g053_p13.png) | g53 | 13/17 | Ubertino | DETTA KLOSTER ÄR VIGT ÅT ORDETS / HÖGFÄRD, ÅT VETANDETS BLÄNDVERK... | 2 |
| [`056_g053_p14.png`](pages/056_g053_p14.png) | g53 | 14/17 | Vilhelm | OM DU VET NÅGOT, SÅ HJÄLP MIG. | 2 |
| [`057_g053_p15.png`](pages/057_g053_p15.png) | g53 | 15/17 | Ubertino | INGENTING VET JAG. DET FINNS / INGENTING SOM JAG VET. | 2 |
| [`058_g053_p16.png`](pages/058_g053_p16.png) | g53 | 16/17 | Ubertino | MEN VISSA TING KÄNNER MAN MED / HJÄRTAT. LÅT DITT HJÄRTA TALA. | 2 |
| [`059_g053_p17.png`](pages/059_g053_p17.png) | g53 | 17/17 | Ubertino | RANNSAKA ANSIKTENA, LYSSNA INTE PÅ / TUNGORNA... | 2 |
| [`060_g054_p01.png`](pages/060_g054_p01.png) | g54 | 1/9 | Salvatore | PENITENZIAGITE! LA MORTZ EST SUPER / NOS! BEDJA ATT LO PAPA SANTO KOMMA | 4 |
| [`061_g054_p02.png`](pages/061_g054_p02.png) | g54 | 2/9 | Salvatore | A LIBERAR NOS A MALO DE TUTTE / PECCATA! | 4 |
| [`062_g054_p03.png`](pages/062_g054_p03.png) | g54 | 3/9 | Vilhelm | VARFÖR SADE DU PENITENZIAGITE? | 4 |
| [`063_g054_p04.png`](pages/063_g054_p04.png) | g54 | 4/9 | Salvatore | DOMINE FRATE MAGNIFICENTISSIMO. / JESUS VENTURUS EST ET LOS HOMINES | 4 |
| [`064_g054_p05.png`](pages/064_g054_p05.png) | g54 | 5/9 | Salvatore | DEBENT FACERE PENITENTIA, NO? | 4 |
| [`065_g054_p06.png`](pages/065_g054_p06.png) | g54 | 6/9 | Vilhelm | KÄNNER DU DOLCINIANERNA? | 4 |
| [`066_g054_p07.png`](pages/066_g054_p07.png) | g54 | 7/9 | Salvatore | IO INTE FÖRSTÅ. | 4 |
| [`067_g054_p08.png`](pages/067_g054_p08.png) | g54 | 8/9 | Vilhelm | HAR DU KOMMIT I KLAMMERI MED DEN / HELIGA INKVISITIONEN? | 4 |
| [`068_g054_p09.png`](pages/068_g054_p09.png) | g54 | 9/9 | Salvatore | SALVATORE DUM. IO INTE VETA. DUM... | 4 |
| [`069_g102_p01.png`](pages/069_g102_p01.png) | g102 | 1/1 | Vilhelm | DET FINNS VATTEN I BRUNNEN OCH ETT / ÄMBAR ATT HÄMTA UPP DET MED. | 1 |
| [`070_g055_p01.png`](pages/070_g055_p01.png) | g55 | 1/9 | Severinus | ÄREVÖRDIGE BRODER, JAG ÄR / SEVERINUS, KLOSTRETS ÖRTLÄKARE. | 1 |
| [`071_g055_p02.png`](pages/071_g055_p02.png) | g55 | 2/9 | Severinus | JAG HAR HAND OM BADHUSET, SJUKHUSET / OCH ÖRTAGÅRDARNA. | 1 |
| [`072_g055_p03.png`](pages/072_g055_p03.png) | g55 | 3/9 | Severinus | OM NI SÅ ÖNSKAR, VISAR JAG ER / KLOSTRET. | 1 |
| [`073_g055_p04.png`](pages/073_g055_p04.png) | g55 | 4/9 | Vilhelm | TACK, BRODER. | 1 |
| [`074_g055_p05.png`](pages/074_g055_p05.png) | g55 | 5/9 | Vilhelm | REDAN NÄR JAG KOM LADE JAG MÄRKE / TILL DEN PRAKTFULLA ÖRTAGÅRDEN. | 1 |
| [`075_g055_p06.png`](pages/075_g055_p06.png) | g55 | 6/9 | Vilhelm | FÖRUTOM ÄTLIGA VÄXTER TYCKS DEN / OCKSÅ RYMMA LÄKEÖRTER. | 1 |
| [`076_g055_p07.png`](pages/076_g055_p07.png) | g55 | 7/9 | Severinus | SÅ ÄR DET. JAG SAMLAR DEM UNDER / HELA ÅRET. | 1 |
| [`077_g055_p08.png`](pages/077_g055_p08.png) | g55 | 8/9 | Severinus | SEDAN FÖRVARAR JAG DEM I KRUKOR I / LABORATORIET. | 1 |
| [`078_g055_p09.png`](pages/078_g055_p09.png) | g55 | 9/9 | Severinus | FÖLJ MIG, SÅ VISAR JAG ER / BYGGNADENS NEDRE VÅNING. | 1 |
| [`079_g056_p01.png`](pages/079_g056_p01.png) | g56 | 1/6 | Vilhelm | TALADE DU OFTA MED ADELMO? | 1 |
| [`080_g056_p02.png`](pages/080_g056_p02.png) | g56 | 2/6 | Severinus | NEJ. VI TALADES SÄLLAN VID. | 1 |
| [`081_g056_p03.png`](pages/081_g056_p03.png) | g56 | 3/6 | Severinus | HAN SATT STÄNDIGT OCH MÅLADE / MINIATYRER I SCRIPTORIET. | 1 |
| [`082_g056_p04.png`](pages/082_g056_p04.png) | g56 | 4/6 | Severinus | SJÄLV HÅLLER JAG MIG MEST I MITT / LABORATORIUM. | 1 |
| [`083_g056_p05.png`](pages/083_g056_p05.png) | g56 | 5/6 | Severinus | HAN VAR GOD VÄN MED BERENGAR, / BIBLIOTEKARIENS MEDHJÄLPARE. | 1 |
| [`084_g056_p06.png`](pages/084_g056_p06.png) | g56 | 6/6 | Severinus | DE VAR NOVISER TILLSAMMANS. | 1 |
| [`085_g057_p01.png`](pages/085_g057_p01.png) | g57 | 1/4 | Severinus | DETTA ÄR REFEKTORIET. | 1 |
| [`086_g057_p02.png`](pages/086_g057_p02.png) | g57 | 2/4 | Severinus | NI MÅSTE KOMMA HIT VID MÅLTIDERNA. /  | 1 |
| [`087_g057_p03.png`](pages/087_g057_p03.png) | g57 | 3/4 | Severinus | VILHELM, NI SKA SITTA TILL HÖGER OM / ABBOTEN. | 1 |
| [`088_g057_p04.png`](pages/088_g057_p04.png) | g57 | 4/4 | Severinus | DU, GOSSE, SITTER TILL VÄNSTER OM / MIG. | 1 |
| [`089_g058_p01.png`](pages/089_g058_p01.png) | g58 | 1/3 | Severinus | DETTA ÄR KLOSTRETS KÖK. | 1 |
| [`090_g058_p02.png`](pages/090_g058_p02.png) | g58 | 2/3 | Severinus | HÄR LAGAS MATEN ÅT ALLA MUNKARNA. | 1 |
| [`091_g058_p03.png`](pages/091_g058_p03.png) | g58 | 3/3 | Severinus | SCRIPTORIET, DÄR AVSKRIVARNA / ARBETAR, LIGGER PÅ ÖVRE VÅNINGEN. | 1 |
| [`092_g010_p01.png`](pages/092_g010_p01.png) | g10 | 1/1 | Adso | VI MÅSTE GÅ TILL REFEKTORIET, / MÄSTARE. | 1 |

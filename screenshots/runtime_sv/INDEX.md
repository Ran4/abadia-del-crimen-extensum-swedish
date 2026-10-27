# Swedish runtime tour: screenshot index

All files are native 320x208 game frames (the exact framebuffer, see docs/FORMAT.md §7.2), captured
from the built game in `game/` started with language `de` (= Swedish), Java 11.

**Jar note (Phase E round 2).** These runs used jar sha256 `e9a95e0c…` (the fixer run of round 1
used the round-1 rebuild). Phase E's final `game/` jar was `0ad2bbf0…`. It differs from `e9a95e0c…`
only in `abadia/k.class` (entry CRC diff over all 445 entries), and within it only in 17 `g` strings:
g52, g54, g61, g64, g75, g77, g85, g114, g118, g122, g125, g131, g143, g149, g150, g155 and g163.
None of them is on screen in this tour. The current wording of all of them is in the harness render
(`screenshots/strings/de/`), and g54 was re-captured live on `0ad2bbf0…` (`opening/INDEX.md`, run 4).

**Jar note (Phase F).** Phase F reworded g54, g61, g64, g122, g131, g149, g150 and g163 (all from the list
above) and rebuilt. The current jar `43846c9e…` differs from `0ad2bbf0…`/`e9a95e0c…` only in
`abadia/k.class` (entry CRC diff, Phase F final verification). None of these is on screen in this
tour. `work/build/manifest.json` holds the current jar's hash.

Where they came from:

- **Tour run** (`work/runs/tour-sv`, 2026-10-27 04:09-04:20):
  `PARCH_FULL=1 SHOT_DIR=work/phaseE/sv_tour RUN_DIR=work/runs/tour-sv tools/run_headless.sh game de tools/drivers/pristine_tour.sh`
  (all phases: intro, parchment, play, menu, walk, gameover). The raw output is in `work/phaseE/sv_tour/`,
  including `full/` 1296x871 window grabs, the 104-frame intro timeline and the 41 idle frames.
- **Fixer run, Phase E round 1** (`work/phaseE/fixer_r1/tour-sv`, 2026-10-27 05:36-05:43):
  `RUN_DIR=work/phaseE/fixer_r1/tour-sv PARCH_FULL=1 GAMEOVER=0 PHASES="intro parchment play menu walk" tools/run_headless.sh game de tools/drivers/pristine_tour.sh`,
  on the rebuilt game (only `abadia/k.class` changed; the parchments, letras and fuente are the same
  bytes). Used for the four parchment-writing frames `11_parchment_writing_*` (from the driver's
  `10_parchment_NNN`, one grab every 5 s) and for pages 3-7 (files 14-18). The driver now measures
  parchment ink only in rows ≥ 21, so these page captures no longer show the first page-turn tick
  at the top edge; below row 21 they are pixel-identical to the earlier captures (AE 0 on all 8 pages).
- **Save run** (`work/runs/save-sv`): `tools/drivers/interactive.sh` on a **copy** of the jar in
  `work/phaseE/save_game/`, so that `savedata.bin` would not be written into `game/`. Used only for
  files 40-41: a filled save slot, which the tour never creates. The raw frames are in `work/phaseE/sv_save/`.

- **Manual menu run** (`work/phaseF/menu_run`, 2026-10-27 10:21-10:23, Phase F, jar `43846c9e…`):
  `RUN_DIR=work/phaseF/menu_run SHOT_DIR=work/phaseF/menu_run/shots tools/run_headless.sh work/phaseF/menu_game de tools/drivers/manual_menu.sh`,
  on a copy of the jar in `work/phaseF/menu_game/`. Used only for file 49: the pause menu opened at the
  first frames of play, before anyone speaks, so no dialogue box lies under the menu scroll (the
  user manual's MENYN picture; every tour menu frame, 24-41, has g49 or g157 underneath). With the
  menu closed again the frame is pixel-identical to `20_play_start_hud.png` (AE 0). `evidence.log`
  records `INVISIBLE OK` before and after, `/dev/snd: 0 entries` and the sink-input on its null sink.

Every file was compared with the same moment in `screenshots/pristine_en/` and `screenshots/pristine_es/`.

| file | shows | time (s after java start) |
|---|---|---|
| 01_intro_loading.png | Loading screen: es title art + "LADDAR: var god vänta..." + "v1.3e" (AWT) | 3.3 |
| 02_intro_manuydani.png | "Manuel Pazos / och Daniel Celemín" | 11.4 |
| 03_intro_pacoyjuan.png | "efter spelet av / Paco Menéndez / och Juan Delcán" | 17.9 |
| 04_intro_novela.png | "efter romanen / "Rosens namn" / av Umberto Eco" | 24.3 |
| 05_intro_pelicula.png | "och / Jean-Jacques Annauds / film med samma namn" | 31.3 |
| 06_intro_monje.png | Monk at the desk (unchanged image; identical to en/es outside the animated moon window) | 37.9 |
| 07_intro_logo.png | Logo over the monk (es logo by decision; pixel-identical to es) | 42.6 |
| 08_intro_press_to_start.png | "Tryck för att starta", blink phase fully visible | 47.3 |
| 09_intro_press_to_start_blink_fading.png | Same, blink phase fading out | 48.5 |
| 10_intro_press_to_start_blink_off.png | Same, blink phase almost invisible | 58.5 |
| 11_fade_to_parchment.png | 1 s after Space: fade to black over the logo screen | 64.3 |
| 11_parchment_writing_1_vantar.png | Fixer run: page 1 being written, "och jag vänta" mid-word (ä) | ≈ 78 |
| 11_parchment_writing_2_da_ode.png | Fixer run: page 1 being written up to "och tys", with "då" and "öde" (å, ö) | ≈ 88 |
| 11_parchment_writing_3_ma_herren.png | Fixer run: page 2 being written, "Må Herren ge mig nå" mid-word (å; red capitals), with "gör", "förunderliga", "fruktansvärda" | ≈ 148 |
| 11_parchment_writing_4_holja.png | Fixer run: page 3 being written up to "att hölja i tys" (ö) | ≈ 168 |
| 12_parchment_page_1.png | Intro parchment p.1 "Nu lider mitt syndi- / ga liv ... lekamen ännu håller" | 109 |
| 13_parchment_page_2.png | p.2 "mig kvar, gör jag mig ... nåden att troget vittna" | 150 |
| 14_parchment_page_3.png | p.3 "om det som skedde i ... franciskan som stod i" | 196 |
| 15_parchment_page_4.png | p.4 "begrepp att ge sig ut ... vid hans sida var" | 241 |
| 16_parchment_page_5.png | p.5 "jag vittne till händel- ... till foten av berget" | 280 |
| 17_parchment_page_6.png | p.6 "där klostret reste ... som sedan hände..." | 317 |
| 18_parchment_page_7.png | p.7 credits "Efter spelet av ... Musik: David Cañadas" | 346 |
| 19_parchment_page_8.png | p.8 "Till minne / av / Paco Menéndez / och / Umberto Eco" | 364 |
| 20_play_start_hud.png | Start of play outside the gate: HUD "Dag", numeral I, hour "TERS" | 370 |
| 21_g49_box1_valkommen.png | Remigio g49 box 1: "VÄLKOMMEN TILL VÅRT KLOSTER, / BRODER." | 377 |
| 22_g49_box2_remigio.png | g49 box 2: "JAG ÄR REMIGIO, KÄLLARMÄSTAREN." | 382 |
| 23_g49_box3_folj_mig.png | g49 box 3: "JAG BER ER ATT FÖLJA MIG. ABBOTEN / VÄNTAR PÅ ER." | 389 |
| 24_menu_main.png | Pause menu, cursor on FORTSÄTT (all 10 rows with default values) | 392 |
| 25_menu_save_highlight.png | Cursor on SPARA SPEL | |
| 26_menu_save_slots_empty.png | Save slot list, 7 x "TOM" | |
| 27_menu_load_slots_empty.png | Load slot list, 7 x "TOM" (g157 now behind the menu) | |
| 28_menu_sound_voices_sfx.png | Cursor on "LJUD: RÖSTER, EFFEKTER" (widest row) | |
| 29_menu_sound_sfx.png | "LJUD: EFFEKTER" | |
| 30_menu_sound_off.png | "LJUD: AV" | |
| 31_menu_music_off.png | "MUSIK: AV" | |
| 32_menu_music_on.png | "MUSIK: PÅ" | |
| 33_menu_control_directional.png | "RIKTNINGSSTYRNING" (control row has no label, GLOSSARY §6.3) | |
| 34_menu_control_classic.png | "KLASSISK STYRNING" | |
| 35_menu_fullscreen_highlight.png | Cursor on "HELSKÄRM: AV" (not selected) | |
| 36_menu_extras_off.png | "VISA INDIKATORER: AV" | |
| 37_menu_extras_on.png | "VISA INDIKATORER: PÅ" | |
| 38_menu_restart_highlight.png | Cursor on STARTA OM (not selected) | |
| 39_menu_exit_highlight.png | Cursor on AVSLUTA (not selected) | |
| 40_menu_save_slots_filled.png | Save run: slot 1 after saving = "DAG 1  TERS", others "TOM" | |
| 41_menu_load_slots_filled.png | Save run: load slot list with the same filled slot | |
| 42_g157_william_remigio.png | Menu closed: g157 "DETTA KLOSTER ÄR UNDERBART VACKERT, / BRODER. OCH SÅ KLOKT ANLAGT." | |
| 43_g50_kom_broder.png | Walk: g50 "KOM, BRODER. ABBOTEN VÄNTAR PÅ ER." | |
| 44_walk_courtyard.png | Walk in the courtyard, no dialogue | |
| 45_g12_box1_abbot.png | Idle ending, abbot g12 box 1: "NI HAR INTE ÅTLYTT MINA / BEFALLNINGAR." | |
| 46_g12_box2_abbot.png | g12 box 2: "LÄMNA DETTA KLOSTER FÖR ALLTID." | |
| 47_end_screen.png | End screen "DU HAR LÖST / 0 PROCENT / AV GÅTAN / TRYCK PÅ MELLANSLAG" | 630 |
| 48_after_end_restart.png | After Space on the end screen: the game restarts at the gate | 636 |
| 49_menu_no_dialogue.png | Manual menu run: pause menu at the start of play, cursor on FORTSÄTT, no dialogue underneath | 66 |

## Comparison with pristine_en / pristine_es

- **Intro:** all 8 plateaus were found at the en/es times (within 0.5 s). With the moon window masked,
  the loading screen differs from es only in the bottom line (172x13 at +82+181). manuydani differs
  only in the conjunction (33x22 at +51+143). monje is identical to en and es. logo and press-to-start,
  with the pulsa band (y 160-190) and the moon masked, are pixel-identical to es (AE 0).
- **Parchment:** 8 pages, as in en and es. Writing took 292 s (en 279 s, es 299 s). Every page ends
  on the expected word, with no lost lines between pages. å, ä, ö, é, í and ñ are drawn correctly,
  and capitals are red as in the original.
- **Play:** frame 20 differs from en only in the HUD day word ("g") and the hour strip (x 30..52,
  y 180..205). The g49, g157, g50 and g12 boxes break and time like en and es.
- **Menu and end screen:** the same layout as en and es. The widest row ("LJUD: RÖSTER, EFFEKTER")
  stays inside the highlight bar with about 6 px to spare.
- **Logs:** `game.log` of both runs holds only the two documented Java 11 startup traces (CCE + NPE in
  `abadia.c.b.a`). There are no `Caracter:` lines.
- **Invisibility and silence:** `evidence.log` of both runs records `INVISIBLE OK` (before and after),
  `game sees /dev/snd: 0 entries`, and the java sink-input on the private null sink. Audio level on
  the null-sink monitor: peak 15683. The fixer run records the same (`INVISIBLE OK` before and after,
  `/dev/snd: 0 entries`, the sink-input on its null sink, no `Caracter:` lines, only the two startup
  traces); its audio level (`samples=263366 peak=15649 rms=2725.0`) is computed with `od` and `awk`,
  no longer with Python.

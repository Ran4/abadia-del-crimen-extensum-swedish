# Runtime regression: en, es and pl on the patched jar

**Verdict: no regression.** The patched `game/TheAbbeyOfCrimeExtensum.jar` (sha256 `e9a95e0c…62ef4`)
draws en, es and pl exactly like the pristine jar (`1bc6b3fc…1a36f0`) at every deterministic state
the tour reaches. That covers the 8 intro screens (moon masked), all 8 completed intro-parchment
pages and the finished parchment, the HUD and the hour name scrolling in (all 8 `20_game_start`
frames identical), every dialogue-box state the tour shows (Remigio's three welcome boxes, William's
"THIS ABBEY IS BEAUTIFUL…", Remigio's "COME, BROTHER…", the abbot's expulsion, and no box), all 17
pause-menu and save/load-slot panels, the end screen and the restart after it. Every
pixel that differs belongs to a moving thing or comes from timing jitter. All six game logs are
clean, all six runs stayed invisible, and all audio went to the private null sinks.

**Jar note (Phase E round 2).** "The patched jar" here is `e9a95e0c…`. The current `game/` jar,
`0ad2bbf0…`, differs from it only in `abadia/k.class` (entry CRC diff over all 445 entries), and
within it only in 17 Swedish `g` strings. `k` is the `de` slot (FORMAT §1.1), so en, es and pl do not
read it. `uv run tools/regress.py` on the current jar is pixel-identical in es, en, it, fr and pl
(3711 frames; `work/regress_final.log`).

Date 2026-10-27. Six live runs through `tools/run_headless.sh` + `tools/drivers/pristine_tour.sh`,
then a pairwise comparison with `work/phaseE/compare_runtime.py`.

## Images in this folder

| file | what it shows |
|---|---|
| `en_sheet.png`, `es_sheet.png`, `pl_sheet.png` | pristine \| patched \| diff for 7 deterministic states per language: a credits screen, an intro-parchment page, the HUD, a message page, the pause menu, the save slots, the end screen |
| `en_moving_things.png`, `es_moving_things.png`, `pl_moving_things.png` | the largest difference of each moving-thing type, showing what was masked and why it is not a regression |

Diff column: red = a differing pixel, blue tint = a masked moving region, grey = equal.

## Setup

* Pristine game dir: `work/phaseE/pristine_game/`, copied from `original/`: the jar, the 5 `.sh` and
  5 `.bat` launchers, and the 5 manuals. sha256 was checked against `original/`. The `.rar` was not
  copied. `original/` was unchanged afterwards (file list, sizes, mtimes and sha256 compared before
  and after), and so was `game/` (sha256 of every file).
* Same settings for both runs of a language: `PARCH_FULL=1 GAMEOVER=1 PHASES="intro parchment play
  menu walk gameover" INTRO_SECS=52 INTRO_IV=0.5`, with the default `JAVA_MEM`, `XVFB_SCREEN` and Java 11.
  The patched and pristine runs of a language were started in the same second (so their timing is
  close), and the languages ran one after another: en 04:11, es 04:22, pl 04:33. Each run took
  10.6 to 10.9 min.
* Screenshots: `work/phaseE/regress/<lang>/{patched,pristine}/` (native 320x208 frames; `full/` holds
  the raw window grabs of the same frames and was not compared separately). Run dirs:
  `work/phaseE/runs/<lang>-{patched,pristine}/` (`game.log`, `evidence.log`, `driver.log`).
* Static context: the two jars differ in exactly 16 entries: `abadia/{E,j,k,w}.class`,
  `res/fuente.png`, `res/letras` and 10 `res/de/**` files (CRC listing). Every en/es/pl resource is
  byte-identical, including `res/{en,es,pl}/intro/pulsa.png`, which the masks use.

## Method (what was compared and how moving things were handled)

`uv run work/phaseE/compare_runtime.py --langs en es pl --sheets screenshots/runtime_regress` pairs
each same-named frame of the two runs (376 pairs) and classifies every pair that is not
pixel-identical:

| frames | rule |
|---|---|
| intro plateaus `01..08` | moon/fog clip 250,0 70x100 masked (`08` also masks the blinking "press" text, alpha>0 of `pulsa.png`). The plateau sets from the 104 timeline frames are compared as well. |
| `08b`, `09`, `12` | `08b` uses the same masks; `09` is mid-fade, reported as transient |
| `11_parchment_page_NN`, `11_parchment_done` | Rows y ≥ 21 must be identical. A difference in the top roll (y < 21) means one run captured the first tick of the page-turn animation; this was checked by eye for all 16 page cases (en 5, es 5, pl 6). |
| `10_parchment_NNN` (one grab every 5 s while writing) | One frame must equal the other plus later ink. Ink is any pixel that differs from `pergamino.png` drawn at (65,9) on black. The frame with less ink must show bare parchment where they differ and must have no ink later in writing order (rest of the line beyond the glyph being written, any lower line). Page-turn frames caught at different phases are reported as transient. |
| pause menu `30..39` | Only the opaque pixels of `pergamino2.png` at (50,20) are compared. The dialogue box below the panel is compared by state. |
| play `20..23`, `39_menu_closed`, `40_*`, `60` | The HUD (y 176..207) must be identical. The dialogue box (alpha 137, so the scene shows through) is compared only by its opaque font layer, with the face excluded because the face animates while speaking. If the state differs at the same moment, it must occur in the other run at another frame (pools are built from every play, menu and `50_idle` frame). |
| `59_game_over` | whole frame |

**Negative control:** six single-pixel edits were made to copies of the en patched frames: a
credits screen, a parchment page body, the HUD, the dialogue font layer, the save-slot panel and the
end screen. All six were flagged (`DIFF` / `UNMATCHED`), so the masks do not hide real changes.

## Results

| | en | es | pl |
|---|---|---|---|
| pairs compared | 122 | 126 | 128 |
| pixel-identical | 22 | 48 | 19 |
| needs inspection (`DIFF` / `UNMATCHED`) | **0** | **0** | **0** |
| intro plateaus found (patched / pristine), sets equal | 8 / 8, yes | 8 / 8, yes | 8 / 8, yes |
| intro screens 01..08 | identical after the moon (and press) mask | same | same |
| parchment pages 1..8 + done | 3 identical, 5 identical below the top roll; done identical | 3 + 5; done identical | 2 + 6; done identical |
| parchment timeline frames | all "the other + later ink", or a page turn | same | same |
| HUD `20_game_start_000..007` | 8/8 identical | 8/8 | 8/8 |
| HUD states over all play frames | 17 = 17 | 17 = 17 | 17 = 17 |
| dialogue states over all play frames | 7 = 7 | 7 = 7 | 7 = 7 |
| menu + slot panels (17 frames), panel pixels differing | 0 | 0 | 0 |
| end screen `59` / restart `60` | identical / identical | identical / identical | identical / identical |

## Every difference, explained

All of them are listed per checkpoint in the appendix below; each one has a side-by-side
image in `work/phaseE/regress/<lang>/diff/<name>.png`.

1. **Moon fog** (r.a clip 250,0 70x100) in intro plateaus: en 7, es 1, pl 7. All differing pixels lie
   inside x 260..308, y 12..91. Example: `work/phaseE/regress/pl/diff/03_credits_pacoyjuan.png`.
2. **"Press to start" blink phase + fog** in `08b_press_to_start_now` (en 4388 px, es 2531, pl 3435), all
   inside the pulsa alpha mask and the moon clip: `work/phaseE/regress/en/diff/08b_press_to_start_now.png`.
3. **Fade phase** in `09_fade_to_parchment` (en 3787, es 38382, pl 3085 px).
4. **Page-turn tick in the parchment top roll**, captured on a page's peak-ink frame in one run only:
   en pages 3-7, es 2/3/4/6/7, pl 1/2/3/4/6/7 (150..992 px, all at y 10..20). The text below is
   identical. Examples: `work/phaseE/regress/en/diff/11_parchment_page_04.png` and
   `work/phaseE/regress/pl/diff/11_parchment_page_02.png`.
5. **Writing progress** in `10_parchment_NNN`: the two runs are 1..23 ink pixels apart at the pen
   (en 53, es 55, pl 58 frames). That includes pixels drawn twice, which get darker (en 6, pl 1), and
   three cases where the pen was at a first-line glyph top above y = 21 (es 051, pl 028, and pl 009,
   which is 1 px at (76,19), the first pixel of a new page). **Page-turn animation at a
   different phase** in en 009/041 and pl 018/027.
6. **Scene timing** in play frames: William, Adso and Remigio are a few pixels apart, plus the
   speaker's mouth animation (about 20 px at x 17..24, y 164..168). The dialogue font layer and the
   HUD are identical in all of these. Example: `work/phaseE/regress/en/diff/40_walk_2.png`.
7. **Dialogue state at the moment of a keypress:**
   * en `30/31/32_menu_*`: when Esc was pressed, the patched run already showed William's "THIS ABBEY
     IS BEAUTIFUL, BROTHER. AND IT IS PERFECTLY ORIENTED." under the panel, and the pristine run showed
     no box yet. The pristine run shows the same box from `33_menu_load_slots` on. The panel is
     identical. See `work/phaseE/regress/en/diff/30_menu_main.png`.
   * pl `22_welcome_003`: the patched run was already on Remigio's second sentence "JESTEM REMIGIUSZ,
     KLUCZNIK.", which the pristine run shows in its next grab (`22_welcome_004`).

Nothing differs in the HUD, the menu text, the slot labels (EMPTY / VACÍO / PUSTE), the end-screen
text, the message text or the parchment text in any of the three languages. That includes the Polish
letters drawn through the shared `fuente.png` / `j.class` path (menu "DŹWIĘK: GŁOSY,EFEKTY",
"POKAŻ", "WYJDŹ"; message "KLUCZNIK"; end screen "UDAŁO CI SIĘ ROZWIĄZAĆ … ŚLEDZTWA") and through
the shared `letras` (parchment "Zbliżając", "świadectwo", "ręki"), and the Spanish accented
letters ("VACÍO", "MÚSICA", "ABADÍA").

## Logs, invisibility, audio (`uv run work/phaseE/check_runs.py`, output in `work/phaseE/runs/check_runs.json`)

| run | game.log | `Caracter:` | :0 check | display | /dev/snd | sink-inputs | audio level on the null-sink monitor | exit |
|---|---|---|---|---|---|---|---|---|
| en patched | exactly the 2 Java 11 traces (12 lines) | 0 | INVISIBLE OK ×2 | :2 | 0 entries | all on `abbey_mute_2143284` | peak 15553 | driver 0, rc 0 |
| en pristine | same | 0 | ×2 | :3 | 0 | all on `abbey_mute_2143287` | peak 13139 | 0 / 0 |
| es patched | same | 0 | ×2 | :1 | 0 | all on `abbey_mute_2746880` | peak 14189 | 0 / 0 |
| es pristine | same | 0 | ×2 | :2 | 0 | all on `abbey_mute_2746888` | peak 15936 | 0 / 0 |
| pl patched | same | 0 | ×2 | :1 | 0 | all on `abbey_mute_3213140` | peak 14875 | 0 / 0 |
| pl pristine | same | 0 | ×2 | :2 | 0 | all on `abbey_mute_3213144` | peak 15053 | 0 / 0 |

* game.log matches FORMAT §7.7 line for line: the ClassCastException and NullPointerException from
  `abadia.c.b.a`, and nothing else.
* Invisibility: each game ran on its own Xvfb (`-displayfd`, never :0), and `/proc/<pid>/environ` had
  the same DISPLAY. `DISPLAY=:0 xdotool search --name 'Abad|Abbey|...'` found no windows before and
  after each driver. Window titles were the same in both runs: en and pl "The Abbey of Crime
  Extensum", es "La Abadía del Crimen Extensum".
* Silence: bwrap hid `/dev/snd` (0 entries). Every java sink-input was on its run's null sink
  (`target.object` = that sink). There was no AUDIO LEAK, and the sound recorded during play exists
  only on the null-sink monitor.
* Cleanup: every game, Xvfb and bwrap process exited (checked by PID). The null-sink modules were
  unloaded, there was no SIGKILL, and `javatmp/` was removed with no leftovers. Nothing outside
  those PIDs was touched. Other tools' Xvfb processes and their `abbey_mute_3781890` sink were left
  alone.
* Tour milestones, the same in every run: 8/8 intro plateaus, 8 parchment pages (en 279 s, es 299 s,
  pl 309 s), game-over screen reached (patched and pristine within 0.03 s of each other), `tour done`.

## Files

* `work/phaseE/compare_runtime.py`: the comparison (masks, state pools, side-by-sides, sheets).
  Its outputs are `work/phaseE/regress/REPORT.md`, `work/phaseE/regress/report.json` and
  `work/phaseE/regress/<lang>/{report.json,diff/}`.
* `work/phaseE/check_runs.py`: log, invisibility and audio checks; writes `work/phaseE/runs/check_runs.json`.
* `work/phaseE/pristine_game/`: the pristine game directory.

## Appendix: every non-identical pair, by verdict

#### en (122 pairs, diff images in `work/phaseE/regress/en/diff/<name>.png`)

| verdict | n | checkpoints (diff px) |
|---|---|---|
| IDENTICAL | 22 | 01_loading, 10_parchment_005, 10_parchment_056, 11_parchment_done, 11_parchment_page_01, 11_parchment_page_02, 11_parchment_page_08, 12_after_parchment_fade, 20_game_start_000, 20_game_start_001, 20_game_start_002, 20_game_start_003, 20_game_start_004, 20_game_start_005, 20_game_start_006, 20_game_start_007, 22_welcome_005, 22_welcome_006, 22_welcome_011, 23_after_space, 59_game_over, 60_after_game_over |
| SAME_AFTER_MASK | 8 | 02_credits_manuydani (1599), 03_credits_pacoyjuan (1338), 04_credits_novela (1178), 05_credits_pelicula (2234), 06_monje (1527), 07_logo (2099), 08_press_to_start (1474), 08b_press_to_start_now (4388) |
| TRANSIENT (fade phase) | 1 | 09_fade_to_parchment (3787) |
| PREFIX (one frame = the other + ink written later) | 47 | 10_parchment_000 (4), 10_parchment_001 (2), 10_parchment_002 (5), 10_parchment_003 (2), 10_parchment_004 (1), 10_parchment_006 (7), 10_parchment_007 (9), 10_parchment_010 (12), 10_parchment_011 (2), 10_parchment_012 (14), 10_parchment_013 (5), 10_parchment_014 (7), 10_parchment_015 (11), 10_parchment_016 (17), 10_parchment_017 (13), 10_parchment_018 (17), 10_parchment_019 (16), 10_parchment_020 (8), 10_parchment_021 (13), 10_parchment_023 (15), 10_parchment_024 (14), 10_parchment_025 (11), 10_parchment_026 (10), 10_parchment_027 (15), 10_parchment_028 (16), 10_parchment_029 (18), 10_parchment_031 (15), 10_parchment_032 (9), 10_parchment_034 (10), 10_parchment_035 (10), 10_parchment_036 (3), 10_parchment_037 (15), 10_parchment_038 (8), 10_parchment_039 (2), 10_parchment_042 (2), 10_parchment_044 (10), 10_parchment_045 (12), 10_parchment_046 (6), 10_parchment_047 (13), 10_parchment_048 (12), 10_parchment_049 (3), 10_parchment_050 (3), 10_parchment_051 (15), 10_parchment_052 (11), 10_parchment_053 (16), 10_parchment_054 (12), 10_parchment_055 (6) |
| PROGRESS (inside the glyph being written; re-hit pixels darken) | 6 | 10_parchment_008 (6), 10_parchment_022 (19), 10_parchment_030 (12), 10_parchment_033 (6), 10_parchment_040 (8), 10_parchment_043 (13) |
| TRANSIENT (page turn / mixed) | 2 | 10_parchment_009 (7674), 10_parchment_041 (16917) |
| BODY IDENTICAL; top band y<21 differs | 5 | 11_parchment_page_03 (986), 11_parchment_page_04 (802), 11_parchment_page_05 (988), 11_parchment_page_06 (651), 11_parchment_page_07 (804) |
| TEXT+HUD IDENTICAL (scene differs: timing) | 14 | 21_walk_in (109), 22_welcome_000 (865), 22_welcome_001 (20), 22_welcome_002 (5), 22_welcome_003 (4), 22_welcome_004 (20), 22_welcome_007 (37), 22_welcome_008 (218), 22_welcome_009 (551), 22_welcome_010 (558), 39_menu_closed (181), 40_walk_1 (266), 40_walk_2 (1616), 40_walk_3 (566) |
| PANEL IDENTICAL (dialogue state below the panel differs: timing) | 3 | 30_menu_main (7714), 31_menu_save_highlight (7714), 32_menu_save_slots (7714) |
| PANEL IDENTICAL (scene behind differs: timing) | 14 | 33_menu_load_slots (315), 34_menu_sound_0 (21), 34_menu_sound_1 (21), 34_menu_sound_2 (21), 34_menu_sound_3 (21), 35_menu_music_off (21), 35_menu_music_on (21), 36_menu_control_classic (21), 36_menu_control_directional (21), 37_menu_fullscreen_highlight (21), 38_menu_extras_back (21), 38_menu_extras_toggled (21), 39_menu_exit_highlight (21), 39_menu_restart_highlight (21) |

#### es (126 pairs, diff images in `work/phaseE/regress/es/diff/<name>.png`)

| verdict | n | checkpoints (diff px) |
|---|---|---|
| IDENTICAL | 48 | 01_loading, 02_credits_manuydani, 03_credits_pacoyjuan, 04_credits_novela, 06_monje, 07_logo, 08_press_to_start, 10_parchment_002, 10_parchment_003, 10_parchment_004, 10_parchment_034, 10_parchment_057, 10_parchment_060, 11_parchment_done, 11_parchment_page_01, 11_parchment_page_05, 11_parchment_page_08, 12_after_parchment_fade, 20_game_start_000, 20_game_start_001, 20_game_start_002, 20_game_start_003, 20_game_start_004, 20_game_start_005, 20_game_start_006, 20_game_start_007, 21_walk_in, 22_welcome_001, 22_welcome_003, 22_welcome_006, 22_welcome_007, 33_menu_load_slots, 34_menu_sound_0, 34_menu_sound_1, 34_menu_sound_2, 34_menu_sound_3, 35_menu_music_off, 35_menu_music_on, 36_menu_control_classic, 36_menu_control_directional, 37_menu_fullscreen_highlight, 38_menu_extras_back, 38_menu_extras_toggled, 39_menu_exit_highlight, 39_menu_restart_highlight, 40_walk_2, 59_game_over, 60_after_game_over |
| SAME_AFTER_MASK | 2 | 05_credits_pelicula (1401), 08b_press_to_start_now (2531) |
| TRANSIENT (fade phase) | 1 | 09_fade_to_parchment (38382) |
| PREFIX (one frame = the other + ink written later) | 54 | 10_parchment_000 (2), 10_parchment_001 (2), 10_parchment_005 (1), 10_parchment_006 (1), 10_parchment_007 (10), 10_parchment_008 (8), 10_parchment_009 (8), 10_parchment_010 (15), 10_parchment_011 (10), 10_parchment_012 (4), 10_parchment_013 (11), 10_parchment_014 (13), 10_parchment_015 (19), 10_parchment_016 (15), 10_parchment_017 (14), 10_parchment_018 (16), 10_parchment_019 (13), 10_parchment_020 (2), 10_parchment_021 (9), 10_parchment_022 (13), 10_parchment_023 (13), 10_parchment_024 (10), 10_parchment_025 (9), 10_parchment_026 (4), 10_parchment_027 (13), 10_parchment_028 (11), 10_parchment_029 (13), 10_parchment_030 (12), 10_parchment_031 (17), 10_parchment_032 (3), 10_parchment_033 (5), 10_parchment_035 (7), 10_parchment_036 (11), 10_parchment_037 (4), 10_parchment_038 (1), 10_parchment_039 (1), 10_parchment_040 (1), 10_parchment_041 (5), 10_parchment_042 (4), 10_parchment_043 (7), 10_parchment_044 (7), 10_parchment_045 (10), 10_parchment_046 (9), 10_parchment_047 (12), 10_parchment_048 (10), 10_parchment_049 (9), 10_parchment_050 (12), 10_parchment_052 (9), 10_parchment_053 (12), 10_parchment_054 (18), 10_parchment_055 (12), 10_parchment_056 (7), 10_parchment_058 (6), 10_parchment_059 (6) |
| PREFIX (one frame = the other + ink written later); top band y<21 differs | 1 | 10_parchment_051 (7) |
| BODY IDENTICAL; top band y<21 differs | 5 | 11_parchment_page_02 (989), 11_parchment_page_03 (801), 11_parchment_page_04 (651), 11_parchment_page_06 (804), 11_parchment_page_07 (919) |
| TEXT+HUD IDENTICAL (scene differs: timing) | 12 | 22_welcome_000 (5), 22_welcome_002 (4), 22_welcome_004 (23), 22_welcome_005 (20), 22_welcome_008 (4), 22_welcome_009 (20), 22_welcome_010 (527), 22_welcome_011 (301), 23_after_space (3), 39_menu_closed (3), 40_walk_1 (5), 40_walk_3 (386) |
| PANEL IDENTICAL (scene behind differs: timing) | 3 | 30_menu_main (9), 31_menu_save_highlight (7), 32_menu_save_slots (7) |

#### pl (128 pairs, diff images in `work/phaseE/regress/pl/diff/<name>.png`)

| verdict | n | checkpoints (diff px) |
|---|---|---|
| IDENTICAL | 19 | 01_loading, 10_parchment_061, 10_parchment_062, 11_parchment_done, 11_parchment_page_05, 11_parchment_page_08, 12_after_parchment_fade, 20_game_start_000, 20_game_start_001, 20_game_start_002, 20_game_start_003, 20_game_start_004, 20_game_start_005, 20_game_start_006, 20_game_start_007, 22_welcome_002, 22_welcome_006, 59_game_over, 60_after_game_over |
| SAME_AFTER_MASK | 8 | 02_credits_manuydani (1607), 03_credits_pacoyjuan (2339), 04_credits_novela (2499), 05_credits_pelicula (1416), 06_monje (1534), 07_logo (1388), 08_press_to_start (1477), 08b_press_to_start_now (3435) |
| TRANSIENT (fade phase) | 1 | 09_fade_to_parchment (3085) |
| PREFIX (one frame = the other + ink written later) | 56 | 10_parchment_000 (2), 10_parchment_001 (1), 10_parchment_002 (8), 10_parchment_003 (1), 10_parchment_004 (7), 10_parchment_005 (3), 10_parchment_006 (7), 10_parchment_007 (5), 10_parchment_008 (2), 10_parchment_010 (3), 10_parchment_011 (2), 10_parchment_012 (1), 10_parchment_013 (3), 10_parchment_014 (4), 10_parchment_015 (2), 10_parchment_016 (1), 10_parchment_017 (2), 10_parchment_019 (8), 10_parchment_020 (11), 10_parchment_021 (10), 10_parchment_022 (9), 10_parchment_023 (7), 10_parchment_024 (14), 10_parchment_025 (3), 10_parchment_026 (12), 10_parchment_029 (10), 10_parchment_030 (13), 10_parchment_031 (7), 10_parchment_032 (13), 10_parchment_033 (13), 10_parchment_034 (9), 10_parchment_035 (6), 10_parchment_036 (4), 10_parchment_037 (3), 10_parchment_038 (3), 10_parchment_039 (10), 10_parchment_040 (7), 10_parchment_041 (5), 10_parchment_042 (4), 10_parchment_043 (15), 10_parchment_044 (1), 10_parchment_046 (13), 10_parchment_047 (18), 10_parchment_048 (12), 10_parchment_049 (12), 10_parchment_050 (12), 10_parchment_051 (13), 10_parchment_052 (19), 10_parchment_053 (13), 10_parchment_054 (13), 10_parchment_055 (13), 10_parchment_056 (17), 10_parchment_057 (14), 10_parchment_058 (14), 10_parchment_059 (16), 10_parchment_060 (23) |
| BODY IDENTICAL; top band y<21 differs | 7 | 10_parchment_009 (1), 11_parchment_page_01 (324), 11_parchment_page_02 (992), 11_parchment_page_03 (914), 11_parchment_page_04 (324), 11_parchment_page_06 (800), 11_parchment_page_07 (150) |
| TRANSIENT (page turn / mixed) | 2 | 10_parchment_018 (5578), 10_parchment_027 (10321) |
| PREFIX (one frame = the other + ink written later); top band y<21 differs | 1 | 10_parchment_028 (8) |
| PROGRESS (inside the glyph being written; re-hit pixels darken) | 1 | 10_parchment_045 (3) |
| TEXT+HUD IDENTICAL (scene differs: timing) | 15 | 21_walk_in (109), 22_welcome_000 (1266), 22_welcome_001 (608), 22_welcome_004 (5), 22_welcome_005 (3), 22_welcome_007 (58), 22_welcome_008 (352), 22_welcome_009 (473), 22_welcome_010 (580), 22_welcome_011 (849), 23_after_space (270), 39_menu_closed (255), 40_walk_1 (1477), 40_walk_2 (1883), 40_walk_3 (1274) |
| STATE MATCHED (same dialogue/HUD state at another frame of the pristine run) | 1 | 22_welcome_003 (1030) |
| PANEL IDENTICAL (scene behind differs: timing) | 17 | 30_menu_main (145), 31_menu_save_highlight (143), 32_menu_save_slots (142), 33_menu_load_slots (377), 34_menu_sound_0 (21), 34_menu_sound_1 (21), 34_menu_sound_2 (21), 34_menu_sound_3 (21), 35_menu_music_off (21), 35_menu_music_on (21), 36_menu_control_classic (21), 36_menu_control_directional (21), 37_menu_fullscreen_highlight (21), 38_menu_extras_back (21), 38_menu_extras_toggled (21), 39_menu_exit_highlight (21), 39_menu_restart_highlight (21) |


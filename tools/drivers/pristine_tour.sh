#!/usr/bin/env bash
# pristine_tour.sh - reusable tour through the game for screenshots (any language/build).
#
#   SHOT_DIR=screenshots/pristine_en tools/run_headless.sh <gamedir> en tools/drivers/pristine_tour.sh
#
# Checkpoints written to $SHOT_DIR (native 320x208 PNGs; full/ holds raw 1296x871 window grabs):
#   00_intro_timeline/t_NNN.png   intro, no input, one frame every INTRO_IV s for INTRO_SECS s
#   01_loading .. 08_press_to_start   the 8 intro plateaus picked from that timeline
#   09_fade_to_parchment, 10_parchment_NN (every PARCH_IV s for PARCH_SECS s; PARCH_FULL=1
#   keeps going until the parchment is finished = static for 3 grabs, then 11_parchment_done)
#   20_game_start_NN (HUD, hour name scrolling in), 21_walk_in, 22_welcome_NN (Remigio's
#   welcome dialogue), 23_after_space, 30-39 pause menu pages, 40_walk_N,
#   50_idle/NNN until the game-over screen (59_game_over) if GAMEOVER=1.
#
# Env knobs: PHASES (default "intro parchment play menu walk gameover"; without "intro" the
# driver just waits INTRO_SECS for "Press to start"), PARCH_FULL=1 (whole parchment with
# per-page captures 11_parchment_page_NN, ~5 min), PARCH_SECS/PARCH_IV (partial parchment),
# INTRO_SECS/INTRO_IV, GAMEOVER/GAMEOVER_CAP. Only pristine-game assumptions used for
# navigation: classic control, "hold Up 3 s" from the start walks into the courtyard.
#
# Timings (VERIFIED on this machine, Java 11, Xvfb, see work/phaseA/runtime.md): window maps
# ~0.6-0.7 s after java starts; intro plateaus at ~3-5 s (loading), ~10-13 s (Manuel Pazos
# and Daniel Celemin), ~17-20 s, ~24-27 s, ~30-34 s (credits), ~38 s monje, ~42 s logo,
# ~45 s+ "Press to start" blinking forever.
{
set -euo pipefail
source "$HEADLESS_LIB"

INTRO_SECS="${INTRO_SECS:-52}"
INTRO_IV="${INTRO_IV:-0.5}"
PARCH_SECS="${PARCH_SECS:-36}"
PARCH_IV="${PARCH_IV:-3}"           # PARCH_FULL=1 uses min(PARCH_IV, 1.5)
PARCH_FULL="${PARCH_FULL:-0}"
GAMEOVER="${GAMEOVER:-1}"
PHASES="${PHASES:-intro parchment play menu walk gameover}"
GAMEOVER_CAP="${GAMEOVER_CAP:-720}"
MOON_MASK="250,0 319,99"   # r.a(): moon + drifting fog are redrawn every frame in this clip

nat() { echo "$SHOT_DIR/$1.png"; }

has_phase() { [[ " $PHASES " == *" $1 "* ]]; }

# ---------------------------------------------------------------- 1. intro, no input ------
if has_phase intro; then
dlog "phase 1: intro timeline ${INTRO_SECS}s every ${INTRO_IV}s"
mkdir -p "$SHOT_DIR/00_intro_timeline"
n=$(LC_ALL=C awk -v d="$INTRO_SECS" -v i="$INTRO_IV" 'BEGIN{printf "%d", d/i}')
SHOT_FULL=0 burst 00_intro_timeline/t "$n" "$INTRO_IV"

# Plateau = >=2 consecutive identical timeline frames (moon clip masked), not black;
# keep the first occurrence of each distinct plateau image.
names=(01_loading 02_credits_manuydani 03_credits_pacoyjuan 04_credits_novela
       05_credits_pelicula 06_monje 07_logo 08_press_to_start)
declare -A seen=()
plateaus=()
prev="" run=0
for f in "$SHOT_DIR"/00_intro_timeline/t_*.png; do
  h=$(convert "$f" -fill black -draw "rectangle $MOON_MASK" rgb:- | md5sum | cut -c1-32)
  if [[ $h == "$prev" ]]; then run=$((run + 1)); else run=0; fi
  prev=$h
  if (( run == 1 )) && [[ -z ${seen[$h]:-} ]]; then
    mean=$(convert "$f" -colorspace gray -format '%[fx:mean]' info:)
    if LC_ALL=C awk -v m="$mean" 'BEGIN{exit !(m > 0.01)}'; then
      seen[$h]=1
      plateaus+=("$f")
    fi
  fi
done
dlog "intro plateaus found: ${#plateaus[@]} (expected 8)"
for i in "${!plateaus[@]}"; do
  if (( ${#plateaus[@]} == 8 )); then nm=${names[$i]}; else nm=$(printf '0%d_plateau_%02d' $(( i < 8 ? i + 1 : 8 )) "$i"); fi
  cp "${plateaus[$i]}" "$(nat "$nm")"
  dlog "plateau $nm <- $(basename "${plateaus[$i]}")"
done
else
  # no input during the intro: "Press to start" (l=7) is reached at ~45 s and blinks forever,
  # so waiting is the robust way there (Space taps can land on the loading screen, where
  # they are ignored, and an extra tap after the parchment fade would skip the parchment).
  dlog "intro phase skipped: waiting ${INTRO_SECS}s for 'Press to start'"
  wait_s "$INTRO_SECS"
fi

# ---------------------------------------------------- 2. press key -> intro parchment -----
# Parchment page capture: poll the native frame as fast as possible (~6-8 grabs/s); "ink" =
# share of dark pixels inside the parchment text area (168x176+76+16; pergamino.png is
# 190x190 centred at 65,9). Ink only grows while a page is written and collapses during
# the page turn, so the frame with the peak ink of each page is that page, complete to
# within one poll (~0.15 s, i.e. at most the last pixels of one glyph).
parchment_full() {
  local cur="$RUN_DIR/.parch_cur.png" peak="$RUN_DIR/.parch_peak.png"
  local ink peak_ink=0 pg=0 h prevh="" t_change t_start now k=0 next_tl armed=0
  t_start=$(_now_ms); t_change=$t_start; next_tl=$t_start
  while :; do
    grab_native "$cur"
    now=$(_now_ms)
    ink=$(convert "$cur" -crop 168x176+76+16 +repage -colorspace gray -threshold 35% -negate -format '%[fx:mean]' info:)
    h=$(png_hash "$cur")
    if [[ $h != "$prevh" ]]; then t_change=$now; prevh=$h; fi
    # armed = a page is being written; a page turn disarms until the ink is ~0 again
    if (( armed )); then
      if LC_ALL=C awk -v a="$ink" -v p="$peak_ink" 'BEGIN{exit !(p > 0.02 && a < p*0.5)}'; then
        pg=$((pg + 1)); cp "$peak" "$(nat "$(printf '11_parchment_page_%02d' "$pg")")"
        dlog "parchment page $pg complete (peak ink $peak_ink)"
        armed=0; peak_ink=0
      elif LC_ALL=C awk -v a="$ink" -v p="$peak_ink" 'BEGIN{exit !(a >= p)}'; then
        peak_ink=$ink; cp "$cur" "$peak"
      fi
    elif LC_ALL=C awk -v a="$ink" 'BEGIN{exit !(a < 0.01)}'; then
      armed=1; peak_ink=$ink; cp "$cur" "$peak"
    fi
    if (( now >= next_tl )); then
      cp "$cur" "$(nat "$(printf '10_parchment_%03d' "$k")")"; k=$((k + 1))
      next_tl=$(( next_tl + 5000 ))
    fi
    if (( now - t_change > 5000 )); then break; fi
    if (( now - t_start > 900000 )); then dlog "parchment cap reached"; break; fi
    game_alive || return 1
  done
  if (( armed )); then pg=$((pg + 1)); cp "$peak" "$(nat "$(printf '11_parchment_page_%02d' "$pg")")"; fi
  dlog "parchment finished: $pg pages, $(( (t_change - t_start) / 1000 ))s from first grab to last change"
  rm -f "$cur" "$peak"
}

if has_phase parchment; then
dlog "phase 2: parchment"
shot 08b_press_to_start_now
tap space 0.2                     # r.a(): l==7 -> m=5, fade to black (+4 alpha/frame)
wait_s 1.0
shot 09_fade_to_parchment
wait_s 1.5
if [[ $PARCH_FULL == 1 ]]; then
  parchment_full
  shot 11_parchment_done
  tap space 0.2                   # E.a: an && C.e -> b.a(0,1) fade to black, then play
  wait_s 1.0; shot 12_after_parchment_fade
  wait_s 5
else
  n=$(LC_ALL=C awk -v d="$PARCH_SECS" -v i="$PARCH_IV" 'BEGIN{printf "%d", d/i}')
  burst 10_parchment "$n" "$PARCH_IV"
  tap space 0.2                   # y.a() state 2: C.e && b != d -> skip the parchment
  wait_s 1.5
fi
fi

# ------------------------------------------------------------------ 3. start of play -----
if has_phase play; then
dlog "phase 3: start of play"
burst 20_game_start 8 0.4
hold Up 3.0                       # classic control: Up = walk forward (into the courtyard)
shot 21_walk_in
burst 22_welcome 12 1.0
tap space 0.2                     # next sentence
wait_s 0.6
shot 23_after_space
fi

# ------------------------------------------------------------------- 4. pause menu -------
if has_phase menu; then
dlog "phase 4: pause menu"
tap Escape 0.2; wait_s 0.8
shot 30_menu_main                 # cursor on CONTINUE (f=0)
tap Down 0.15; wait_s 0.4
shot 31_menu_save_highlight
tap space 0.2; wait_s 0.6
shot 32_menu_save_slots           # 7 slots "EMPTY"/"DAY n <hour>"; never press space here
tap Escape 0.2; wait_s 0.8        # Esc inside the menu = CONTINUE (w.a: f=0,g=0,C.e=true)
tap Escape 0.2; wait_s 0.8        # reopen
tap Down 0.15; wait_s 0.3; tap Down 0.15; wait_s 0.4
tap space 0.2; wait_s 0.6
shot 33_menu_load_slots
tap Escape 0.2; wait_s 0.8
tap Escape 0.2; wait_s 0.8
for k in 1 2 3; do tap Down 0.15; wait_s 0.3; done
shot 34_menu_sound_0              # SOUND: VOICES,SFX
tap space 0.2; wait_s 0.5; shot 34_menu_sound_1   # SFX
tap space 0.2; wait_s 0.5; shot 34_menu_sound_2   # SILENCE
tap space 0.2; wait_s 0.5; shot 34_menu_sound_3   # back to VOICES,SFX
tap Down 0.15; wait_s 0.3
tap space 0.2; wait_s 0.5; shot 35_menu_music_off
tap space 0.2; wait_s 0.5; shot 35_menu_music_on
tap Down 0.15; wait_s 0.3
tap space 0.2; wait_s 0.5; shot 36_menu_control_directional
tap space 0.2; wait_s 0.5; shot 36_menu_control_classic
tap Down 0.15; wait_s 0.4; shot 37_menu_fullscreen_highlight   # NOT selected
tap Down 0.15; wait_s 0.3
tap space 0.2; wait_s 0.5; shot 38_menu_extras_toggled
tap space 0.2; wait_s 0.5; shot 38_menu_extras_back
tap Down 0.15; wait_s 0.4; shot 39_menu_restart_highlight      # NOT selected
tap Down 0.15; wait_s 0.4; shot 39_menu_exit_highlight         # NOT selected
tap Escape 0.2; wait_s 0.8
shot 39_menu_closed
fi

# ---------------------------------------------------------------------- 5. walk ----------
if has_phase walk; then
dlog "phase 5: walk"
tap Right 0.15; wait_s 0.3; hold Up 2.0; shot 40_walk_1
tap Left 0.15; wait_s 0.3; hold Up 2.0; shot 40_walk_2
tap Left 0.15; wait_s 0.3; hold Up 2.0; shot 40_walk_3
audio_level 3
check_audio
fi

# ----------------------------------------------------------- 6. idle until game over -----
if [[ $GAMEOVER == 1 ]] && has_phase gameover; then
  dlog "phase 6: idle until game over (cap ${GAMEOVER_CAP}s)"
  mkdir -p "$SHOT_DIR/50_idle"
  t_end=$(( $(date +%s) + GAMEOVER_CAP )); i=0; over=0
  while (( $(date +%s) < t_end )); do
    nm=$(printf '50_idle/%03d' "$i"); SHOT_FULL=0 shot "$nm"; i=$((i + 1))
    f="$(nat "$nm")"
    top=$(convert "$f" -crop 320x160+0+0 +repage -colorspace gray -format '%[fx:mean]' info:)
    band=$(convert "$f" -crop 120x10+100+126 +repage -colorspace gray -format '%[fx:maxima]' info:)
    if LC_ALL=C awk -v t="$top" -v b="$band" 'BEGIN{exit !(t < 0.06 && b > 0.95)}'; then over=1; break; fi
    wait_s 5
  done
  if (( over )); then
    wait_s 1; shot 59_game_over
    dlog "game over screen reached"
    tap space 0.2; wait_s 6; shot 60_after_game_over
  else
    dlog "no game over within ${GAMEOVER_CAP}s"
  fi
fi
dlog "tour done"
exit 0
}

#!/usr/bin/env bash
# probe_parchment.sh [INTERVAL=5] [CAP_SECONDS=900]
# Skips the credits with Space, starts the intro parchment and captures it every INTERVAL s
# until the frame stays unchanged for 3 captures (parchment finished) or CAP_SECONDS.
# Early probe, kept for reference. Superseded by
#   PHASES=parchment PARCH_FULL=1 ... tools/drivers/pristine_tour.sh
# NOTE: its 6 Space taps at 8 s assume they all land after the loading screen.
set -euo pipefail
source "$HEADLESS_LIB"
iv="${1:-5}" cap="${2:-900}"
export SHOT_FULL=0
wait_s 8
for i in 1 2 3 4 5 6; do tap space 0.2; wait_s 1; done
shot p_pulsa
tap space 0.2
dlog "parchment started (fade ~64 frames)"
t_start=$(date +%s); i=0; same=0; prev=""
while (( $(date +%s) - t_start < cap )); do
  shot "$(printf 'p_%03d' "$i")"
  h=$(png_hash "$SHOT_DIR/$(printf 'p_%03d' "$i").png")
  if [[ $h == "$prev" ]]; then same=$((same+1)); else same=0; fi
  prev=$h; i=$((i+1))
  if (( same >= 2 )); then dlog "parchment static for 3 captures -> finished"; break; fi
  wait_s "$iv"
done
audio_level 3
dlog "pressing space after the finished parchment"
tap space 0.2
burst after 10 1

#!/usr/bin/env bash
# interactive.sh: keeps the game running for manual/experimental driving from other shells.
# Writes $RUN_DIR/env.sh (source it to get DISPLAY, WIN_ID, GAME_PID, ... and the helpers),
# then waits until $RUN_DIR/stop exists, the game dies, or MAX seconds (default 1800) pass.
set -euo pipefail
source "$HEADLESS_LIB"
{
  for v in DISPLAY GAME_PID WIN_ID SHOT_DIR RUN_DIR GAME_LOG GAME_DIR LANG_CODE NULL_SINK NULL_SINK_IDX HEADLESS_LIB T0 EVID_LOG TITLE_RE; do
    printf 'export %s=%q\n' "$v" "${!v}"
  done
  printf 'source %q\n' "$HEADLESS_LIB"
} > "$RUN_DIR/env.sh"
dlog "interactive: source $RUN_DIR/env.sh ; touch $RUN_DIR/stop to end"
max="${1:-1800}"
end=$(( $(date +%s) + max ))
while [[ ! -e $RUN_DIR/stop ]] && game_alive && [[ $(date +%s) -lt $end ]]; do sleep 0.5; done
rm -f "$RUN_DIR/stop"

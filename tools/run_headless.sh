#!/usr/bin/env bash
# run_headless.sh - run "The Abbey of Crime Extensum" invisibly and silently, then hand
# control to a driver script.
#
#   tools/run_headless.sh <gamedir> <lang> <driver-script> [driver-args...]
#
#   <gamedir>  directory containing TheAbbeyOfCrimeExtensum.jar (the game writes
#              savedata.bin next to the jar). Refused if it is inside original/.
#   <lang>     es | en | it | fr | de | pl  (passed to the game as argv[0])
#   <driver>   bash script; it is run with `bash <driver> [driver-args...]` and gets:
#                DISPLAY=:N  GAME_PID  WIN_ID  SHOT_DIR  RUN_DIR  GAME_LOG  GAME_DIR
#                LANG_CODE  NULL_SINK  HEADLESS_LIB  T0 (epoch ms when java started)
#              and should `source "$HEADLESS_LIB"` for helpers (shot, tap, hold, wait_s,
#              dlog, check_invisible, check_audio, ...).
#
# Invisibility: the game runs on a private Xvfb (-displayfd, unix socket only). DISPLAY
#   is never :0 for anything this script starts. :0 is only *queried* (read-only
#   `xdotool search`) to prove the game window is not there.
# Silence (three independent layers):
#   1. a private PulseAudio/PipeWire null sink (module-null-sink), PULSE_SINK=<it>;
#   2. a private ALSA config (ALSA_CONFIG_PATH) whose pcm.default is the pulse plugin
#      with device=<null sink>  (Java Sound -> ALSA "default" -> pulse);
#   3. bubblewrap hides /dev/snd from the JVM, so Java Sound cannot fall back to a raw
#      hw:/plughw: device (the game opens the FIRST mixer that accepts 44.1k/16/stereo).
#   An audio watchdog kills the game if any of its sink-inputs is on another sink.
#
# Environment overrides (all optional):
#   XVFB_BIN XVFB_SCREEN(1920x1080x24) XVFB_EXTRA  JAVA_BIN(java) JAVA_MEM(-Xms256M -Xmx256M)
#   JAVA_EXTRA  JAR_NAME(TheAbbeyOfCrimeExtensum.jar)  RUN_DIR SHOT_DIR
#   WINDOW_TIMEOUT(120 s) DRIVER_TIMEOUT(1800 s)  ALLOW_NO_BWRAP(0)
#
# Exit status: the driver's exit status (or non-zero if setup failed).
#
# The whole body is one { ... } block: bash parses it completely before running it, so
# editing this file while a run is in progress cannot corrupt that run (bash otherwise
# reads scripts incrementally - VERIFIED: an edit mid-run produced "ort: command not found").
{
set -euo pipefail

TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_DIR="$(dirname "$TOOLS_DIR")"
XVFB_BIN="${XVFB_BIN:-$TOOLS_DIR/xvfb-root/usr/bin/Xvfb}"
# The game asks for a 1296x871 window (320*4+16 x 208*4+39, Abadia.a()) and centres it,
# so the screen must be larger than 1280x800 or the window hangs off the top/left edge.
XVFB_SCREEN="${XVFB_SCREEN:-1920x1080x24}"
XVFB_EXTRA="${XVFB_EXTRA:-}"
JAVA_BIN="${JAVA_BIN:-java}"
JAVA_MEM="${JAVA_MEM:--Xms256M -Xmx256M}"
JAVA_EXTRA="${JAVA_EXTRA:-}"
JAR_NAME="${JAR_NAME:-TheAbbeyOfCrimeExtensum.jar}"
WINDOW_TIMEOUT="${WINDOW_TIMEOUT:-120}"
DRIVER_TIMEOUT="${DRIVER_TIMEOUT:-1800}"
ALLOW_NO_BWRAP="${ALLOW_NO_BWRAP:-0}"
HEADLESS_LIB="$TOOLS_DIR/headless_lib.sh"
# Window titles per language (abadia.E.h): es, en/pl, it, fr, de.
TITLE_RE='Abad|Abbey|Abbaz|abbaye|Abtei'

die() { echo "run_headless: $*" >&2; exit 1; }
usage() { sed -n '2,32p' "${BASH_SOURCE[0]}" >&2; exit 2; }

[[ $# -ge 3 ]] || usage
[[ -d $1 ]] || die "game dir not found: $1"
GAME_DIR="$(cd "$1" && pwd -P)"
LANG_CODE="$2"
[[ -f $3 ]] || die "driver not found: $3"
DRIVER="$(realpath "$3")"
shift 3

case "$LANG_CODE" in es|en|it|fr|de|pl) ;; *) echo "run_headless: warning: unknown lang '$LANG_CODE' (game falls back to en)" >&2 ;; esac
[[ -f "$GAME_DIR/$JAR_NAME" ]] || die "no $JAR_NAME in $GAME_DIR"
case "$GAME_DIR/" in "$PROJECT_DIR/original/"*) die "refusing to run inside original/ (pristine, read-only)";; esac
[[ -x $XVFB_BIN ]] || die "Xvfb not executable: $XVFB_BIN"
for t in xdotool xwd convert pactl xwininfo realpath timeout; do command -v "$t" >/dev/null || die "missing tool: $t"; done
if ! command -v bwrap >/dev/null && [[ $ALLOW_NO_BWRAP != 1 ]]; then
  die "bwrap missing: cannot hide /dev/snd (set ALLOW_NO_BWRAP=1 to accept the risk)"
fi

RUN_DIR="${RUN_DIR:-$PROJECT_DIR/work/runs/$(date +%Y%m%d-%H%M%S)-$LANG_CODE-$$}"
mkdir -p "$RUN_DIR"
RUN_DIR="$(cd "$RUN_DIR" && pwd -P)"
SHOT_DIR="${SHOT_DIR:-$RUN_DIR/shots}"
mkdir -p "$SHOT_DIR"
SHOT_DIR="$(cd "$SHOT_DIR" && pwd -P)"
GAME_LOG="$RUN_DIR/game.log"          # java stdout+stderr
EVID_LOG="$RUN_DIR/evidence.log"       # invisibility / silence evidence, timings
XVFB_LOG="$RUN_DIR/xvfb.log"
JAVA_TMP="$RUN_DIR/javatmp"            # java.io.tmpdir: the game writes abbey*.tmp audio files
mkdir -p "$JAVA_TMP"

XVFB_PID="" BWRAP_PID="" GAME_PID="" MOD="" WATCH_PID="" NULL_SINK="" DISPLAY_NUM="" DRIVER_PID=""
now_ms() { date +%s%3N; }
elog() { printf '[%s] %s\n' "$(date +%T.%3N)" "$*" | tee -a "$EVID_LOG" >&2; }

cleanup() {
  local rc=$?
  trap - EXIT INT TERM HUP
  set +e
  if [[ -n $DRIVER_PID ]] && kill -0 "$DRIVER_PID" 2>/dev/null; then
    elog "cleanup: stopping driver (timeout pid $DRIVER_PID)"
    kill -TERM "$DRIVER_PID" 2>/dev/null; wait "$DRIVER_PID" 2>/dev/null
  fi
  if [[ -n $WATCH_PID ]]; then kill "$WATCH_PID" 2>/dev/null; wait "$WATCH_PID" 2>/dev/null; fi
  if [[ -n $GAME_PID ]] && kill -0 "$GAME_PID" 2>/dev/null; then
    elog "cleanup: SIGTERM game pid $GAME_PID"
    kill -TERM "$GAME_PID" 2>/dev/null
    for _ in $(seq 1 50); do kill -0 "$GAME_PID" 2>/dev/null || break; sleep 0.1; done
    if kill -0 "$GAME_PID" 2>/dev/null; then elog "cleanup: SIGKILL game pid $GAME_PID"; kill -KILL "$GAME_PID" 2>/dev/null; fi
  fi
  if [[ -n $BWRAP_PID ]]; then
    for _ in $(seq 1 30); do kill -0 "$BWRAP_PID" 2>/dev/null || break; sleep 0.1; done
    kill -0 "$BWRAP_PID" 2>/dev/null && kill -TERM "$BWRAP_PID" 2>/dev/null
    wait "$BWRAP_PID" 2>/dev/null
  fi
  if [[ -n $XVFB_PID ]]; then kill -TERM "$XVFB_PID" 2>/dev/null; wait "$XVFB_PID" 2>/dev/null; fi
  if [[ -n $MOD ]]; then pactl unload-module "$MOD" 2>/dev/null && elog "cleanup: unloaded null-sink module $MOD"; fi
  local left
  left=$(find "$JAVA_TMP" -mindepth 1 2>/dev/null | wc -l)
  [[ $left -gt 0 ]] && elog "cleanup: $left leftover file(s) in java.io.tmpdir removed"
  rm -rf "$JAVA_TMP"
  elog "done rc=$rc  run dir: $RUN_DIR"
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

echo "$$" > "$RUN_DIR/run_headless.pid"
elog "run_headless pid=$$: game=$GAME_DIR lang=$LANG_CODE driver=$DRIVER run=$RUN_DIR"

# ---- 1. private Xvfb ------------------------------------------------------------------
DFILE="$RUN_DIR/xvfb.displayfd"
: > "$DFILE"
# shellcheck disable=SC2086
"$XVFB_BIN" -displayfd 3 -screen 0 "$XVFB_SCREEN" -nolisten tcp $XVFB_EXTRA 3>"$DFILE" >"$XVFB_LOG" 2>&1 &
XVFB_PID=$!
for _ in $(seq 1 100); do
  [[ -s $DFILE ]] && break
  kill -0 "$XVFB_PID" 2>/dev/null || die "Xvfb exited early, see $XVFB_LOG"
  sleep 0.1
done
DISPLAY_NUM="$(tr -dc '0-9' < "$DFILE")"
[[ -n $DISPLAY_NUM ]] || die "Xvfb did not report a display number"
[[ $DISPLAY_NUM != 0 ]] || die "refusing display :0"
export DISPLAY=":$DISPLAY_NUM"
elog "Xvfb pid=$XVFB_PID display=$DISPLAY screen=$XVFB_SCREEN"
# No X key auto-repeat on the private server: a held key (walking) is then exactly one
# KeyPress + one KeyRelease, instead of a 25 Hz press/release storm after 660 ms.
if [[ ${XVFB_AUTOREPEAT:-0} != 1 ]] && command -v xset >/dev/null; then xset -r || true; fi

# ---- 2. private null sink + ALSA config --------------------------------------------------
NULL_SINK="abbey_mute_$$"
MOD="$(pactl load-module module-null-sink sink_name="$NULL_SINK" sink_properties=device.description="$NULL_SINK")"
[[ $MOD =~ ^[0-9]+$ ]] || die "could not load module-null-sink: $MOD"
NULL_SINK_IDX="$(pactl list short sinks | awk -v s="$NULL_SINK" '$2==s{print $1}')"
[[ -n $NULL_SINK_IDX ]] || die "null sink $NULL_SINK not visible in pactl list"
elog "null sink $NULL_SINK index=$NULL_SINK_IDX module=$MOD"
ASOUND_CONF="$RUN_DIR/asound-abbey.conf"
cat > "$ASOUND_CONF" <<EOF
# generated by run_headless.sh: route ALSA default to the private null sink only
pcm.!default { type pulse device "$NULL_SINK" }
ctl.!default { type pulse device "$NULL_SINK" }
EOF

# ---- 3. the game, sandboxed so /dev/snd is invisible -------------------------------------
INFO="$RUN_DIR/bwrap.info"
: > "$INFO"
# shellcheck disable=SC2206
JAVA_CMD=("$JAVA_BIN" $JAVA_MEM "-Djava.io.tmpdir=$JAVA_TMP" $JAVA_EXTRA -jar "$JAR_NAME" "$LANG_CODE")
T0="$(now_ms)"
if command -v bwrap >/dev/null; then
  ( cd "$GAME_DIR" && exec env DISPLAY="$DISPLAY" PULSE_SINK="$NULL_SINK" \
      ALSA_CONFIG_PATH="/usr/share/alsa/alsa.conf:$ASOUND_CONF" \
      bwrap --dev-bind / / --tmpfs /dev/snd --die-with-parent --new-session \
            --chdir "$GAME_DIR" --info-fd 4 -- "${JAVA_CMD[@]}" ) 4>"$INFO" >"$GAME_LOG" 2>&1 &
  BWRAP_PID=$!
  for _ in $(seq 1 100); do
    [[ -s $INFO ]] && grep -q 'child-pid' "$INFO" && break
    kill -0 "$BWRAP_PID" 2>/dev/null || die "bwrap exited early, see $GAME_LOG"
    sleep 0.05
  done
  GAME_PID="$(grep -o '"child-pid": *[0-9]*' "$INFO" | grep -o '[0-9]*$')"
else
  elog "WARNING: no bwrap, /dev/snd is visible to the JVM"
  ( cd "$GAME_DIR" && exec env DISPLAY="$DISPLAY" PULSE_SINK="$NULL_SINK" \
      ALSA_CONFIG_PATH="/usr/share/alsa/alsa.conf:$ASOUND_CONF" "${JAVA_CMD[@]}" ) >"$GAME_LOG" 2>&1 &
  GAME_PID=$!
fi
[[ -n $GAME_PID ]] || die "could not determine game pid"
elog "game pid=$GAME_PID (bwrap pid=${BWRAP_PID:-none}) cmd: ${JAVA_CMD[*]}"
GAME_DISPLAY="$(tr '\0' '\n' < "/proc/$GAME_PID/environ" 2>/dev/null | grep '^DISPLAY=' || true)"
elog "game env: $GAME_DISPLAY  $(tr '\0' '\n' < "/proc/$GAME_PID/environ" 2>/dev/null | grep '^PULSE_SINK=' || true)"
[[ $GAME_DISPLAY == "DISPLAY=$DISPLAY" ]] || die "game process has unexpected $GAME_DISPLAY"
elog "game sees /dev/snd: $(ls -A "/proc/$GAME_PID/root/dev/snd" 2>/dev/null | wc -l) entries"

# ---- 4. audio watchdog --------------------------------------------------------------------
# Lists "<sink-input-index> <sink-index>" for every sink-input owned by the game pid.
game_sink_inputs() {
  pactl list sink-inputs 2>/dev/null | awk -v pid="$GAME_PID" '
    /^Sink Input #/ { idx=substr($3,2); sink="" }
    /^[ \t]*Sink: / { sink=$2 }
    /application\.process\.id = / { v=$3; gsub(/"/,"",v); if (v==pid) print idx, sink }'
}
(
  trap - EXIT
  while kill -0 "$GAME_PID" 2>/dev/null; do
    while read -r si sk; do
      [[ -z $si ]] && continue
      if [[ $sk != "$NULL_SINK_IDX" ]]; then
        pactl move-sink-input "$si" "$NULL_SINK" 2>/dev/null || true
        elog "AUDIO LEAK: sink-input $si of game on sink $sk (not $NULL_SINK_IDX) -> killing game"
        kill -KILL "$GAME_PID" 2>/dev/null || true
      fi
    done < <(game_sink_inputs)
    sleep 0.25
  done
) &
WATCH_PID=$!

# ---- 5. wait for the window ---------------------------------------------------------------
WIN_ID=""
deadline=$(( $(now_ms) + WINDOW_TIMEOUT * 1000 ))
while [[ $(now_ms) -lt $deadline ]]; do
  kill -0 "$GAME_PID" 2>/dev/null || die "game exited before showing a window, see $GAME_LOG"
  WIN_ID="$(xdotool search --onlyvisible --name "$TITLE_RE" 2>/dev/null | head -n1 || true)"
  [[ -n $WIN_ID ]] && break
  sleep 0.1
done
[[ -n $WIN_ID ]] || die "no game window on $DISPLAY after ${WINDOW_TIMEOUT}s"
T_WIN="$(now_ms)"
elog "window $WIN_ID '$(xdotool getwindowname "$WIN_ID")' mapped after $(( T_WIN - T0 )) ms"
xwininfo -id "$WIN_ID" | grep -E 'Absolute|Width|Height|Map State' | sed 's/^ */  /' | tee -a "$EVID_LOG" >&2
# There is no window manager (windowactivate needs one). Java only accepts keys while the
# X focus is on the frame's "FocusProxy" child, so focus that (see headless_lib.sh _focus).
FP_HEX=""
for _ in $(seq 1 50); do
  FP_HEX="$(xwininfo -id "$WIN_ID" -children 2>/dev/null | awk '/"FocusProxy"/{print $1; exit}')"
  [[ -n $FP_HEX ]] && break
  sleep 0.1
done
if [[ -n $FP_HEX ]]; then
  sleep 0.5   # let Java finish its own show/focus handling first
  xdotool windowfocus "$(printf '%d' "$FP_HEX")" || true
else
  xdotool windowfocus "$WIN_ID" || true
fi
sleep 0.2
elog "focus on $DISPLAY: $(xdotool getwindowfocus 2>/dev/null) (frame $WIN_ID, FocusProxy ${FP_HEX:-none})"

export DISPLAY GAME_PID WIN_ID SHOT_DIR RUN_DIR GAME_LOG GAME_DIR LANG_CODE NULL_SINK \
       NULL_SINK_IDX HEADLESS_LIB T0 EVID_LOG TITLE_RE

# shellcheck source=headless_lib.sh
source "$HEADLESS_LIB"
check_invisible || true
check_audio || true

# ---- 6. driver ----------------------------------------------------------------------------
elog "driver start: $DRIVER $*"
# Run the driver in the background and `wait` for it: unlike a foreground child, `wait`
# is interrupted by INT/TERM, so killing this script's PID always runs cleanup().
set +e
timeout "$DRIVER_TIMEOUT" bash "$DRIVER" "$@" &
DRIVER_PID=$!
wait "$DRIVER_PID"
DRC=$?
DRIVER_PID=""
set -e
elog "driver exit=$DRC"
if kill -0 "$GAME_PID" 2>/dev/null; then check_invisible || true; check_audio || true; fi
grep -n -E 'Exception|Error|at abadia' "$GAME_LOG" | head -20 | sed 's/^/  game.log: /' >> "$EVID_LOG" || true
exit "$DRC"
}

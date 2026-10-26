# headless_lib.sh - helpers for driver scripts started by tools/run_headless.sh.
# Usage inside a driver:   source "$HEADLESS_LIB"
#
#   shot NAME          window capture -> $SHOT_DIR/NAME.png (the 320x208 game frame, exact
#                      native pixels) and, unless SHOT_FULL=0, $SHOT_DIR/full/NAME.png
#                      (raw window pixels, 1296x871 in windowed mode)
#   shot_root NAME     whole Xvfb screen  (xwd -root | convert) -> $SHOT_DIR/root/NAME.png
#   burst PREFIX N INTERVAL   N shots PREFIX_000.. every INTERVAL seconds
#   tap KEY [HOLD]     key down, hold HOLD s (default 0.25), key up (XTEST -> focused window).
#                      The game's keyReleased() clears the flag that keyPressed() set, so a
#                      press+release shorter than one game frame can be lost: always hold.
#   hold KEY SECONDS   same, for walking
#   keys KEY...        raw `xdotool key` (12 ms press) - unreliable for the game, see tap
#   wait_s SECONDS     sleep; fails if the game has died
#   frame_hash [MASK]  md5 of the native frame; MASK = "x0,y0 x1,y1" rectangle blanked first
#   png_hash FILE      signature of a PNG's pixels (file bytes are not comparable across grabs)
#   grab_native FILE   native frame to FILE without logging (fast polling)
#   wait_stable [TIMEOUT] [MASK]   until two consecutive frames (0.25 s apart) are equal
#   wait_until_frame_changes [TIMEOUT]
#   audio_level [SECONDS]  records the private null sink's monitor, logs peak/RMS (proves the
#                      game makes sound and that it all goes to the null sink)
#   dlog MSG           timestamped line (+seconds since java start) in $RUN_DIR/driver.log
#   check_invisible    proves no game window exists on the user's :0 (read-only query)
#   check_audio        logs the game's PulseAudio sink-inputs and their sink
#   game_geom          sets GAME_WX GAME_WY GAME_WW GAME_WH GAME_SCALE GAME_OX GAME_OY
#
# Every X call here goes to $DISPLAY (the private Xvfb); :0 is only queried by
# check_invisible. WIN_ID is re-resolved automatically if the game recreates its window
# (F1 / menu FULLSCREEN toggles dispose() the JFrame and map a new X window).

: "${DISPLAY:?}" "${WIN_ID:?}" "${SHOT_DIR:?}" "${GAME_PID:?}" "${RUN_DIR:?}" "${T0:?}"
if [[ $DISPLAY == ":0" || $DISPLAY == ":0.0" ]]; then
  echo "headless_lib: refusing to work on DISPLAY=:0" >&2
  return 1 2>/dev/null || exit 1
fi
DRIVER_LOG="${DRIVER_LOG:-$RUN_DIR/driver.log}"
EVID_LOG="${EVID_LOG:-$RUN_DIR/evidence.log}"
TITLE_RE="${TITLE_RE:-Abad|Abbey|Abbaz|abbaye|Abtei}"
SHOT_FULL="${SHOT_FULL:-1}"

_now_ms() { date +%s%3N; }
_elapsed() { LC_ALL=C awk -v a="$(_now_ms)" -v b="$T0" 'BEGIN{printf "%7.2f", (a-b)/1000}'; }
dlog() { printf '[%s +%ss] %s\n' "$(date +%T.%3N)" "$(_elapsed)" "$*" | tee -a "$DRIVER_LOG" >&2; }
elog() { printf '[%s] %s\n' "$(date +%T.%3N)" "$*" | tee -a "$EVID_LOG" >&2; }
game_alive() { kill -0 "$GAME_PID" 2>/dev/null; }

_win_refresh() {
  if ! xwininfo -id "$WIN_ID" 2>/dev/null | grep -q 'IsViewable'; then
    local w
    w="$(xdotool search --onlyvisible --name "$TITLE_RE" 2>/dev/null | head -n1 || true)"
    if [[ -n $w && $w != "$WIN_ID" ]]; then
      dlog "game window changed $WIN_ID -> $w"
      WIN_ID="$w"
      export WIN_ID
    fi
  fi
}

game_geom() {
  _win_refresh
  local info
  info="$(xwininfo -id "$WIN_ID")"
  GAME_WX=$(awk '/Absolute upper-left X/{print $NF}' <<<"$info")
  GAME_WY=$(awk '/Absolute upper-left Y/{print $NF}' <<<"$info")
  GAME_WW=$(awk '/^ *Width:/{print $NF}' <<<"$info")
  GAME_WH=$(awk '/^ *Height:/{print $NF}' <<<"$info")
  # abadia.H.componentResized: d = min(w/320, h/208); E.a(Graphics) centres 320d x 208d.
  local sx=$(( GAME_WW / 320 )) sy=$(( GAME_WH / 208 ))
  GAME_SCALE=$(( sx < sy ? sx : sy ))
  if (( GAME_SCALE < 1 )); then GAME_SCALE=1; fi
  GAME_OX=$(( (GAME_WW - 320 * GAME_SCALE) / 2 ))
  GAME_OY=$(( (GAME_WH - 208 * GAME_SCALE) / 2 ))
}

# Keyboard focus (VERIFIED on Xvfb without a window manager): Java/XToolkit only turns X
# key events into AWT KeyEvents when the X input focus is on the frame's 1x1 child window
# named "FocusProxy". With focus on the frame itself (what `xdotool windowfocus <frame>`
# gives) every key is silently dropped. Java sometimes moves focus to the proxy by itself
# (a race at startup), sometimes not - so always focus the proxy explicitly.
focus_proxy_id() {
  local hex
  hex="$(xwininfo -id "$WIN_ID" -children 2>/dev/null | awk '/"FocusProxy"/{print $1; exit}')"
  if [[ -n $hex ]]; then printf '%d\n' "$hex"; fi
  return 0
}
_focus_ok() {
  local f p
  f="$(xdotool getwindowfocus 2>/dev/null)" || return 1
  p="$(focus_proxy_id)"
  [[ -n $p && $f == "$p" ]]
}
_focus() {
  _win_refresh
  if ! _focus_ok; then
    local p
    p="$(focus_proxy_id)"
    if [[ -n $p ]]; then
      xdotool windowfocus "$p" 2>/dev/null || true
    else
      xdotool windowfocus "$WIN_ID" 2>/dev/null || true
    fi
    sleep 0.2
    dlog "focus set -> $(xdotool getwindowfocus 2>/dev/null) (proxy ${p:-none}, frame $WIN_ID)"
  fi
}

# native frame as raw RGB on stdout
_native_rgb() {
  game_geom
  xwd -silent -id "$WIN_ID" | convert xwd:- \
    -crop "$((320 * GAME_SCALE))x$((208 * GAME_SCALE))+$GAME_OX+$GAME_OY" +repage \
    -sample 320x208 "$@" rgb:-
}

shot() {
  local name="$1"
  mkdir -p "$SHOT_DIR"
  game_alive || { dlog "shot $name: game not running"; return 1; }
  game_geom
  local nat="$SHOT_DIR/$name.png" tmp="$RUN_DIR/.shot_$$.xwd"
  mkdir -p "$(dirname "$nat")"
  xwd -silent -id "$WIN_ID" > "$tmp"
  if [[ $SHOT_FULL == 1 ]]; then
    mkdir -p "$(dirname "$SHOT_DIR/full/$name.png")"
    convert "xwd:$tmp" -define png:exclude-chunks=date,time "png:$SHOT_DIR/full/$name.png"
  fi
  convert "xwd:$tmp" -crop "$((320 * GAME_SCALE))x$((208 * GAME_SCALE))+$GAME_OX+$GAME_OY" +repage \
          -sample 320x208 -define png:exclude-chunks=date,time "png:$nat"
  rm -f "$tmp"
  dlog "shot $name"
}

shot_root() {
  local name="$1"
  mkdir -p "$SHOT_DIR/root"
  xwd -silent -root | convert xwd:- "png:$SHOT_DIR/root/$name.png"
  dlog "shot_root $name"
}

burst() {
  local prefix="$1" n="$2" iv="$3" i
  for (( i = 0; i < n; i++ )); do
    shot "$(printf '%s_%03d' "$prefix" "$i")"
    if (( i < n - 1 )); then sleep "$iv"; fi
  done
  return 0
}

tap() {
  local key="$1" hold_s="${2:-0.25}"
  _focus
  xdotool keydown "$key"; sleep "$hold_s"; xdotool keyup "$key"
  dlog "tap $key (${hold_s}s)"
}

hold() { tap "$1" "$2"; }

keys() { _focus; xdotool key --delay 80 "$@"; dlog "keys $*"; }

wait_s() {
  sleep "$1"
  game_alive || { dlog "game died"; return 1; }
}

frame_hash() {
  if [[ -n ${1:-} ]]; then
    _native_rgb -fill black -draw "rectangle $1" | md5sum | cut -c1-32
  else
    _native_rgb | md5sum | cut -c1-32
  fi
}

png_hash() { identify -format '%#' "$1"; }   # ImageMagick pixel signature (ignores metadata)

# grab_native FILE: the native 320x208 frame to FILE (PNG), no logging (for fast polling)
grab_native() {
  game_geom
  xwd -silent -id "$WIN_ID" | convert xwd:- \
    -crop "$((320 * GAME_SCALE))x$((208 * GAME_SCALE))+$GAME_OX+$GAME_OY" +repage \
    -sample 320x208 -define png:exclude-chunks=date,time "png:$1"
}

wait_stable() {
  local timeout_s="${1:-30}" mask="${2:-}" a b t_end
  t_end=$(( $(_now_ms) + timeout_s * 1000 ))
  a="$(frame_hash "$mask")"
  while [[ $(_now_ms) -lt $t_end ]]; do
    sleep 0.25
    b="$(frame_hash "$mask")"
    [[ $a == "$b" ]] && return 0
    a="$b"
  done
  return 1
}

wait_until_frame_changes() {
  local timeout_s="${1:-30}" a b t_end
  t_end=$(( $(_now_ms) + timeout_s * 1000 ))
  a="$(frame_hash)"
  while [[ $(_now_ms) -lt $t_end ]]; do
    sleep 0.2
    b="$(frame_hash)"
    [[ $a != "$b" ]] && return 0
  done
  return 1
}

audio_level() {
  local secs="${1:-3}" res
  res="$(timeout "$secs" parec --device="$NULL_SINK.monitor" --format=s16le --rate=44100 \
          --channels=2 --raw 2>/dev/null | python3 -I -c '
import sys, array, math
a = array.array("h"); a.frombytes(sys.stdin.buffer.read() or b"")
n = len(a)
pk = max((abs(x) for x in a), default=0)
rms = math.sqrt(sum(x*x for x in a)/n) if n else 0.0
print(f"samples={n} peak={pk} rms={rms:.1f}")' || true)"
  elog "AUDIO LEVEL on $NULL_SINK.monitor over ${secs}s: $res"
}

check_invisible() {
  local out names="" w
  _win_refresh
  out="$(DISPLAY=:0 xdotool search --name "$TITLE_RE" 2>/dev/null || true)"
  if [[ -z $out ]]; then
    elog "INVISIBLE OK: DISPLAY=:0 xdotool search --name '$TITLE_RE' -> no windows"
  else
    for w in $out; do names+="$w='$(DISPLAY=:0 xdotool getwindowname "$w" 2>/dev/null)' "; done
    elog "CHECK: windows on :0 match '$TITLE_RE': $names (not ours unless the game is on :0)"
  fi
  elog "game window on $DISPLAY: $WIN_ID '$(xdotool getwindowname "$WIN_ID" 2>/dev/null)' map_state=$(xwininfo -id "$WIN_ID" | awk '/Map State/{print $NF}')"
}

check_audio() {
  local blk
  blk="$(pactl list sink-inputs 2>/dev/null | awk -v pid="$GAME_PID" '
    /^Sink Input #/ { if (keep) print buf; buf=$0; keep=0; next }
    { buf = buf "\n" $0 }
    /application\.process\.id = / { v=$3; gsub(/"/,"",v); if (v==pid) keep=1 }
    END { if (keep) print buf }' | grep -E 'Sink Input #|^\s*Sink:|Corked|Mute|application\.name|application\.process\.id|target\.object|node\.target|media\.name' || true)"
  if [[ -z $blk ]]; then
    elog "AUDIO: game pid $GAME_PID has no sink-input right now"
  else
    elog "AUDIO: game sink-inputs (null sink $NULL_SINK = index $NULL_SINK_IDX):"
    sed 's/^/    /' <<<"$blk" | tee -a "$EVID_LOG" >&2
  fi
}

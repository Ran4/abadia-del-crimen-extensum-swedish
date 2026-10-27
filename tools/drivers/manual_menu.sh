{
# manual_menu.sh - driver for tools/run_headless.sh: the pause menu over a scene with no
# dialogue box, for the user manual's MENYN picture (screenshots/runtime_sv/49_menu_no_dialogue.png).
# The tour opens the menu during Remigio's welcome (g49), so its menu frames all have dialogue
# under the menu scroll. Here the menu is opened at the first frames of play, before William
# has walked in and before anyone speaks: the same moment as 20_play_start_hud.png.
#
#   tools/run_headless.sh <gamedir> de tools/drivers/manual_menu.sh
set -euo pipefail
source "$HEADLESS_LIB"

INTRO_SECS="${INTRO_SECS:-52}"

dlog "wait ${INTRO_SECS}s for 'Press to start'"
wait_s "$INTRO_SECS"
shot 01_press_to_start
tap space 0.2                     # fade to the parchment
wait_s 2.5
shot 02_parchment
wait_s 4.0
tap space 0.2                     # y.a() state 2: skip the parchment
wait_s 1.5
burst 03_play_start 6 0.4
shot 04_before_menu
tap Escape 0.2; wait_s 0.8
shot 05_menu_main                 # cursor on CONTINUE, no dialogue underneath
wait_s 1.0
shot 06_menu_main_again           # the same frame a second later (stable)
tap Escape 0.2; wait_s 0.8
shot 07_menu_closed
dlog "manual_menu done"
exit 0
}

#!/bin/sh
# Render every string of a language with the game's own drawing code, headless (no DISPLAY,
# java.awt.headless=true; no Frame/Window is ever loaded). See HARNESS.md.
# usage: tools/harness/render.sh --jar GAME.jar [--res RESDIR] --lang es|en|it|fr|de|pl --out OUTDIR
#            [--ref-lang C] [--msgfile F] [--textfile F] [--parchfile F] [--only-custom]
#            [--no-parchment] [--no-images] [--no-raw] [--per-sheet N]
# exit 0 = OK, 2 = errors (missing glyphs / layout errors), 1 = usage/crash
# env: JAVA (default java), HARNESS_BUILD (default: the content-addressed build dir that build.sh
#      prints, under <project>/work/harness_build/; built on demand, never deleted while in use)
H=$(cd "$(dirname "$0")" && pwd)
JAVA=${JAVA:-java}
HB=$("$H/build.sh" ${HARNESS_BUILD:+"$HARNESS_BUILD"}) || exit 1
exec env -u DISPLAY -u WAYLAND_DISPLAY "$JAVA" -Djava.awt.headless=true -Xmx512m \
    -cp "$HB/launcher" harness.Launch --harness-classes "$HB/gameside" "$@"

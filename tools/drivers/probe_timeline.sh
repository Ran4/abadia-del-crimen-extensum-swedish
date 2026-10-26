#!/usr/bin/env bash
# probe_timeline.sh [SECONDS=60] [INTERVAL=0.5] [PREFIX=t]
# No input: just screenshots every INTERVAL seconds, to measure the attract/intro timeline.
set -euo pipefail
source "$HEADLESS_LIB"
dur="${1:-60}" iv="${2:-0.5}" prefix="${3:-t}"
n=$(awk -v d="$dur" -v i="$iv" 'BEGIN{printf "%d", d/i}')
burst "$prefix" "$n" "$iv"

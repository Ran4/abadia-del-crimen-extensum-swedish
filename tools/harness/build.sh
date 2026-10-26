#!/bin/sh
# Compile the headless text-rendering harness (javac --release 8), a copy of the Phase A harness
# (work/phaseA/harness, documented in HARNESS.md) so the delivered tooling is self-contained.
#
# usage: tools/harness/build.sh            build if needed; print the build dir on stdout
#        tools/harness/build.sh OUTDIR     the same, into an explicit dir (rebuilt if its sources differ)
#
# The default build dir is content-addressed: <project>/work/harness_build/<key>, key = sha256 of
# the sources, this script and the javac version. A finished build is never modified or deleted, so
# any number of renders (render_strings.py, regress.py, other tracks) can run concurrently with each
# other and with tools/build.py (which only wipes work/build/). A new build is compiled into a temp
# dir and published with one atomic rename; when two processes race, the loser discards its copy.
# The game classes are compiled against the pristine original jar (read-only).
set -eu
H=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$(dirname "$H")")
REF=$ROOT/original/TheAbbeyOfCrimeExtensum.jar
KEY=$( (cd "$H" && find src -name '*.java' -type f | LC_ALL=C sort | xargs sha256sum && sha256sum build.sh \
        && javac -version 2>&1) | sha256sum | cut -c1-16)
OUT=${1:-$ROOT/work/harness_build/$KEY}

complete() { [ -f "$1/.complete" ] && [ "$(cat "$1/.complete")" = "$KEY" ]; }

if complete "$OUT"; then
    echo "$OUT"
    exit 0
fi
mkdir -p "$(dirname "$OUT")"
TMP=$(mktemp -d "$OUT.tmp.XXXXXX")
chmod 755 "$TMP"
trap 'rm -rf "$TMP"' EXIT
trap 'exit 1' INT TERM HUP
mkdir -p "$TMP/gameside" "$TMP/launcher" "$TMP/tools"
{
    javac --release 8 -encoding UTF-8 -nowarn -cp "$REF" -d "$TMP/gameside" "$H"/src/abadia/*.java
    javac --release 8 -encoding UTF-8 -nowarn -d "$TMP/launcher" "$H"/src/harness/*.java
    javac --release 8 -encoding UTF-8 -nowarn -d "$TMP/tools" "$H"/src/PergHarness.java "$H"/src/OverlayPixels.java
} >&2
echo "$KEY" > "$TMP/.complete"
if [ -e "$OUT" ] && [ "$#" -ge 1 ]; then
    # explicit OUTDIR holding an older build: replace it (only this case deletes a build)
    exec 9>"$ROOT/work/.harness.lock"
    flock 9
    if ! complete "$OUT"; then
        rm -rf "$OUT"
        mv -T "$TMP" "$OUT"
    fi
elif ! mv -T "$TMP" "$OUT" 2>/dev/null; then
    complete "$OUT" || { echo "harness build: cannot publish $OUT" >&2; exit 1; }
fi
echo "harness built: $OUT" >&2
echo "$OUT"

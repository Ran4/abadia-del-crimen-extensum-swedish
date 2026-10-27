# /// script
# requires-python = ">=3.11"
# ///
"""Lint translation/strings_sv.tsv against every text rule of docs/FORMAT.md (§1.4, §1.7-1.9,
§1.13, §2) before it goes into abadia.k / w.class / E.class.

  uv run tools/lint_strings.py [TSV] [--placeholder] [--ref tools/data/context.tsv] [-q]

Exit 0 = no errors (warnings allowed), 1 = errors, 2 = unreadable input.
--placeholder: Spanish placeholder text is allowed, so the untranslated-text checks become warnings.

Importable: read_tsv(path), read_ref(path), lint(rows, ref, placeholder) -> (errors, warnings),
hud_bytes(sv) -> 7 hour bytes. tools/build.py runs it first and stops on errors.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import text_sim  # noqa: E402  (copy of work/phaseA/scripts/text_sim.py, the exact port of j.c/e/b)

HEADER = ["array", "index", "context", "speaker", "max_len", "es", "en", "sv", "note"]
REF_HEADER = ["array", "index", "context", "speaker", "max_len", "es", "en"]
DEFAULT_TSV = ROOT / "translation" / "strings_sv.tsv"
DEFAULT_REF = HERE / "data" / "context.tsv"   # byte copy of work/phaseA/context.tsv

SIZES = {"g": 164, "a": 4, "b": 7, "c": 2, "d": 2, "e": 3, "f": 10}
EXTRA = [("w.t", 4), ("w.u", 4), ("E.h", 4)]

# Characters the shared glyph switch j.a(int,...) draws (FORMAT §1.9), after the Å patch (D5).
SV_CORE = set(" ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,:;?!'-ÅÄÖÉ")
SWITCH_EXTRA = set("ÀÁÂÇÈÊÌÍÎÑÒÓÔÙÚÛÜßĄĆĘŁŃŒŚŹŻ¡¿")
DRAWABLE = SV_CORE | SWITCH_EXTRA
MARKERS = set("@_*")
HUD_ALLOWED = set(" ABCDEFGHIJKLMNOPQRSTUVWXYZÖ")
HUD_O_UMLAUT = 119      # precomposed HUD Ö: fuente.png cell 74 (FORMAT §2.4, GLOSSARY §5.1)

MENU_HARD = [27, 26, 26, 25, 25, 25, 27, 27, 27, 27]   # FORMAT §1.7 (opaque paper per row)
MENU_SOFT = 23                                          # 190-px highlight bar
MENU_SUFFIX = {3: "e", 4: "c", 5: "d", 6: "c", 7: "c"}
# Remigio's day-1 walk (FORMAT §1.8): isolated tick caps, plus 158 chained after 157.
# g157: 215, not the longest shipped (it, 232). Phase E measured the real window from g157's start to
# g158's (Remigio reaching waypoint 8 interrupts it) at 220 and 223 ticks (work/phaseE/runs/run1,
# run2 events.log: ak 6351 -> 7011, 1233 -> 1903); 215 keeps the whole message, its 17-tick linger
# included, inside that window with a margin (es, 221, and it, 232, lose part of their linger).
# Measured windows of the others, far above their caps: g158 187 ticks, g159 319.
TICK_CAPS = {157: 215, 158: 96, 159: 211, 51: 77}
TICK_CAP_158_CHAINED = 129
TITLE_RE = re.compile(r"Abad|Abbey|Abbaz|abbaye|Abtei")   # tools/run_headless.sh line 56
MARKER_OK = re.compile(r"@(?:[0-9]|1[0-4])(?= |$)")
# Untranslated-text check (an error, a warning under --placeholder) for every used g string and
# every a/c/d/e/f/w.t/w.u string that equals its es or en text. Explicit allowlists:
UNTRANSLATED_OK = {92}   # g indices: "@1 ..." (punctuation only)
SAME_OK = {"SFX"}         # whole a/c/d/e/f strings that are also correct Swedish
SAME_OK_B = {(3, " SEXT  ")}   # HUD hours equal to es/en that are also the Swedish (en b[3], GLOSSARY §5.1)
NOTE_BYTES = re.compile(r"bytes=([0-9]+(?:,[0-9]+)*)(?=$|[\s;])")   # GLOSSARY §5.1 hour_hud note token


def _split_lines(raw: bytes, path) -> list[str]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as ex:
        raise ValueError(f"{path}: not UTF-8: {ex}")
    if text.startswith("﻿"):
        raise ValueError(f"{path}: starts with a BOM")
    if "\r" in text:
        raise ValueError(f"{path}: contains CR (LF line endings required)")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def read_tsv(path) -> list[dict]:
    """strings_sv.tsv -> list of row dicts (header checked; fields raw, spaces significant)."""
    path = pathlib.Path(path)
    lines = _split_lines(path.read_bytes(), path)
    if not lines or lines[0].split("\t") != HEADER:
        raise ValueError(f"{path}: header must be exactly {'<TAB>'.join(HEADER)}")
    rows = []
    for n, line in enumerate(lines[1:], 2):
        f = line.split("\t")
        if len(f) != len(HEADER):
            raise ValueError(f"{path} line {n}: {len(f)} fields, expected {len(HEADER)}")
        rows.append(dict(zip(HEADER, f)) | {"_line": n})
    return rows


def read_ref(path=DEFAULT_REF) -> list[dict]:
    path = pathlib.Path(path)
    lines = _split_lines(path.read_bytes(), path)
    if lines[0].split("\t") != REF_HEADER:
        raise ValueError(f"{path}: unexpected header")
    return [dict(zip(REF_HEADER, line.split("\t"))) for line in lines[1:]]


def hud_bytes(sv: str) -> list[int]:
    return [HUD_O_UMLAUT if ch == "Ö" else ord(ch) for ch in sv]


def markers(s: str) -> list[str]:
    return re.findall(r"@[0-9]*", s)


def space_runs(s: str) -> list[int]:
    return sorted(len(m) for m in re.findall(r" {2,}", s))


def has_letters(s: str) -> bool:
    return any(ch.isalpha() for ch in re.sub(r"@[0-9]+", "", s))


def mutf8_len(s: str) -> int:
    n = 0
    for ch in s.encode("utf-16-le").decode("utf-16-le", "surrogatepass"):
        c = ord(ch)
        n += 1 if 0 < c < 0x80 else 2 if c < 0x800 else 3
    return n


def lint(rows: list[dict], ref: list[dict], placeholder: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    E = errors.append
    W = warnings.append
    untranslated = W if placeholder else E

    # ---------------------------------------------------------------- structure (§1.11, §1.13.1)
    keys = [(r["array"], r["index"]) for r in rows]
    ref_keys = [(r["array"], r["index"]) for r in ref]
    if keys != ref_keys:
        for n, (k, rk) in enumerate(zip(keys, ref_keys)):
            if k != rk:
                E(f"row {n + 2}: key {k} where context.tsv has {rk} (same rows and order required)")
                break
        if len(keys) != len(ref_keys):
            E(f"{len(keys)} rows, context.tsv has {len(ref_keys)}")
        return errors, warnings
    for r, rr in zip(rows, ref):
        for col in ("es", "en"):
            if r[col] != rr[col]:
                E(f"{r['array']}[{r['index']}]: column {col} differs from context.tsv (copy it unchanged)")
    sv = {(r["array"], r["index"]): r["sv"] for r in rows}
    notes = {(r["array"], r["index"]): r.get("note", "") for r in rows}
    es = {(r["array"], r["index"]): r["es"] for r in ref}
    en = {(r["array"], r["index"]): r["en"] for r in ref}
    used = {(r["array"], r["index"]): r["context"].startswith("USED") for r in ref}
    arr = {a: [sv[(a, str(i))] for i in range(n) if (a, str(i)) in sv] for a, n in SIZES.items()}
    for a, n in SIZES.items():
        if len(arr[a]) != n:
            E(f"array {a}: {len(arr[a])} rows, expected {n}")
    for a, i in EXTRA:
        if (a, str(i)) not in sv:
            E(f"missing row {a} {i}")
    if errors:
        return errors, warnings

    def charset(where: str, s: str, allow_markers: bool):
        foreign = sorted(set(ch for ch in s if ch in SWITCH_EXTRA))
        if foreign:
            W(f"{where}: {' '.join(foreign)} draw, but are not Swedish letters (intended?)")
        for pos, ch in enumerate(s):
            if ch in DRAWABLE or (allow_markers and ch in MARKERS):
                continue
            if "a" <= ch <= "z":
                E(f"{where} pos {pos}: lowercase '{ch}' (lowercase codes draw special glyphs; UPPERCASE only)")
            elif ch == "}":
                E(f"{where} pos {pos}: '}}' draws a bare ring after the Å patch")
            elif ch in MARKERS:
                E(f"{where} pos {pos}: marker '{ch}' outside g (a line break or ¿ in j.a(String))")
            elif ch == " ":
                E(f"{where} pos {pos}: NBSP")
            else:
                E(f"{where} pos {pos}: '{ch}' (U+{ord(ch):04X}) has no glyph in the in-game font (FORMAT §1.9)")

    def no_outer_ws(where: str, s: str):
        if s != s.strip(" "):
            E(f"{where}: leading/trailing space in {s!r}")

    # ---------------------------------------------------------------- g (messages)
    g_sv = arr["g"]
    if g_sv[0] != "":
        E("g[0] must be the empty string")
    for i in range(1, 164):
        key = ("g", str(i))
        s, e = g_sv[i], es[key]
        where = f"g[{i}]"
        is_used = used[key]
        lvl = E if is_used else W
        if s == "":
            E(f"{where}: empty")
            continue
        if mutf8_len(s) > 65535:
            E(f"{where}: longer than the class-file limit of 65535 bytes")
        charset(where, s, True)
        if s.startswith("@") != e.startswith("@"):
            E(f"{where}: starts with '@' = {s.startswith('@')}, es = {e.startswith('@')} (must match)")
        if markers(s) != markers(e):
            E(f"{where}: speaker markers {markers(s)} != es {markers(e)}")
        for m in re.finditer("@", s):
            if not MARKER_OK.match(s, m.start()):
                E(f"{where} pos {m.start()}: '@' must be '@0'..'@14' followed by a space or the end "
                  f"(parseInt / speaker range), got {s[m.start():m.start() + 5]!r}")
        if "@14" in s:
            W(f"{where}: @14 has no face (and Adso's voice)")
        # space before a mid-string marker (FORMAT §1.4): an error unless es has one before the same marker
        s_pos = [m.start() for m in re.finditer("@", s)]
        e_pos = [m.start() for m in re.finditer("@", e)]
        for k, p in enumerate(s_pos):
            if p > 0 and s[p - 1] == " ":
                es_has = k < len(e_pos) and e_pos[k] > 0 and e[e_pos[k] - 1] == " "
                (W if es_has else E)(f"{where}: space before marker #{k + 1} at pos {p} (glue it to the "
                                     f"preceding text; a full line gives a blank page)" + (" (as in es)" if es_has else ""))
        if re.search(r"_ *@", s):
            E(f"{where}: '_' right before '@' gives a blank \" _ \" page")
        if "%" in s:
            E(f"{where}: '%' is a line break in j.a(String)")
        if s != s.strip(" ") or "\t" in s:
            E(f"{where}: leading/trailing whitespace (a trailing space can crash e())")
        if s.endswith("_") or s.endswith("*"):
            E(f"{where}: ends with '{s[-1]}' (AIOOBE when it lands at a page start)")
        runs, e_runs = space_runs(s), space_runs(e)
        rest = list(e_runs)
        for run in runs:
            if run in rest:
                rest.remove(run)
            else:
                E(f"{where}: a run of {run} spaces that es does not have (each extra space is a pause and "
                  f"widens the line)")
        for tok in s.replace("@", " _ @").split(" "):
            if len(tok) > 35:
                E(f"{where}: word of {len(tok)} chars > 35 ({tok[:40]!r}): the rest of the message is lost")
            for ch in "_*":
                if ch in tok[:-1]:
                    E(f"{where}: '{ch}' inside the token {tok!r} (only at the end of a token)")
        sim = text_sim.simulate(s)
        probs = [p for p in sim["problems"] if not p.startswith("does not start with")]
        for p in probs:
            lvl(f"{where}: message simulation: {p}")
        if "QUATUOR" in e:
            if "QUATUOR" not in s:
                E(f"{where}: must keep the word QUATUOR (Q and R are the hard-coded mirror keys)")
            elif s.count("QUATUOR") < e.count("QUATUOR"):
                W(f"{where}: QUATUOR {s.count('QUATUOR')}x, es has it {e.count('QUATUOR')}x")
        if i in TICK_CAPS and "ticks" in sim:
            if sim["ticks"] > TICK_CAPS[i]:
                E(f"{where}: {sim['ticks']} ticks > cap {TICK_CAPS[i]} (Remigio's walk cuts it, FORMAT §1.8)")
        if is_used and has_letters(s) and (s == e or s == en[key]) and i not in UNTRANSLATED_OK:
            untranslated(f"{where}: identical to {'es' if s == e else 'en'} (untranslated)")
        if not is_used and has_letters(s) and (s == e or s == en[key]):
            W(f"{where} (dead): identical to {'es' if s == e else 'en'} (untranslated)")
    s157 = text_sim.simulate(g_sv[157])
    if "leftover_bR" in s157:
        if s157["leftover_bR"]:
            W(f"g[157]: leaves bR={s157['leftover_bR']} (last page < 40 ticks), which delays g[158]")
        s158 = text_sim.simulate(g_sv[158], bR0=s157["leftover_bR"])
        if s158.get("ticks", 0) > TICK_CAP_158_CHAINED:
            E(f"g[158]: {s158['ticks']} ticks chained after g[157] > cap {TICK_CAP_158_CHAINED}")

    # ---------------------------------------------------------------- a (end screen)
    for i, s in enumerate(arr["a"]):
        where = f"a[{i}]"
        charset(where, s, False)
        if i == 1:
            if not s.startswith(" "):
                E(f"{where}: must start with a space (drawn as pct + a[1])")
            if len(s) > 37:
                E(f"{where}: {len(s)} glyphs > 37 (the pct prefix has up to 3 digits; 40 centred)")
            if s != s.rstrip(" "):
                E(f"{where}: trailing space")
        else:
            no_outer_ws(where, s)
            if len(s) > 40:
                E(f"{where}: {len(s)} glyphs > 40 (centred on 320 px)")
        if s == "":
            E(f"{where}: empty")

    # ---------------------------------------------------------------- c d e f (pause menu)
    for a in "cdef":
        for i, s in enumerate(arr[a]):
            where = f"{a}[{i}]"
            charset(where, s, False)
            if a == "f" and i in MENU_SUFFIX and s == "":
                # label + value row (w.java: v[i].concat(value)): an empty label is safe and the
                # value carries the whole row (GLOSSARY §6.3: Swedish f[5] = "")
                continue
            if s == "":
                E(f"{where}: empty")
            if a == "f" and i in MENU_SUFFIX:
                e_s = es[("f", str(i))]
                if s.startswith(" "):
                    E(f"{where}: leading space")
                if s.endswith(" ") != e_s.endswith(" "):
                    E(f"{where}: label must end with its own separator (': ' or ' ') like es {e_s!r}")
                if s.endswith("  "):
                    E(f"{where}: ends with two spaces")
            else:
                no_outer_ws(where, s)
    for r in range(10):
        base = arr["f"][r]
        combos = [base + suf for suf in arr[MENU_SUFFIX[r]]] if r in MENU_SUFFIX else [base]
        for c in combos:
            if len(c) > MENU_HARD[r]:
                E(f"menu row {r}: {c!r} is {len(c)} glyphs > hard limit {MENU_HARD[r]} (leaves the menu parchment)")
            elif len(c) > MENU_SOFT:
                W(f"menu row {r}: {c!r} is {len(c)} glyphs > {MENU_SOFT} (wider than the highlight bar)")
    for a in "acdef":
        for i, s in enumerate(arr[a]):
            key = (a, str(i))
            if has_letters(s) and (s == es[key] or s == en[key]) and s not in SAME_OK:
                untranslated(f"{a}[{i}]: identical to {'es' if s == es[key] else 'en'} ({s!r}) (untranslated)")

    # ---------------------------------------------------------------- b (HUD hours, §2)
    for i, s in enumerate(arr["b"]):
        where = f"b[{i}] (HUD hour)"
        if len(s) != 7:
            E(f"{where}: {len(s)} chars, exactly 7 required ({s!r})")
        for pos, ch in enumerate(s):
            if ch not in HUD_ALLOWED:
                E(f"{where} pos {pos}: {ch!r} not allowed (space, A-Z, or Ö = precomposed byte {HUD_O_UMLAUT})")
        if s.strip() == "":
            E(f"{where}: blank")
        key = ("b", str(i))
        if has_letters(s) and (s == es[key] or s == en[key]) and (i, s) not in SAME_OK_B:
            untranslated(f"{where}: identical to {'es' if s == es[key] else 'en'} ({s!r}) (untranslated)")
        note = notes[key]
        if note.startswith("bytes="):
            m = NOTE_BYTES.match(note)
            if not m:
                E(f"{where}: note starts with 'bytes=' but its first token is not a comma-separated list of "
                  f"integers: {note.split()[0]!r}")
            else:
                nb = [int(x) for x in m.group(1).split(",")]
                if all(ch in HUD_ALLOWED for ch in s) and nb != hud_bytes(s):
                    E(f"{where}: note bytes={m.group(1)} disagree with the sv cell {s!r}, which the build "
                      f"emits as {','.join(map(str, hud_bytes(s)))} (fix one of them)")

    # ---------------------------------------------------------------- w.t, w.u, E.h (§1.10)
    t, u, h = sv[("w.t", "4")], sv[("w.u", "4")], sv[("E.h", "4")]
    charset("w.t[4]", t, False)
    charset("w.u[4]", u, False)
    if not t.endswith(" ") or t.endswith("  ") or t.startswith(" "):
        E(f"w.t[4]: {t!r} must be a word plus exactly one trailing space (label = w.t + day + ' ' + hour)")
    if len(t) > 6:
        E(f"w.t[4]: {len(t)} glyphs > 6 (the save label must fit 15 glyphs)")
    no_outer_ws("w.u[4]", u)
    if not 0 < len(u) <= 15:
        E(f"w.u[4]: {len(u)} glyphs, 1..15 allowed")
    if h != h.strip() or not h:
        E(f"E.h[4]: empty or leading/trailing whitespace: {h!r}")
    if any(ord(ch) < 32 for ch in h):
        E("E.h[4]: control characters")
    if not TITLE_RE.search(h):
        W(f"E.h[4]: window title {h!r} does not match TITLE_RE in tools/run_headless.sh and "
          f"tools/headless_lib.sh (every headless run would time out finding the window; DECISIONS D6)")
    for key, s in ((("w.t", "4"), t), (("w.u", "4"), u)):
        if has_letters(s) and (s == es[key] or s == en[key]):
            untranslated(f"{key[0]}[4]: identical to {'es' if s == es[key] else 'en'} ({s!r})")
    return errors, warnings


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tsv", nargs="?", default=str(DEFAULT_TSV))
    ap.add_argument("--ref", default=str(DEFAULT_REF))
    ap.add_argument("--placeholder", action="store_true")
    ap.add_argument("-q", "--quiet", action="store_true", help="print errors only")
    a = ap.parse_args()
    try:
        rows = read_tsv(a.tsv)
        ref = read_ref(a.ref)
    except (OSError, ValueError) as ex:
        print(f"ERROR {ex}")
        sys.exit(2)
    errors, warnings = lint(rows, ref, a.placeholder)
    if not a.quiet:
        for w in warnings:
            print("WARNING", w)
    for e in errors:
        print("ERROR", e)
    print(f"lint {a.tsv}: {len(errors)} error(s), {len(warnings)} warning(s)"
          + (" [placeholder mode]" if a.placeholder else ""))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

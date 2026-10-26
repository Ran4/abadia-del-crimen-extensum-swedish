# /// script
# requires-python = ">=3.11"
# ///
"""Check the Swedish strings (and parchments) against translation/glossary.tsv (GLOSSARY §11).

  uv run tools/check_glossary.py [--strings TSV] [--glossary TSV] [--perg1 F] [--perg2 F]
                                 [--only g:1,2,3] [-q]

Checks, per row kind:
  phrase     one ' / ' alternative stands verbatim in every message of the note's `g` list;
             `variant:` messages are listed as manual checks; `reserve` / `not in strings` rows
             are skipped
  forbidden  no alternative stands as a whole word (case-sensitive) in any g message, nor in
             the parchments when the note names a parchment
  latin      the form stands as a whole word in every g message the note names
  ui         a/c/d/e/f/w.t/w.u/E.h equal the sv cell exactly (the note starts with the field)
  hour_hud   b[h] equals the sv cell (the note names `hour h`)
  parchment  the form stands in the parchment(s) the note names (warning: forms inflect)
Other kinds (name, place, title, term, address, hour_text, image) are inflected or drawn and are
checked by people. Exit 1 on errors. Importable: load_glossary(path), check(strings, gloss, perg).
"""
import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import lint_strings  # noqa: E402

LETTER = "A-Za-zÅÄÖåäöÉéÍíÑñÁáÜü"


def load_glossary(path) -> list[dict]:
    lines = pathlib.Path(path).read_text(encoding="utf-8").split("\n")
    head = lines[0].split("\t")
    rows = []
    for n, line in enumerate(lines[1:], 2):
        if not line:
            continue
        f = line.split("\t")
        rows.append(dict(zip(head, f)) | {"_line": n})
    return rows


def _int_list(s: str) -> list[int]:
    return [int(x) for x in re.findall(r"\d+", s)]


def phrase_lists(note: str) -> tuple[list[int], list[int], bool]:
    """(verbatim indices, variant indices, skip) per GLOSSARY §11 index syntax."""
    n = re.sub(r"\([^()]*\)", "", note).strip()
    if n.startswith("reserve") or "not in strings" in n:
        return [], [], True
    plain, variant = [], []
    m = re.match(r"g ([\d,\s]+)", n)
    if m:
        plain = _int_list(m.group(1))
    for v in re.finditer(r"variant: ([\d,\s]+)", n):
        variant += _int_list(v.group(1))
    return plain, variant, False


def whole_word(form: str, text: str) -> bool:
    return re.search(rf"(?<![{LETTER}]){re.escape(form)}(?![{LETTER}])", text) is not None


def check(strings: dict, gloss: list[dict], perg: dict, only: set | None = None):
    """strings: {(array, index): sv}; perg: {1: text, 2: text} (may be empty).
    Returns (errors, warnings, manual)."""
    errors, warnings, manual = [], [], []
    g = {i: s for (a, i), s in strings.items() if a == "g"}

    def want(key):
        return only is None or key in only

    for r in gloss:
        kind, sv, note, es = r.get("kind"), r.get("sv", ""), r.get("note", ""), r.get("es", "")
        alts = [a for a in sv.split(" / ")] if sv else []
        where = f"glossary line {r['_line']} ({kind} {es!r})"
        if kind == "phrase":
            plain, variant, skip = phrase_lists(note)
            if skip:
                continue
            for i in plain:
                if not want(("g", i)):
                    continue
                if i not in g:
                    errors.append(f"{where}: g{i} missing from strings")
                elif not any(a and a in g[i] for a in alts):
                    errors.append(f"{where}: g{i} lacks the fixed form {sv!r}")
            for i in variant:
                if want(("g", i)):
                    manual.append(f"{where}: g{i} variant of {sv!r}, check by hand")
        elif kind == "forbidden":
            in_perg = "parchment" in note or "pergamino" in note
            for a in alts:
                if not a:
                    continue
                for i, s in g.items():
                    if want(("g", i)) and whole_word(a, s):
                        errors.append(f"{where}: forbidden {a!r} in g{i}; {note}")
                if in_perg:
                    for p, t in perg.items():
                        if whole_word(a, t):
                            errors.append(f"{where}: forbidden {a!r} in pergamino{p}")
        elif kind == "latin":
            for i in sorted(set(int(x) for x in re.findall(r"\bg ?(\d+)", note))):
                if not want(("g", i)) or i not in g:
                    continue
                if not whole_word(sv, g[i]):
                    errors.append(f"{where}: Latin {sv!r} not kept verbatim in g{i}")
        elif kind == "ui":
            m = re.match(r"(a|c|d|e|f|w\.t|w\.u|E\.h)\[(\d+)\]", note)
            if not m:
                warnings.append(f"{where}: ui note does not name its field")
                continue
            key = (m.group(1), int(m.group(2)))
            if want(key) and key in strings and strings[key] != sv:
                errors.append(f"{where}: {key[0]}[{key[1]}] is {strings[key]!r}, glossary says {sv!r}")
        elif kind == "hour_hud":
            m = re.search(r"hour (\d)", note)
            if m:
                key = ("b", int(m.group(1)))
                if want(key) and key in strings and strings[key] != sv:
                    errors.append(f"{where}: b[{key[1]}] is {strings[key]!r}, glossary says {sv!r}")
        elif kind == "parchment" and perg:
            ps = [p for p in (1, 2) if re.search(rf"parchment {p}\b|parchment 1, 2|parchment credits", note)]
            if "credits" in note:
                ps = [2]
            for p in ps:
                if p in perg and not any(a and a in perg[p] for a in alts):
                    warnings.append(f"{where}: pergamino{p} lacks {sv!r} (fine if inflected)")
    return errors, warnings, manual


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strings", default=str(ROOT / "translation" / "strings_sv.tsv"))
    ap.add_argument("--glossary", default=str(ROOT / "translation" / "glossary.tsv"))
    ap.add_argument("--perg1", default=str(ROOT / "translation" / "pergamino1_sv.txt"))
    ap.add_argument("--perg2", default=str(ROOT / "translation" / "pergamino2_sv.txt"))
    ap.add_argument("--only", default=None, help="e.g. g:1,5,7 (restrict to these rows)")
    ap.add_argument("-q", "--quiet", action="store_true", help="errors only")
    a = ap.parse_args()
    rows = lint_strings.read_tsv(a.strings)
    strings = {(r["array"], int(r["index"])): r["sv"] for r in rows}
    perg = {}
    for p, path in ((1, a.perg1), (2, a.perg2)):
        if pathlib.Path(path).exists():
            perg[p] = pathlib.Path(path).read_text(encoding="utf-8")
    only = None
    if a.only:
        arr, _, idx = a.only.partition(":")
        only = {(arr, int(x)) for x in idx.split(",") if x.strip()}
    errors, warnings, manual = check(strings, load_glossary(a.glossary), perg, only)
    for e in errors:
        print("ERROR", e)
    if not a.quiet:
        for w in warnings:
            print("WARN ", w)
        for m in manual:
            print("CHECK", m)
    print(f"{len(errors)} errors, {len(warnings)} warnings, {len(manual)} manual checks")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

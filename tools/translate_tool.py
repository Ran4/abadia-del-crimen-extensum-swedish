# /// script
# requires-python = ">=3.11"
# ///
"""Translation helper (Phase C): chunk plan, source view, per-chunk checks, merge, game order.

  uv run tools/translate_tool.py plan                       write/print work/phaseC/plan.json
  uv run tools/translate_tool.py show CHUNK|g52,g54         source rows of one chunk: context, speaker,
                                                            es/en/fr/it, es pages, relevant glossary rows
  uv run tools/translate_tool.py pages "TEXT"               how the game pages a g string; ticks
  uv run tools/translate_tool.py check FILE.json [...]      lint + glossary + timing for the chunk's rows
  uv run tools/translate_tool.py merge [--out TSV] [--force] all chunk files -> translation/strings_sv.tsv
                                                            (refused once the TSV is newer than the chunks)
  uv run tools/translate_tool.py extract g52,g54 OUT.json   rows of the TSV -> a chunk file (for `check`)
  uv run tools/translate_tool.py apply FILE.json            a chunk file's rows -> back into the TSV
  uv run tools/translate_tool.py gameorder [--tsv TSV] [--sv-only]   every used g string in rough game order
  uv run tools/translate_tool.py letras                     work/phaseC/letras_sv = original letras + the
                                                            current assets_sv/glyphs/letras_add.json, for
                                                            `uv run tools/letras.py check F --text --letras ...`

A chunk file is UTF-8 JSON: {"chunk": "c03", "rows": [{"array": "g", "index": 57, "sv": "...",
"note": "..."}, ...]}. Spaces in sv are significant. The latest file per chunk lives at
work/phaseC/chunks/<chunk>.json; `merge` reads exactly those (and work/phaseC/chunks/ui.json).
"""
import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import check_glossary  # noqa: E402
import lint_strings  # noqa: E402
import text_sim  # noqa: E402

ALL = ROOT / "work" / "phaseA" / "strings_all.json"
INDEX = ROOT / "work" / "phaseA" / "text_index.json"
PHASE = ROOT / "work" / "phaseC"
CHUNKS = PHASE / "chunks"
PLAN = PHASE / "plan.json"
GLOSSARY = ROOT / "translation" / "glossary.tsv"
OUT_TSV = ROOT / "translation" / "strings_sv.tsv"

MAX_CHARS = 2800
MAX_ROWS = 22
SPEAKERS = {0: "Guillermo", 1: "Adso", 2: "Severino", 3: "Abad", 4: "Malaquias", 5: "Berengario",
            6: "Bernardo Gui", 7: "Jorge", 8: "Remigio", 9: "?", 10: "Salvatore", 11: "villager",
            12: "Ubertino", 13: "Nicola", 14: "?"}
HOURS = ["NOCHE", "PRIMA", "TERCIA", "SEXTA", "NONA", "VISPERAS", "COMPLETAS"]


def ref_rows():
    return lint_strings.read_ref()


def all_strings():
    return json.loads(ALL.read_text(encoding="utf-8"))


def messages():
    return {m["index"]: m for m in json.loads(INDEX.read_text(encoding="utf-8"))["messages"]}


def make_plan():
    msgs = messages()
    es = all_strings()["es"]["g"]
    used = [i for i in range(164) if msgs[i]["used"]]
    unused = [i for i in range(1, 164) if not msgs[i]["used"]]
    chunks, cur, size = [], [], 0
    for i in used:
        n = len(es[i])
        if cur and (size + n > MAX_CHARS or len(cur) >= MAX_ROWS):
            chunks.append(cur)
            cur, size = [], 0
        cur.append(i)
        size += n
    if cur:
        if chunks and sum(len(es[i]) for i in cur) < MAX_CHARS // 3:
            chunks[-1] += cur   # a short tail joins the chunk before it
        else:
            chunks.append(cur)
    plan = [{"id": f"c{k + 1:02d}", "rows": [["g", i] for i in c],
             "es_chars": sum(len(es[i]) for i in c)} for k, c in enumerate(chunks)]
    plan.append({"id": "u01", "rows": [["g", i] for i in unused],
                 "es_chars": sum(len(es[i]) for i in unused), "unused": True})
    PHASE.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(json.dumps(plan, indent=1) + "\n", encoding="utf-8")
    return plan


def load_plan():
    return json.loads(PLAN.read_text(encoding="utf-8")) if PLAN.exists() else make_plan()


def gloss_rows_for(i, gloss):
    hits = []
    for r in gloss:
        kind, note = r.get("kind"), r.get("note", "")
        if kind in ("ui", "hour_hud", "image", "parchment"):
            continue
        if kind == "phrase":
            plain, variant, skip = check_glossary.phrase_lists(note)
            if i in plain or i in variant:
                hits.append(r)
            continue
        nums = set(int(x) for x in re.findall(r"(?<![=\d.])\b(\d{1,3})\b(?! glyph| cells| px)", note))
        if i in nums:
            hits.append(r)
    return hits


def pages_report(text, indent="    "):
    r = text_sim.simulate(text)
    out = [f"{indent}pages={len(r.get('pages', []))} ticks={r.get('ticks')} problems={r['problems']}"]
    for p in r.get("pages", []):
        lines = [ln.rstrip(" ") for ln in p["lines"]]
        out.append(f"{indent}@{p['speaker']:<2} " + " / ".join(f"|{ln}|" for ln in lines))
    return r, "\n".join(out)


def cmd_show(a):
    plan = {c["id"]: c for c in load_plan()}
    if a.chunk not in plan:
        if re.match(r"(g|a|b|c|d|e|f|w\.t|w\.u|E\.h)\[?\d", a.chunk):
            plan[a.chunk] = {"rows": [list(k) for k in parse_keys(a.chunk)]}
        else:
            sys.exit(f"unknown chunk {a.chunk}; known: {', '.join(plan)} (or give rows, e.g. g52,g54)")
    d, msgs = all_strings(), messages()
    ref = {(r["array"], int(r["index"])): r for r in ref_rows()}
    gloss = check_glossary.load_glossary(GLOSSARY)
    for arr, i in plan[a.chunk]["rows"]:
        r, m = ref[(arr, i)], msgs.get(i, {})
        print(f"=== {arr}[{i}]  speakers: {' > '.join(m.get('speaker_names', [])) or r['speaker']}")
        print(f"  when:    {r['context']}")
        print(f"  limits:  {r['max_len']}")
        for lang in ("es", "en", "fr", "it"):
            print(f"  {lang}: {d[lang][arr][i]!r}")
        if arr == "g" and d["es"]["g"][i]:
            print("  es as shown in game:")
            print(pages_report(d["es"]["g"][i])[1])
        hits = gloss_rows_for(i, gloss)
        if hits:
            print("  glossary rows naming this message:")
            for h in hits:
                print(f"    [{h['kind']}] {h['es']} -> {h['sv']}  ({h.get('note', '')[:160]})")
        print()


def cmd_pages(a):
    r, rep = pages_report(a.text, "")
    print(rep)


def read_chunk(path):
    d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    rows = d["rows"] if isinstance(d, dict) else d
    return d.get("chunk") if isinstance(d, dict) else None, rows


def overlay(chunk_files):
    """Full table: es text as placeholder, chunk rows on top. Returns (rows, chunk_keys)."""
    d = all_strings()
    rows, keys = [], []
    base = {}
    for r in ref_rows():
        key = (r["array"], int(r["index"]))
        if r["array"] in ("w.t", "w.u", "E.h"):
            sv = r["es"]
        elif r["array"] == "b":
            sv = r["es"]
        else:
            sv = d["es"][r["array"]][int(r["index"])]
        base[key] = dict(r) | {"sv": sv, "note": ""}
    for f in chunk_files:
        _, crow = read_chunk(f)
        for c in crow:
            key = (c["array"], int(c["index"]))
            if key not in base:
                sys.exit(f"{f}: unknown row {key}")
            base[key]["sv"] = c["sv"]
            base[key]["note"] = c.get("note", "")
            keys.append(key)
    for r in ref_rows():
        rows.append(base[(r["array"], int(r["index"]))])
    return rows, keys


def write_tsv(rows, path):
    out = ["\t".join(lint_strings.HEADER)]
    for r in rows:
        note = r.get("note", "").replace("\t", " ").replace("\n", " ")
        for k in ("sv",):
            if "\t" in r[k] or "\n" in r[k]:
                sys.exit(f"{r['array']}[{r['index']}]: tab or newline in sv")
        out.append("\t".join([r["array"], str(r["index"]), r["context"], r["speaker"], r["max_len"],
                              r["es"], r["en"], r["sv"], note]))
    pathlib.Path(path).write_text("\n".join(out) + "\n", encoding="utf-8")


def mentions(msg, key):
    arr, i = key
    pats = [rf"\b{re.escape(arr)}\[{i}\]", rf"\bg ?{i}\b"] if arr == "g" else [rf"\b{re.escape(arr)}\[{i}\]"]
    return any(re.search(p, msg) for p in pats)


def cmd_check(a):
    rows, keys = overlay(a.files)
    keyset = set(keys)
    errors, warnings = lint_strings.lint(rows, ref_rows(), placeholder=True)
    mine_e = [e for e in errors if any(mentions(e, k) for k in keyset)]
    mine_w = [w for w in warnings if any(mentions(w, k) for k in keyset)
              and "untranslated" not in w.lower() and "placeholder" not in w.lower()]
    strings = {(r["array"], int(r["index"])): r["sv"] for r in rows}
    ge, gw, gm = check_glossary.check(strings, check_glossary.load_glossary(GLOSSARY), {}, keyset)
    d = all_strings()
    print(f"# check of {len(keys)} rows: {', '.join(f'{k[0]}{k[1]}' for k in keys)}")
    n_err = len(mine_e) + len(ge)
    for e in mine_e:
        print("LINT ERROR", e)
    for e in ge:
        print("GLOSSARY ERROR", e)
    for w in mine_w:
        print("LINT WARN ", w)
    for m in gm:
        print("GLOSSARY CHECK", m)
    caps = lint_strings.TICK_CAPS
    print()
    tot_es = tot_sv = 0
    for key in keys:
        arr, i = key
        sv = strings[key]
        es = d["es"][arr][i] if arr in d["es"] else ""
        if arr != "g" or not sv:
            print(f"{arr}[{i}] {sv!r}")
            continue
        tot_es += len(es)
        tot_sv += len(sv)
        r, rep = pages_report(sv)
        r_es = text_sim.simulate(es) if es else {"ticks": 0, "pages": []}
        cap = f" CAP {caps[i]} ticks" if i in caps else ""
        over = " OVER CAP!" if i in caps and r.get("ticks", 0) > caps[i] else ""
        if over:
            n_err += 1
        ratio = f"{100 * (len(sv) - len(es)) / len(es):+.0f}%" if es else "n/a"
        print(f"g[{i}] chars {len(es)}->{len(sv)} ({ratio}); es pages {len(r_es.get('pages', []))} "
              f"ticks {r_es.get('ticks')}; sv:{cap}{over}")
        print(rep)
    if tot_es:
        print(f"\nchunk length {tot_es} -> {tot_sv} chars ({100 * (tot_sv - tot_es) / tot_es:+.1f}%; aim <= +12% overall)")
    print(f"\n{n_err} errors")
    sys.exit(1 if n_err else 0)


def chunk_files():
    plan = load_plan()
    files = []
    for c in plan:
        f = CHUNKS / f"{c['id']}.json"
        if f.exists():
            files.append(f)
        else:
            print(f"WARNING: no file for chunk {c['id']}; Spanish placeholder kept", file=sys.stderr)
    ui = CHUNKS / "ui.json"
    if ui.exists():
        files.append(ui)
    else:
        print("WARNING: no ui.json", file=sys.stderr)
    return files


def cmd_merge(a):
    files = chunk_files()
    out = pathlib.Path(a.out)
    if out.exists() and not a.force and all(f.stat().st_mtime < out.stat().st_mtime for f in files):
        sys.exit(f"{out} is newer than every chunk file: it has been edited since the chunks were merged "
                 f"(Phase E fixes live only there). Use extract/apply instead, or --force to overwrite it.")
    rows, keys = overlay(files)
    dup = {k for k in keys if keys.count(k) > 1}
    if dup:
        sys.exit(f"rows in more than one chunk file: {sorted(dup)}")
    write_tsv(rows, a.out)
    print(f"wrote {a.out}: {len(rows)} rows, {len(keys)} from {len(files)} chunk files")


def parse_keys(spec):
    keys = []
    for tok in spec.split(","):
        m = re.fullmatch(r"(g|a|b|c|d|e|f|w\.t|w\.u|E\.h)\[?(\d+)\]?", tok.strip())
        if not m:
            sys.exit(f"bad row key {tok!r} (use e.g. g52,g54,a1)")
        keys.append((m.group(1), int(m.group(2))))
    return keys


def cmd_extract(a):
    rows = {(r["array"], int(r["index"])): r for r in lint_strings.read_tsv(a.tsv)}
    out = [{"array": k[0], "index": k[1], "sv": rows[k]["sv"], "note": rows[k]["note"]} for k in parse_keys(a.keys)]
    pathlib.Path(a.out).write_text(json.dumps({"chunk": a.name, "rows": out}, ensure_ascii=False, indent=1) + "\n",
                                   encoding="utf-8")
    print(f"wrote {a.out}: {len(out)} rows from {a.tsv}")


def cmd_apply(a):
    rows = lint_strings.read_tsv(a.tsv)
    by_key = {(r["array"], int(r["index"])): r for r in rows}
    _, crow = read_chunk(a.file)
    for c in crow:
        key = (c["array"], int(c["index"]))
        if key not in by_key:
            sys.exit(f"{a.file}: unknown row {key}")
        by_key[key]["sv"] = c["sv"]
        if "note" in c:
            by_key[key]["note"] = c["note"]
    write_tsv(rows, a.tsv)
    print(f"applied {len(crow)} rows from {a.file} to {a.tsv}")


def order_key(m):
    w = m.get("when", "")
    day = re.search(r"day ?(\d)", w)
    hour = next((h for h, name in enumerate(HOURS) if name in w.upper()), 9)
    return (int(day.group(1)) if day else 9, hour, m["index"])


def cmd_gameorder(a):
    msgs = messages()
    sv = {}
    if pathlib.Path(a.tsv).exists():
        sv = {int(r["index"]): r["sv"] for r in lint_strings.read_tsv(a.tsv) if r["array"] == "g"}
    es = all_strings()["es"]["g"]
    for m in sorted((m for m in msgs.values() if m["used"]), key=order_key):
        i = m["index"]
        print(f"=== g[{i}] {' > '.join(m['speaker_names'])} | when: {m['when']}")
        if not a.sv_only:
            print(f"  es: {es[i]}")
        if i in sv:
            print(f"  sv: {sv[i]}")
    print("\n# unused messages (never shown)")
    for i in range(1, 164):
        if not msgs[i]["used"]:
            print(f"=== g[{i}] unused" + ("" if a.sv_only else f"\n  es: {es[i]}") + (f"\n  sv: {sv[i]}" if i in sv else ""))


def cmd_letras(a):
    import letras
    add_path = ROOT / "assets_sv" / "glyphs" / "letras_add.json"
    orig = (ROOT / "work" / "jar" / "res" / "letras").read_bytes()
    new, problems = letras.apply_add(orig, json.loads(add_path.read_text(encoding="utf-8")))
    if problems:
        sys.exit("\n".join(problems))
    out = PHASE / "letras_sv"
    PHASE.mkdir(parents=True, exist_ok=True)
    out.write_bytes(new)
    print(f"wrote {out} ({len(new)} bytes) from {add_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    s = sub.add_parser("show")
    s.add_argument("chunk")
    p = sub.add_parser("pages")
    p.add_argument("text")
    c = sub.add_parser("check")
    c.add_argument("files", nargs="+")
    m = sub.add_parser("merge")
    m.add_argument("--out", default=str(OUT_TSV))
    m.add_argument("--force", action="store_true")
    x = sub.add_parser("extract")
    x.add_argument("keys")
    x.add_argument("out")
    x.add_argument("--name", default="extract")
    x.add_argument("--tsv", default=str(OUT_TSV))
    y = sub.add_parser("apply")
    y.add_argument("file")
    y.add_argument("--tsv", default=str(OUT_TSV))
    g = sub.add_parser("gameorder")
    g.add_argument("--tsv", default=str(OUT_TSV))
    g.add_argument("--sv-only", action="store_true", help="Swedish only (a reader who never sees es)")
    sub.add_parser("letras")
    a = ap.parse_args()
    if a.cmd == "plan":
        for c in make_plan():
            print(c["id"], c["es_chars"], " ".join(f"{x[0]}{x[1]}" for x in c["rows"]))
    else:
        {"show": cmd_show, "pages": cmd_pages, "check": cmd_check, "merge": cmd_merge,
         "gameorder": cmd_gameorder, "letras": cmd_letras,
         "extract": cmd_extract, "apply": cmd_apply}[a.cmd](a)


if __name__ == "__main__":
    main()

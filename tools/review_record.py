#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Regenerate docs/TRANSLATION_REVIEW.md, the record of the translation review passes.

The verdicts of the review passes live in the workflow journals (Claude Code session files
outside the project). This script reads them, cross-checks them against the project files and
git history, and writes the record:

    uv run tools/review_record.py [--journals DIR] [--out FILE]

Inputs
  <journals>/wf_4a0ebacc-9c0/journal.jsonl   Phase C: translation, per-unit review, whole-game passes
  <journals>/wf_dcee03f1-9e3/journal.jsonl   Phase E: rendered-text and runtime critics, fixers
  <journals>/wf_4230a7f1-04d/journal.jsonl   Phase F: re-review of the 17 strings changed in Phase E
  <journals>/wf_cb1d7e9e-f32/journal.jsonl   Phase B: glossary critics (counts only, optional)
  work/phaseC/plan.json, work/phaseC/chunks/*.json, work/phaseF/rereview_result.json
  work/phaseF/ui_review/x01_result.json      Phase F final verification: the UI rows and the
                                             round-3 nits (editor, blind back-translation, meaning
                                             check). Not in any journal: without it a cross-check fails.
  translation/strings_sv.tsv (working tree and git commits e7b6230 = Phase C, 0450eaa = Phase E)
  translation/pergamino{1,2}_sv.txt

Each journal line is a JSON object. "started" lines carry an agent's "label" keyed by "agentId";
"result" lines carry that agent's full return value.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import io
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JOURNALS = (
    Path.home()
    / ".claude/projects/-home-ran-the-abbey-of-crime-extensum-swedish"
    / "8dfa1262-e7c1-4492-8c56-1b182a40f8ec/subagents/workflows"
)
WF_B, WF_C, WF_E, WF_F = "wf_cb1d7e9e-f32", "wf_4a0ebacc-9c0", "wf_dcee03f1-9e3", "wf_4230a7f1-04d"
COMMIT_C, COMMIT_E = "e7b6230", "0450eaa"
CHANGED17 = [52, 54, 61, 64, 75, 77, 85, 114, 118, 122, 125, 131, 143, 149, 150, 155, 163]
LENSES = ["language", "visual", "completeness", "runs"]
MAX_ROUNDS_C = 4  # MAX_ROUNDS in the Phase C workflow script
PARCH_NAME = {"perg1": "intro parchment (pergamino1)", "perg2": "ending parchment (pergamino2)"}

CHECKS: list[tuple[bool, str]] = []


def check(ok: bool, text: str) -> bool:
    CHECKS.append((bool(ok), text))
    if not ok:
        print(f"CHECK FAILED: {text}", file=sys.stderr)
    return bool(ok)


# ---------------------------------------------------------------------------- loading


class Journal:
    def __init__(self, path: Path):
        self.path = path
        self.items: list[tuple[str, object]] = []
        self.started = 0
        labels: dict[str, str] = {}
        done: set[str] = set()
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                o = json.loads(line)
                if o.get("type") == "started":
                    labels[o["agentId"]] = o.get("label", "?")
                    self.started += 1
                elif o.get("type") == "result":
                    done.add(o["agentId"])
                    self.items.append((labels.get(o["agentId"], "?"), o.get("result")))
        self.by_label = {lab: res for lab, res in self.items}
        missing = [lab for a, lab in labels.items() if a not in done]
        self.relaunched = sorted(lab for lab in missing if lab in self.by_label)
        self.no_result = sorted(lab for lab in missing if lab not in self.by_label)

    def get(self, label: str):
        return self.by_label.get(label)


def load_tsv(text: str) -> dict[tuple[str, int], dict]:
    rows = {}
    for r in csv.DictReader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE):
        rows[(r["array"], int(r["index"]))] = r
    return rows


def git_show(rev: str, path: str) -> str | None:
    p = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{path}"], capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


# ---------------------------------------------------------------------------- formatting


def clean(s) -> str:
    s = str(s or "").replace(str(ROOT) + "/", "")
    return re.sub(r"\s+", " ", s).strip()


def open_marks(s: str) -> str:
    """The closing marks needed for quotes or code spans left open in s."""
    marks = ""
    if len(re.findall(r"(?:^|[\s(/])'", s)) > len(re.findall(r"'(?=[\s.,;:!?)/]|$)", s)):
        marks += "'"
    if s.count('"') % 2:
        marks += '"'
    if s.count("`") % 2:
        marks += "`"
    return marks


def brief(s, limit: int) -> str:
    """Shorten to at most about `limit` characters, preferring a sentence end outside quotes."""
    s = clean(s)
    if len(s) <= limit:
        return s
    cut = s[:limit]
    ends = [m.end() for m in re.finditer(r"[.!?](?=\s)", cut) if not open_marks(cut[: m.end()])]
    if ends and ends[-1] >= limit * 0.55:
        return cut[: ends[-1]]
    sp = cut.rfind(" ")
    out = (cut[:sp] if sp > limit * 0.5 else cut).rstrip(" ,;:")
    return out + " …" + open_marks(out)


def plural(n: int, word: str, many: str | None = None) -> str:
    return f"{n} {word if n == 1 else (many or word + 's')}"


def and_list(items) -> str:
    items = [str(x) for x in items]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def md(s: str) -> str:
    """Escape '<' outside code spans so it is never read as HTML."""
    parts = s.split("`")
    for k in range(0, len(parts), 2):
        parts[k] = parts[k].replace("<", "&lt;")
    return "`".join(parts)


def cell(s: str) -> str:
    return md(s).replace("|", "\\|")


def smn(issues) -> tuple[int, int, int]:
    c = Counter(i.get("severity") for i in (issues or []))
    return c["must"], c["should"], c["nit"]


def fmt3(t) -> str:
    return "/".join(str(x) for x in t)


def add3(a, b):
    return tuple(x + y for x, y in zip(a, b))


def compress(ids, prefix: str = "g") -> str:
    ids = sorted(set(ids))
    out, k = [], 0
    while k < len(ids):
        j = k
        while j + 1 < len(ids) and ids[j + 1] == ids[j] + 1:
            j += 1
        if j - k >= 2:
            out.append(f"{prefix}{ids[k]}–{prefix}{ids[j]}")
        else:
            out.extend(f"{prefix}{x}" for x in ids[k : j + 1])
        k = j + 1
    return ", ".join(out)


def glist(ids) -> str:
    ids = sorted(set(ids))
    return ", ".join(f"g{i}" for i in ids) if ids else "none"


def row_label(a: str, i: int) -> str:
    return f"{a}{i}" if len(a) == 1 else f"{a}[{i}]"


def where_g(index, unit: str | None = None) -> str:
    if unit in ("perg1", "perg2"):
        return f"line {index}" if index not in (None, 0) else "parchment"
    if index == 1001:
        return "intro parchment"
    if index == 1002:
        return "ending parchment"
    if isinstance(index, str):
        return index
    return f"g{index}" if index is not None else "?"


def issue_line(i: dict, where: str, src: str | None = None) -> str:
    sev = i.get("severity", "?")
    tag = f" ({src})" if src else ""
    prob = brief(i.get("problem", ""), 150)
    fix = brief(i.get("fix", ""), 140)
    return f"- **{sev}** {where}{tag}: {md(prob)} *Fix:* {md(fix)}"


def rejection_line(r: dict, unit: str | None = None) -> str:
    idx = r.get("index")
    where = where_g(idx, unit) + " — " if idx not in (None, 0) else ""
    return f"- {where}**rejected:** {md(brief(r.get('issue', ''), 120))} **Reason:** {md(brief(r.get('reason', ''), 170))}"


def word_hunks(old: str, new: str, ctx: int = 1, width: int = 64):
    a, b = old.split(), new.split()
    ops = [o for o in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes() if o[0] != "equal"]
    spans: list[list[int]] = []
    for _, i1, i2, j1, j2 in ops:
        if spans and i1 - spans[-1][1] <= 2:
            spans[-1][1], spans[-1][3] = i2, j2
        else:
            spans.append([i1, i2, j1, j2])

    def short(s: str) -> str:
        if len(s) <= width:
            return s
        words, h = s.split(), width // 2 - 2
        head, tail = [], []
        while words and len(" ".join(head + words[:1])) <= h:
            head.append(words.pop(0))
        while words and len(" ".join(words[-1:] + tail)) <= h:
            tail.insert(0, words.pop())
        return " ".join(head) + " … " + " ".join(tail)

    out = []
    for i1, i2, j1, j2 in spans:
        pre, post = a[max(0, i1 - ctx) : i1], a[i2 : i2 + ctx]
        o = " ".join(pre + a[i1:i2] + post) or "∅"
        n = " ".join(pre + b[j1:j2] + post) or "∅"
        out.append((short(o), short(n)))
    return out


def hunks_text(old: str, new: str, maxh: int = 6) -> str:
    h = word_hunks(old, new)
    if not h:
        return "no change in the text"
    parts = [f"`{o}` → `{n}`" for o, n in h[:maxh]]
    more = f" (+{len(h) - maxh} more)" if len(h) > maxh else ""
    return "; ".join(parts) + more


def first_sentence(s: str, limit: int = 260) -> str:
    s = clean(s)
    m = re.search(r"^(.{40,}?[.!?])(?=\s|$)", s)
    return brief(m.group(1) if m else s, limit)


# ---------------------------------------------------------------------------- Phase C


def parse_c_label(label: str):
    p = label.split(":")
    if p[0] in ("translate", "nits", "finalfix") and len(p) == 2:
        return p[1], p[0], None
    if p[0] in ("edit", "backtr", "meaning", "revise") and len(p) == 3:
        return p[1], p[0], int(p[2][1:])
    if p[0] == "fix" and len(p) == 3:
        return p[1], "fix", int(p[2][2:])
    if re.fullmatch(r"perg\d", p[0]):
        if len(p) == 2:
            return p[0], p[1], None
        return p[0], p[1], int(p[2][1:])
    return None


def analyse_c(C: Journal, plan: list[dict]):
    units = [c["id"] for c in plan] + ["perg1", "perg2"]
    U = {u: {"rounds": defaultdict(dict), "state": None, "fix": {}} for u in units}
    for label, res in C.items:
        p = parse_c_label(label)
        if not p or p[0] not in U:
            continue
        u, step, rnd = p
        d = U[u]
        if step in ("edit", "meaning"):
            d["rounds"][rnd][step] = res.get("issues") or []
        elif step == "backtr":
            d["rounds"][rnd]["backtr"] = res.get("lines") or []
        elif step in ("translate", "revise", "nits", "fix", "finalfix"):
            if u.startswith("perg"):
                new = res.get("text", "")
            else:
                new = {int(r["index"]): r["sv"] for r in res.get("rows", [])}
            old = d["state"]
            if old is None:
                changed = None
            elif u.startswith("perg"):
                sm = difflib.SequenceMatcher(a=old.splitlines(), b=new.splitlines(), autojunk=False)
                changed = sum(max(i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal")
            else:
                changed = sorted(k for k in new if new[k] != old.get(k))
            d["state"] = new
            entry = {
                "label": label,
                "step": step,
                "round": rnd,
                "changed": changed,
                "rejected": res.get("rejected") or [],
                "check_errors": res.get("check_errors"),
                "summary": res.get("summary", ""),
            }
            if step == "revise":
                d["rounds"][rnd]["revise"] = entry
            elif step == "fix":
                d["fix"][rnd] = entry
            else:
                d[step] = entry
    return units, U


def changed_text(entry, unit: str) -> str:
    ch = entry["changed"]
    if unit.startswith("perg"):
        return f"{plural(ch, 'line')} changed" if ch else "no line changed"
    return f"{len(ch)} changed" if ch else "0 changed"


# ---------------------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--journals", type=Path, default=DEFAULT_JOURNALS)
    ap.add_argument("--out", type=Path, default=ROOT / "docs/TRANSLATION_REVIEW.md")
    ap.add_argument("--phasef", type=Path, default=ROOT / "work/phaseF/rereview_result.json")
    ap.add_argument("--x01", type=Path, default=ROOT / "work/phaseF/ui_review/x01_result.json")
    args = ap.parse_args()

    C = Journal(args.journals / WF_C / "journal.jsonl")
    E = Journal(args.journals / WF_E / "journal.jsonl")
    fj = args.journals / WF_F / "journal.jsonl"
    F = Journal(fj) if fj.exists() else None
    bj = args.journals / WF_B / "journal.jsonl"
    B = Journal(bj) if bj.exists() else None
    # work/ is git-ignored scratch. Each input taken from it has a fallback, so the record can
    # still be rebuilt from the journals and git after work/ is deleted.
    if args.phasef.exists():
        F_res = json.loads(args.phasef.read_text(encoding="utf-8"))
        phasef_src = f"`{args.phasef.relative_to(ROOT) if args.phasef.is_relative_to(ROOT) else args.phasef}`"
    else:
        hist = []
        for r in (1, 2, 3):
            ed, me = F.get(f"rereview:edit:r{r}") if F else None, F.get(f"rereview:meaning:r{r}") if F else None
            if not ed and not me:
                break
            iss = [dict(i, **{"from": "editor"}) for i in (ed or {}).get("issues", [])]
            iss += [dict(i, **{"from": "meaning"}) for i in (me or {}).get("issues", [])]
            hist.append({"round": r, **dict(zip(("must", "should", "nit"), smn(iss))), "issues": iss})
        if F and F.get("rereview:nits"):
            hist.append({"nits_applied": F.get("rereview:nits").get("summary", "")})
        last = [h for h in hist if "round" in h]
        F_res = {"clean": bool(last) and not (last[-1]["must"] or last[-1]["should"]), "history": hist}
        phasef_src = "rebuilt from the Phase F journal"

    tsv_now = load_tsv((ROOT / "translation/strings_sv.tsv").read_text(encoding="utf-8"))
    tsv_c = load_tsv(git_show(COMMIT_C, "translation/strings_sv.tsv") or "")
    tsv_e = load_tsv(git_show(COMMIT_E, "translation/strings_sv.tsv") or "")

    plan_path = ROOT / "work/phaseC/plan.json"
    if plan_path.exists():
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    else:  # the translators' first rows name each chunk's messages
        plan = [{"id": lab.split(":")[1], "rows": [["g", int(r["index"])] for r in res.get("rows", [])]}
                for lab, res in C.items if re.fullmatch(r"translate:[cu]\d+", lab)]
        plan.sort(key=lambda c: (c["id"].startswith("u"), c["id"]))
    chunk_rows = {c["id"]: sorted(int(i) for a, i in c["rows"] if a == "g") for c in plan}
    chunk_of = {i: cid for cid, ids in chunk_rows.items() for i in ids}
    ui_path = ROOT / "work/phaseC/chunks/ui.json"
    if ui_path.exists():
        ui = json.loads(ui_path.read_text(encoding="utf-8"))
        ui_src = "work/phaseC/chunks/ui.json"
    else:
        ui = {"rows": [{"array": a, "index": i, "sv": r["sv"]} for (a, i), r in tsv_c.items() if a != "g" or i == 0]}
        ui_src = f"the TSV at {COMMIT_C}"
    ui_keys = [(r["array"], int(r["index"])) for r in ui["rows"]]

    units, U = analyse_c(C, plan)
    g_units = [u for u in units if not u.startswith("perg")]

    def unit_of(idx):
        if idx == 1001:
            return "perg1"
        if idx == 1002:
            return "perg2"
        if isinstance(idx, str) and re.fullmatch(r"g\d+", idx):
            idx = int(idx[1:])
        return chunk_of.get(idx)

    # ------------------------------------------------------------ coverage checks
    used = sorted(i for (a, i), r in tsv_now.items() if a == "g" and r["context"].startswith("USED"))
    unused = sorted(i for (a, i), r in tsv_now.items() if a == "g" and r["context"].startswith("UNUSED"))
    c_ids = sorted(i for u in g_units if u != "u01" for i in chunk_rows[u])
    u_ids = chunk_rows["u01"]
    check(len(tsv_now) == 195, f"translation/strings_sv.tsv has {len(tsv_now)} rows (195 expected)")
    check(c_ids == used and len(used) == 143, f"chunks c01–c12 hold exactly the {len(used)} rows marked USED in the TSV")
    check(sorted(u_ids + [0]) == unused and len(u_ids) == 20, f"chunk u01 holds the {len(u_ids)} rows marked UNUSED, apart from g0 (in ui)")
    groups = [("g", i) for i in c_ids + u_ids] + ui_keys
    check(len(groups) == len(set(groups)) and set(groups) == set(tsv_now),
          f"every TSV row is in exactly one group ({len(c_ids)} + {len(u_ids)} + {len(ui_keys)} = {len(groups)})")

    files_ok = journal_c_ok = 0
    have_files = all((ROOT / f"work/phaseC/chunks/{u}.json").exists() for u in g_units)
    for u in g_units:
        st = U[u]["state"] or {}
        journal_c_ok += sum(1 for i in chunk_rows[u] if st.get(i) == tsv_c.get(("g", i), {}).get("sv"))
        if have_files:
            fc = json.loads((ROOT / f"work/phaseC/chunks/{u}.json").read_text(encoding="utf-8"))
            fs = {int(r["index"]): r["sv"] for r in (fc["rows"] if isinstance(fc, dict) else fc)}
            files_ok += sum(1 for i in chunk_rows[u] if st.get(i) == fs.get(i))
    if have_files:
        check(files_ok == 163, f"the last Phase C journal state equals work/phaseC/chunks/*.json for {files_ok}/163 g rows")
    check(journal_c_ok == 163, f"the last Phase C journal state equals the TSV at commit {COMMIT_C} (Phase C) for {journal_c_ok}/163 g rows")
    ui_now = sum(1 for r in ui["rows"] if tsv_now.get((r["array"], int(r["index"])), {}).get("sv") == r["sv"])
    ui_c = sum(1 for r in ui["rows"] if tsv_c.get((r["array"], int(r["index"])), {}).get("sv") == r["sv"])
    if ui_path.exists():
        check(ui_now == ui_c == len(ui_keys), f"the {len(ui_keys)} ui rows equal {ui_src} in the TSV at {COMMIT_C} ({ui_c}) and now ({ui_now})")
    else:
        check(ui_now == len(ui_keys), f"the {len(ui_keys)} ui rows are unchanged since {COMMIT_C} ({ui_now})")
    for n in (1, 2):
        fp = f"translation/pergamino{n}_sv.txt"
        now = (ROOT / fp).read_text(encoding="utf-8")
        st = U[f"perg{n}"]["state"] or ""
        then = git_show(COMMIT_C, fp)
        check(st.rstrip("\n") == now.rstrip("\n"), f"the last Phase C journal text of pergamino{n} equals {fp}")
        check(then is not None and then == now, f"{fp} is unchanged since commit {COMMIT_C} (Phase C)")

    diff_ce = sorted(i for (a, i) in tsv_e if a == "g" and tsv_e[(a, i)]["sv"] != tsv_c.get((a, i), {}).get("sv"))
    diff_en = sorted(i for (a, i) in tsv_now if a == "g" and tsv_now[(a, i)]["sv"] != tsv_e.get((a, i), {}).get("sv"))
    other_ce = [k for k in tsv_e if k[0] != "g" and tsv_e[k]["sv"] != tsv_c.get(k, {}).get("sv")]
    other_en = [k for k in tsv_now if k[0] != "g" and tsv_now[k]["sv"] != tsv_e.get(k, {}).get("sv")]
    check(diff_ce == CHANGED17 and not other_ce, f"the TSV diff {COMMIT_C} → {COMMIT_E} (Phase E) is exactly the 17 messages {glist(diff_ce)}")
    check(not other_en and set(diff_en) <= set(CHANGED17), f"since {COMMIT_E} only messages among the 17 changed ({glist(diff_en)})")
    for cmd, pat, what in (
        (["uv", "run", "tools/lint_strings.py", "translation/strings_sv.tsv"], r"(\d+) error\(s\)", "`lint_strings.py` on the current TSV"),
        (["uv", "run", "tools/check_glossary.py", "-q"], r"(\d+) errors", "`check_glossary.py -q` on the current TSV and parchments"),
    ):
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        m = re.findall(pat, p.stdout + p.stderr)
        tail = clean((p.stdout + p.stderr).strip().splitlines()[-1] if (p.stdout + p.stderr).strip() else "no output")
        check(p.returncode == 0 and bool(m) and m[-1] == "0", f"{what}: {tail}")

    # ------------------------------------------------------------ Phase C per-unit tables
    totals = {"edit": (0, 0, 0), "meaning": (0, 0, 0)}
    n_rounds = 0
    n_bt_lines = n_unclear = 0
    rej_review = 0
    table = []
    notes_after_table = []
    for u in units:
        d = U[u]
        rounds = sorted(d["rounds"])
        if u.startswith("perg"):
            n = int(u[-1])
            nlines = len((ROOT / f"translation/pergamino{n}_sv.txt").read_text(encoding="utf-8").splitlines())
            msgs = f"{PARCH_NAME[u]}, {nlines} lines"
        else:
            msgs = f"{compress(chunk_rows[u])} ({len(chunk_rows[u])})"
        for k, r in enumerate(rounds):
            rd = d["rounds"][r]
            e3, m3 = smn(rd.get("edit")), smn(rd.get("meaning"))
            totals["edit"] = add3(totals["edit"], e3)
            totals["meaning"] = add3(totals["meaning"], m3)
            n_rounds += 1
            bt = rd.get("backtr") or []
            unclear = sum(len(x.get("unclear") or []) for x in bt)
            n_bt_lines += len(bt)
            n_unclear += unclear
            if "revise" in rd:
                ent = rd["revise"]
                rej_review += len(ent["rejected"])
                then = f"revised: {changed_text(ent, u)}, {len(ent['rejected'])} rejected"
                if r == rounds[-1]:
                    then += f" (limit of {MAX_ROUNDS_C} rounds reached)" if r == MAX_ROUNDS_C else ""
            elif r == rounds[-1] and "nits" in d:
                ent = d["nits"]
                rej_review += len(ent["rejected"])
                then = f"nits pass: {changed_text(ent, u)}, {len(ent['rejected'])} rejected"
            else:
                then = "clean: no issues"
            first = k == 0
            table.append(
                f"| {u if first else ''} | {cell(msgs) if first else ''} | {r} | {fmt3(e3)} | {fmt3(m3)} | {len(bt)} ({unclear}) | {then} |"
            )
        last = d["rounds"][rounds[-1]]
        blocking = [i for i in (last.get("edit") or []) + (last.get("meaning") or []) if i.get("severity") != "nit"]
        if blocking:
            ent = last.get("revise")
            ff = d.get("finalfix")
            txt = (
                f"**{u}, round {rounds[-1]}:** {plural(len(blocking), 'blocking issue')} remained: "
                + "; ".join(f"{i['severity']}, {where_g(i.get('index'), u)}: {md(brief(i.get('problem', ''), 150))}" for i in blocking)
            )
            if ent and not ent["changed"]:
                txt += (f" The reviser changed nothing. In its words: “{md(brief(ent['summary'], 230))}”"
                        f" The {MAX_ROUNDS_C}-round limit then ended the loop.")
            if ff:
                txt += f" `{ff['label']}` resolved it after the whole-game passes ({changed_text(ff, u)}: {glist(ff['changed'])}; see §2.3)."
            notes_after_table.append(txt)
    unit_rounds = {u: len(U[u]["rounds"]) for u in units}
    by_rounds = defaultdict(list)
    for u, n in unit_rounds.items():
        by_rounds[n].append(u)

    # ------------------------------------------------------------ whole-game passes
    passes = []
    for cr in (1, 2):
        cons, player = C.get(f"consistency:r{cr}"), C.get(f"player:r{cr}")
        if not cons and not player:
            continue
        issues = [dict(i, src="consistency editor") for i in (cons or {}).get("issues", [])]
        issues += [dict(i, src="player") for i in (player or {}).get("issues", [])]
        for i in issues:
            i["unit"] = unit_of(i.get("index"))
            i["routed"] = cr == 1 or i.get("severity") != "nit"
        fixers = {u: U[u]["fix"][cr] for u in units if cr in U[u]["fix"]}
        routed_units = {i["unit"] for i in issues if i["routed"] and i["unit"]}
        check(routed_units == set(fixers),
              f"consistency pass {cr}: the units with routed issues ({len(routed_units)}) are exactly the units with a fixer step ({len(fixers)})")
        passes.append({"cr": cr, "cons": cons, "player": player, "issues": issues, "fixers": fixers})

    # ------------------------------------------------------------ Phase E
    crit = {}
    for label, res in E.items:
        m = re.fullmatch(r"critic:(\w+):r(\d)", label)
        if m:
            crit[(m.group(1), int(m.group(2)))] = res
    e_rounds = sorted({r for _, r in crit})
    efix = {r: E.get(f"fix:r{r}") for r in (1, 2, 3) if E.get(f"fix:r{r}")}
    r1_changed: list[int] = []
    vis2 = crit.get(("visual", 2)) or {}
    for item in vis2.get("checked", []):
        if "Diffed the Swedish column" in item:
            r1_changed = sorted(int(x) for x in re.findall(r"\bg(\d+)\b", item))
    r2_changed: list[int] = []
    s2 = (efix.get(2) or {}).get("summary", "")
    m = re.search(r"CHANGED\n(.*?)\n- docs/GLOSSARY", s2, re.S)
    if m:
        r2_changed = sorted({int(x) for x in re.findall(r"^\s*- g(\d+)\b", m.group(1), re.M)})
    m = re.search(r"exactly 17 g strings differ \(javap Utf8 diff\): ([g\d ]+)", s2)
    javap17 = sorted(int(x) for x in re.findall(r"g(\d+)", m.group(1))) if m else []
    check(sorted(set(r1_changed) | set(r2_changed)) == CHANGED17 == javap17,
          "Phase E: round 1 changes (critic:visual:r2, diff against HEAD) ∪ round 2 changes (fix:r2) = the fixer's javap diff of the jar = the 17 messages")

    def e_issue_gs(i):
        return sorted({int(x) for x in re.findall(r"\bg\[?(\d+)\]?", i.get("where", ""))})

    e_by_unit = defaultdict(list)  # unit -> [(round, lens, issue)]
    e_general = defaultdict(list)  # round -> [(lens, issue)]
    for (lens, r), res in sorted(crit.items(), key=lambda kv: (kv[0][1], LENSES.index(kv[0][0]) if kv[0][0] in LENSES else 9)):
        for i in res.get("issues", []):
            gs = e_issue_gs(i)
            if i.get("area") == "translation" and len(gs) == 1 and gs[0] in chunk_of:
                e_by_unit[chunk_of[gs[0]]].append((r, lens, i, gs[0]))
            else:
                e_general[r].append((lens, i))

    # ------------------------------------------------------------ Phase F
    f_hist = [h for h in F_res.get("history", []) if "round" in h]
    f_nits_text = next((h["nits_applied"] for h in F_res.get("history", []) if "nits_applied" in h), "")
    f_rounds = []
    for h in f_hist:
        r = h["round"]
        ed = [i for i in h["issues"] if i.get("from") == "editor"]
        me = [i for i in h["issues"] if i.get("from") == "meaning"]
        bt = (F.get(f"rereview:backtr:r{r}") or {}).get("lines", []) if F else []
        if F and args.phasef.exists():
            j_issues = [dict(i, **{"from": "editor"}) for i in (F.get(f"rereview:edit:r{r}") or {}).get("issues", [])]
            j_issues += [dict(i, **{"from": "meaning"}) for i in (F.get(f"rereview:meaning:r{r}") or {}).get("issues", [])]
            check(j_issues == h["issues"], f"Phase F round {r}: the issues in {phasef_src} equal rereview:edit/meaning:r{r} in the Phase F journal")
        blocking = [i for i in h["issues"] if i.get("severity") != "nit"]
        if blocking:
            rev = (F.get(f"rereview:revise:r{r}") if F else None) or {}
            kind = "revised"
        else:
            rev = (F.get("rereview:nits") if F else None) or {"summary": f_nits_text, "rejected": []}
            kind = "nits pass"
        summ = rev.get("summary", "")
        rejected = rev.get("rejected") or []
        mm = re.search(r"Only (?:[a-z]+ rows changed: )?(g\d+(?:(?:, | and )g\d+)*)", summ)
        if mm:
            changed = sorted(int(x) for x in re.findall(r"g(\d+)", mm.group(1)))
            how = "as the reviser lists them"
        else:
            rej_msgs = {m2 for x in rejected for m2 in re.findall(r"g\d+", x.get("issue", ""))[:1]}
            changed = sorted({int(i["index"][1:]) for i in h["issues"] if i["index"] not in rej_msgs})
            how = "the messages of the accepted issues; the reviser accepted all"
        f_rounds.append({"round": r, "ed": ed, "me": me, "bt": bt, "kind": kind, "changed": changed, "how": how,
                         "rejected": rejected, "summary": summ})
    f_union = sorted({i for fr in f_rounds for i in fr["changed"]})
    check(f_union == diff_en, f"Phase F: the messages its revisions changed ({glist(f_union)}) equal the TSV diff {COMMIT_E} → working tree ({glist(diff_en)})")

    # ------------------------------------------------------------ Phase F final verification (unit x01)
    X = json.loads(args.x01.read_text(encoding="utf-8")) if args.x01.exists() else None
    x_rel = args.x01.relative_to(ROOT) if args.x01.is_relative_to(ROOT) else args.x01
    x_keys: list[tuple[str, int]] = []
    if check(X is not None, f"the Phase F final-verification record {x_rel} exists"):
        x_keys = [(r["array"], int(r["index"])) for r in X["rows"]]
        x_same = sum(1 for r in X["rows"] if tsv_now.get((r["array"], int(r["index"])), {}).get("sv") == r["sv"])
        check(x_same == len(X["rows"]), f"unit x01: {x_same}/{len(X['rows'])} reviewed rows equal the current TSV")
        x_expect = sorted(k for k in ui_keys if k not in (("g", 0), ("E.h", 4))) + [("g", 61), ("g", 64), ("g", 149)]
        check(sorted(x_keys) == sorted(x_expect),
              f"unit x01 holds every ui row but g0 and E.h[4] ({len(x_expect) - 3}), plus g61, g64 and g149")
        x_bt = X["backtr"]["items"]
        x_nonempty = [row_label(a, i) for (a, i) in x_keys if tsv_now[(a, i)]["sv"].strip()]
        x_bt_ids = [{"w.t": "w.t[4]", "w.u": "w.u[4]"}.get(b["id"], b["id"]) for b in x_bt]
        check(x_bt_ids == x_nonempty, f"unit x01: the blind back-translation covers the {len(x_nonempty)} non-empty rows, in order")
        x_flags = sum(len(b.get("unclear") or []) for b in x_bt)
        check(x_flags == len(X["meaning"]["judged_unclear"]),
              f"unit x01: the meaning check judged all {x_flags} segments the back-translator flagged")

    # ======================================================================== write
    o: list[str] = []
    w = o.append
    tot_c_issues = add3(totals["edit"], totals["meaning"])
    n_wg = [smn(p["issues"]) for p in passes]
    n_fix_rej = sum(len(f["rejected"]) for p in passes for f in p["fixers"].values())
    f_tot = (sum(h["must"] for h in f_hist), sum(h["should"] for h in f_hist), sum(h["nit"] for h in f_hist))
    all_ok = all(ok for ok, _ in CHECKS)

    w("# Translation review record")
    w("")
    w("> Generated by `uv run tools/review_record.py` from the workflow journals. Do not edit by hand:")
    w("> change the script and rerun it.")
    w("")
    w("The brief's definition of done asks that every one of the 185 strings and both parchments")
    w('"have passed the editor, back-translation and consistency passes". This file is the on-disk')
    w("record of those passes: what each pass looked at, how many rounds it took, what it found, what")
    w("was changed, and every rejected suggestion with its reason. `docs/DECISIONS.md` D17 summarises")
    w("it. The texts themselves are `translation/strings_sv.tsv` (each row's note records its")
    w("decisions) and `translation/pergamino{1,2}_sv.txt`.")
    w("")
    w("**In short**")
    w("")
    w(f"- **Per-unit loop (Phase C).** The 163 `g` messages were split into 13 chunks, and each parchment was its own unit:"
      f" {len(units)} units in all. Every unit got an editor pass, a blind back-translation and a meaning check in every"
      f" round. Rounds repeated until a round had no must or should issue, then a last pass handled the remaining nits."
      f" That took {n_rounds} rounds in all. The passes raised {sum(tot_c_issues)} issues (must/should/nit"
      f" {fmt3(tot_c_issues)}), and {rej_review} were rejected with a reason.")
    w(f"- **UI rows.** The {len(ui_keys)} fixed UI rows (`g0`, the `a c d e f` strings, the 7 HUD hours `b`, and `w.t`, `w.u`, `E.h`)"
      " were settled in the glossary in Phase B and copied from it. They were not translated in chunks (§1.4).")
    w(f"- **Whole-game passes.** Two whole-game passes followed (consistency editor and Swedish-only player), raising"
      f" {fmt3(n_wg[0])} and {fmt3(n_wg[1])} issues (must/should/nit). Per-unit fixers applied them or rejected them"
      f" with a reason ({n_fix_rej} rejected).")
    w(f"- **Phase E.** A four-lens critic panel reviewed the built game, including every rendered page, in {len(e_rounds)} rounds."
      f" Its fixers changed 17 messages, mostly to move page breaks.")
    w(f"- **Phase F.** Those 17 messages went through the editor, back-translation and meaning loop again in {len(f_hist)}"
      f" rounds ({fmt3(f_tot)} must/should/nit issues). The loop ended clean: **{'yes' if F_res.get('clean') else 'no'}**.")
    if X:
        x_ed, x_me = smn(X["editor"]["issues"]), smn(X["meaning"]["issues"])
        w(f"- **Phase F final verification.** One more unit (x01) put the UI rows that have text, and the final wording of"
          f" g61, g64 and g149, through an editor pass, a blind back-translation and a meaning check (editor {fmt3(x_ed)},"
          f" meaning {fmt3(x_me)} must/should/nit). It ended clean in {plural(X['outcome']['rounds'], 'round')}"
          f" and changed {'no row' if not X['outcome']['changed'] else ', '.join(X['outcome']['changed'])} (§3.4).")
    w(f"- **Cross-checks.** The script ran {len(CHECKS)} cross-checks against the project files and git: "
      + ("**all pass**." if all_ok else f"**{sum(1 for ok, _ in CHECKS if not ok)} FAILED**, see §0.") )
    w("")

    # ---- §0 sources
    w("## 0. Sources and cross-checks")
    w("")
    w("| Phase | Workflow | Agent results read | Notes |")
    w("|---|---|---|---|")
    jdir = "~/" + str(args.journals.relative_to(Path.home())) if args.journals.is_relative_to(Path.home()) else str(args.journals)

    def jnote(j: Journal | None) -> str:
        if not j:
            return "journal not found"
        bits = []
        if j.relaunched:
            bits.append(f"{len(j.relaunched)} agents relaunched under the same label (the relaunch's result is used): " + ", ".join(f"`{x}`" for x in j.relaunched))
        if j.no_result:
            bits.append("no result when this file was generated: " + ", ".join(f"`{x}`" for x in j.no_result))
        return "; ".join(bits) or "–"

    if B:
        w(f"| B, glossary | `{WF_B}` | {len(B.items)} | counts only (§1.4) |")
    w(f"| C, translation | `{WF_C}` | {len(C.items)} | {jnote(C)} |")
    w(f"| E, verification | `{WF_E}` | {len(E.items)} | {jnote(E)} |")
    w(f"| F, re-review | `{WF_F}` | {len(F.items) if F else 0} | the re-review result: {phasef_src}; {jnote(F)} |")
    w("")
    w(f"Journals: `{jdir}/<workflow>/journal.jsonl`. These are Claude Code session files outside the")
    w("project. They are not in git and may be cleaned up, which is why this record exists. The other")
    w("inputs are: `work/phaseC/plan.json` (chunk → messages); `work/phaseC/chunks/*.json`;")
    w(f"`translation/strings_sv.tsv` at commit `{COMMIT_C}` (end of Phase C), at `{COMMIT_E}` (end of Phase E) and in the")
    w("working tree (after Phase F); and the two parchment files.")
    w("")
    w("Cross-checks:")
    w("")
    for ok, text in CHECKS:
        w(f"- {'PASS' if ok else '**FAIL**'}: {md(text)}")
    w("")

    # ---- §1
    w("## 1. Per-unit passes and coverage")
    w("")
    w("### 1.1 Every row accounted for")
    w("")
    ui_by_arr = defaultdict(list)
    for a, i in ui_keys:
        ui_by_arr[a].append(i)
    ui_desc = ", ".join(
        (compress(v, a) if len(a) == 1 and len(v) > 1 else ", ".join(row_label(a, i) for i in sorted(v)))
        for a, v in ui_by_arr.items()
    )
    w("| Group | Rows | Count | Review route |")
    w("|---|---|---|---|")
    w(f"| c01–c12 | the `g` messages the game shows (context USED) | {len(c_ids)} | Phase C per-unit loop (§1.3), whole-game passes (§2), Phase E critics |")
    w(f"| u01 | `g` messages the game never shows (context UNUSED) | {len(u_ids)} | Phase C per-unit loop (§1.3), Phase E critics |")
    w(f"| ui | {ui_desc} | {len(ui_keys)} | fixed in GLOSSARY §5.1 and §6 (Phase B, §1.4), Phase E critics"
      + (", Phase F final-verification unit x01 (§3.4; all but g0 and E.h[4])" if X else "") + " |")
    w(f"| **all rows of `translation/strings_sv.tsv`** | | **{len(groups)}** | |")
    for u in ("perg1", "perg2"):
        n = int(u[-1])
        nl = len((ROOT / f"translation/pergamino{n}_sv.txt").read_text(encoding="utf-8").splitlines())
        w(f"| {u} | {PARCH_NAME[u]} | {nl} lines | Phase C per-unit loop (§1.3), player pass (§2), Phase E critics |")
    w("")
    w("The 195 TSV rows are the brief's 185 strings (`a` 4, `c` 2, `d` 2, `e` 3, `f` 10, `g` 164) plus the 7 HUD")
    w("hour names (`b`) and the three slot-4 strings outside `abadia.k` (`w.t`, `w.u`, `E.h`).")
    w("")
    w("### 1.2 How each unit was reviewed")
    w("")
    w("- **Translation** (`translate:<unit>`): a translator worked from the Spanish, using en/fr/it only for meaning, and followed")
    w("  the glossary.")
    w("- **Each round** ran two passes in parallel:")
    w("  - **Editor** (`edit:<unit>:rN`): a Swedish editor read the Swedish against the Spanish. It checked")
    w("    correctness, idiom, register, glossary use, forms of address, length and paging, and the markers.")
    w("  - **Blind back-translation** (`backtr:<unit>:rN`), then a **meaning check** (`meaning:<unit>:rN`). A separate agent")
    w("    saw only the Swedish lines, with no files, no commands and no web. It translated them literally into")
    w("    English, marking NI and DU, and listed whatever read as unclear. The meaning checker compared that")
    w("    back-translation with the Spanish (en/fr/it where useful). It looked for omissions, additions, changed facts,")
    w("    shifts in tone or address, and lost player information, and it judged every segment flagged as unclear.")
    w("- **Revision** (`revise:<unit>:rN`): if either pass had a must or should, a reviser fixed each right issue,")
    w("  rejected each wrong one with a reason, and the next round began. The next round's reviewers saw those")
    w("  rejections and could raise an issue again if the reason did not hold.")
    w("- **Nits pass** (`nits:<unit>`): when a round had no must or should, this last pass applied the nits it")
    w(f"  agreed with and rejected the others with a reason. The limit was {MAX_ROUNDS_C} rounds.")
    w("- **Severity:** *must* means wrong: ungrammatical, wrong meaning, a broken rule or glossary form,")
    w("  wrong address, or lost player information. *should* means clearly unidiomatic, stiff or off-register,")
    w("  a noticeable shift in nuance, or a poor page cut. *nit* means a small preference.")
    w("- **Deviation from the brief:** the brief asks for a back-translation into Spanish. The")
    w("  back-translator wrote literal English instead, and the meaning checker compared that with the Spanish.")
    w("")
    w("### 1.3 Summary per unit and round")
    w("")
    w("Issue counts are must/should/nit. *Back-translation* gives the lines back-translated (messages,")
    w("or paragraphs for the parchments) and, in brackets, how many segments the back-translator flagged as")
    w("unclear. *Then* says what followed the round and how many messages it changed (lines, for a")
    w("parchment).")
    w("")
    w("| Unit | Messages (count) | Round | Editor | Meaning | Back-translation | Then |")
    w("|---|---|---|---|---|---|---|")
    o.extend(table)
    w(f"| **all** | **163 `g` + 2 parchments** | **{n_rounds}** | **{fmt3(totals['edit'])}** | **{fmt3(totals['meaning'])}** | **{n_bt_lines} ({n_unclear})** | **{rej_review} rejected** |")
    w("")
    w("Rounds per unit: " + "; ".join(f"{n} for {', '.join(sorted(v))}" for n, v in sorted(by_rounds.items())) + ".")
    w("Every unit's final round had no must or should, with the exception below.")
    w("")
    for t in notes_after_table:
        w(t)
        w("")
    w("### 1.4 The fixed UI rows (Phase B)")
    w("")
    w(f"The {len(ui_keys)} UI rows ({ui_desc}) were not translated in chunks. The work file")
    w("`work/phaseC/chunks/ui.json` copies them from GLOSSARY §5.1 (HUD hours) and §6 (menu, end screen, save")
    w("labels, window title). D8 and D9 settle `NATTBÖN` and the empty `f[5]`. The glossary itself went")
    w(f"through the Phase B loop (`{WF_B}`): a draft, then three rounds of two critic lenses, a Swedish-language")
    w("critic and a constraints critic. The constraints critic was a localisation QA lens. Its remit included")
    w("these rows: each HUD hour exactly 7 drawable cells, menu label plus value ≤ 23 glyphs, end-screen")
    w("lines ≤ 40, the leading space of `a[1]` and the trailing space of `w.t`, all verified by computing the")
    w("counts. Each round ended with a revision that applied every must and should. GLOSSARY §12 lists the")
    w("suggestions taken only in part, with reasons.")
    if B:
        w("Issue counts over the whole glossary (must/should/nit):")
        w("")
        w("| Round | Swedish-language critic | Constraints critic |")
        w("|---|---|---|")
        for r in (1, 2, 3):
            sw = (B.get(f"critic:swedish:r{r}") or {}).get("issues")
            cs = (B.get(f"critic:constraints:r{r}") or {}).get("issues")
            if sw is None and cs is None:
                continue
            w(f"| {r} | {fmt3(smn(sw))} | {fmt3(smn(cs))} |")
        w("")
    w("These rows got no blind back-translation in Phases B and C, and the Phase C whole-game passes read only")
    w("`g`. They were read rendered and live by the Phase E language critic in every round (§3.1).")
    if X:
        w("The Phase F final verification then gave every one of them that has text an editor pass, a blind")
        w("back-translation and a meaning check, including their consistency with the rest of the game (§3.4).")
    w("")

    # ---- §2
    w("## 2. The two whole-game passes")
    w("")
    w("Each pass ran two readers in parallel over the merged table:")
    w("")
    w("- **Consistency editor** (`consistency:rN`): read every message in game order with es and sv, both")
    w("  parchments and the translators' GLOSSARY GAP notes. It checked that a term, name or recurring phrase is")
    w("  rendered the same way everywhere, address per speaker pair, each character's voice, references and")
    w("  facts between messages, the hint chain, and repeated scenes.")
    w("- **Swedish-only player** (`player:rN`): read only the Swedish, in game order, plus both parchments.")
    w("  It had no other language, no docs and no glossary, and reported whatever would bother a Swedish")
    w("  player.")
    w("")
    w("Issues were routed to a fixer per unit (`fix:<unit>:crN`), which applied each one or rejected it with")
    w("a reason. Pass 1 routed every issue; pass 2 routed only must and should, so its nits were recorded but")
    w("not acted on (they are marked *not routed* in the appendix).")
    w("")
    w("| Pass | Consistency editor | Player | Routed to fixers | Fixer steps | Messages changed | Rejected |")
    w("|---|---|---|---|---|---|---|")
    for p in passes:
        routed = [i for i in p["issues"] if i["routed"]]
        not_routed = len(p["issues"]) - len(routed)
        ch = sorted({i for u, f in p["fixers"].items() if not u.startswith("perg") for i in (f["changed"] or [])})
        perg_ch = [u for u, f in p["fixers"].items() if u.startswith("perg") and f["changed"]]
        rej = sum(len(f["rejected"]) for f in p["fixers"].values())
        ch_txt = f"{len(ch)} `g`" + (f" + {', '.join(perg_ch)}" if perg_ch else "")
        w(f"| {p['cr']} | {fmt3(smn((p['cons'] or {}).get('issues')))} | {fmt3(smn((p['player'] or {}).get('issues')))} |"
          f" {len(routed)}" + (f" ({not_routed} nits not routed)" if not_routed else "") +
          f" | {len(p['fixers'])} | {ch_txt} | {rej} |")
    w("")
    w("### 2.1 What the passes found")
    w("")
    mismatches = []
    for p in passes:
        for key, who in (("cons", "Consistency editor"), ("player", "Player")):
            res = p[key]
            if not res:
                continue
            verdict = res.get("verdict", "")
            para = re.split(r"\n\s*\n|\s\(1\)|\s1\. ", verdict.strip())[0].strip()
            if para.endswith(":") and ". " in para:
                para = para[: para.rfind(". ") + 1]
            w(f"- **{who}, pass {p['cr']}:** {md(brief(para, 420))}")
            m = re.search(r"(\d+) problems: (\d+) must, (\d+) should, (\d+) nit", verdict)
            listed = smn(res.get("issues"))
            if m and (int(m.group(1)), tuple(int(x) for x in m.group(2, 3, 4))) != (sum(listed), listed):
                mismatches.append(f"the {who.lower()}'s pass-{p['cr']} verdict says {m.group(1)} problems"
                                  f" ({m.group(2)}/{m.group(3)}/{m.group(4)}), but its issue list holds {sum(listed)} ({fmt3(listed)})")
    w("")
    if mismatches:
        w("All counts in this record come from the issue lists themselves. Where a verdict's own count differs: "
          + "; ".join(mismatches) + ".")
        w("")
    w("### 2.2 What was changed")
    w("")
    for p in passes:
        w(f"Pass {p['cr']}:")
        w("")
        for u in units:
            f = p["fixers"].get(u)
            if not f:
                continue
            iss = [i for i in p["issues"] if i["routed"] and i["unit"] == u]
            if u.startswith("perg"):
                ch = changed_text(f, u)
            else:
                ch = ("changed " + glist(f["changed"])) if f["changed"] else "changed nothing"
            w(f"- `{f['label']}`: {plural(len(iss), 'issue')} ({fmt3(smn(iss))}); {ch}; {len(f['rejected'])} rejected.")
        w("")
    musts = [(p["cr"], i) for p in passes for i in p["issues"] if i.get("severity") == "must"]
    if musts:
        w("The must issues and their outcome:")
        w("")
        for cr, i in musts:
            u = i["unit"]
            f = passes[cr - 1]["fixers"].get(u) if u else None
            rej = [r for r in (f["rejected"] if f else []) if r.get("index") == i.get("index")]
            if rej:
                outcome = "rejected: " + md(brief(rej[0].get("reason", ""), 260))
            elif f and i.get("index") in (f["changed"] or []):
                outcome = "applied (the message changed)"
            else:
                outcome = "not changed"
            w(f"- Pass {cr}, {i['src']}, {where_g(i.get('index'))}: {md(brief(i.get('problem', ''), 160))} Outcome: {outcome}")
        w("")
    w("### 2.3 Final checks")
    w("")
    for lab in ("final-check", "final-check-2"):
        fc = C.get(lab)
        if not fc:
            continue
        w(f"- `{lab}`: lint {fc.get('lint_errors')} errors, `check_glossary.py` {fc.get('glossary_errors')} errors"
          f" (rows with errors: {glist(fc.get('error_rows') or [])}). pergamino1 {fc.get('perg1_pages')} pages, ink edge {fc.get('perg1_max_ink')};"
          f" pergamino2 {fc.get('perg2_pages')} pages, ink edge {fc.get('perg2_max_ink')}. Swedish length {fc.get('length_growth_percent')} % against es.")
        if lab == "final-check":
            ff = U["c11"].get("finalfix")
            if ff:
                w(f"- `{ff['label']}`: {changed_text(ff, 'c11')} ({glist(ff['changed'])}), {len(ff['rejected'])} rejected. {md(brief(ff['summary'], 420))}")
    w("")
    w("No Phase C pass saw the `finalfix:c11` change to g127. The Phase E language critic read it.")
    w("")

    # ---- §3
    w("## 3. Phase E rendered-text review and the Phase F re-review")
    w("")
    w("### 3.1 Phase E critic panel")
    w("")
    w(f"Phase E (`{WF_E}`) verified the built game. Four critics, each with its own lens, reviewed it in up to three")
    w("rounds. The **language** critic read the Swedish as the player sees it. The **visual** critic checked")
    w("glyphs, images and layout. The **completeness** critic checked the brief, build and strings. The **runs**")
    w("critic checked the runtime evidence. After rounds 1 and 2, a fixer acted on every must and should and on")
    w("the trivial nits. The panel stopped after round 3, which got no fixer. Counts are must/should/nit; the")
    w("*translation* column counts the issues whose area is the translation.")
    w("")
    w("| Round | Language | Visual | Completeness | Runs | Of which translation | Fixer |")
    w("|---|---|---|---|---|---|---|")
    for r in e_rounds:
        all_i = [i for lens in LENSES for i in (crit.get((lens, r)) or {}).get("issues", [])]
        tr = [i for i in all_i if i.get("area") == "translation"]
        fx = efix.get(r)
        if fx:
            chg = r1_changed if r == 1 else r2_changed if r == 2 else []
            fx_txt = f"`fix:r{r}`: changed {glist(chg)}"
        else:
            fx_txt = "none (last round)"
        w(f"| {r} | " + " | ".join(fmt3(smn((crit.get((lens, r)) or {}).get("issues"))) for lens in LENSES) + f" | {fmt3(smn(tr))} | {fx_txt} |")
    w("")
    for r in e_rounds:
        lang = crit.get(("language", r))
        if lang:
            w(f"- **Language critic, round {r}:** {md(brief(lang.get('summary', ''), 420))}")
    w("")
    w("Translation issues the critics raised (the whole text of each is in the appendix):")
    w("")
    for r in e_rounds:
        for lens in LENSES:
            for i in (crit.get((lens, r)) or {}).get("issues", []):
                if i.get("area") != "translation":
                    continue
                gs = e_issue_gs(i)
                w(f"- r{r} {lens}, **{i.get('severity')}**, {glist(gs) if gs else md(brief(i.get('where', ''), 60))}: {md(brief(i.get('problem', ''), 150))}")
    w("")
    w(f"The round-1 fixer changed {len(r1_changed)} messages ({glist(r1_changed)}). The round-2 fixer changed {len(r2_changed)} ({glist(r2_changed)}).")
    both = sorted(set(r1_changed) & set(r2_changed))
    w(f"{and_list('g' + str(x) for x in both)} changed in both rounds, so 17 messages changed in all. Each change answers one of the issues")
    w("above. A page break moved, or a sentence was shortened or reworded (g64, g85 and g163 most visibly). The")
    w("aim was that no page cuts a clause and that line 2 stays clear of the blinking ▶▶ marker, which hides its")
    w("35th glyph. §3.3 shows each change word by word.")
    r3_tr = [i for lens in LENSES for i in (crit.get((lens, 3)) or {}).get("issues", []) if i.get("area") == "translation"]
    r3_record = [i for i in r3_tr if i.get("severity") != "nit" and "work/phaseC" in i.get("where", "")]
    r3_other_block = [i for i in r3_tr if i.get("severity") != "nit" and i not in r3_record]
    w(f"In round 3, the only translation must or should issues were {len(r3_record)} repeats of the missing-record issue"
      + (f" and {len(r3_other_block)} others" if r3_other_block else "; no message was faulted above nit level")
      + ". Round 3 had no fixer, so its translation nits were not routed:")
    w("")
    for lens in LENSES:
        for i in (crit.get((lens, 3)) or {}).get("issues", []):
            if i.get("area") == "translation" and i.get("severity") == "nit":
                gs = e_issue_gs(i)
                w(f"- {lens}, {glist(gs)}: {md(brief(i.get('problem', ''), 200))} *Fix:* {md(brief(i.get('fix', ''), 120))}"
                  + (" (Phase F re-reviewed " + glist(sorted(set(gs) & set(CHANGED17))) + ")" if set(gs) & set(CHANGED17) else ""))
    w("")
    rec_rounds = sorted({r for (lens, r), res in crit.items() for i in res.get("issues", [])
                         if i.get("area") == "translation" and "work/phaseC" in i.get("where", "")})
    w(f"Each of rounds {and_list(rec_rounds)} raised a should that the Phase C passes had no on-disk record.")
    w("This file answers it, together with D17.")
    w("")
    w("### 3.2 The Phase F re-review of the 17 messages")
    w("")
    w(f"Phase F (`{WF_F}`) ran the 17 messages through the Phase C loop again. Each round had an editor, a blind")
    w("back-translation into English by an agent that saw only the Swedish, and a meaning check against the")
    w("Spanish. A revision followed while must or should issues remained, then a nits pass. The reviewers saw")
    w("the previous round's rejections.")
    w("")
    w("| Round | Editor | Meaning | Back-translation | Then |")
    w("|---|---|---|---|---|")
    for fr in f_rounds:
        unclear = sum(len(x.get("unclear") or []) for x in fr["bt"])
        w(f"| {fr['round']} | {fmt3(smn(fr['ed']))} | {fmt3(smn(fr['me']))} | {len(fr['bt'])} ({unclear}) |"
          f" {fr['kind']}: changed {glist(fr['changed'])}; {len(fr['rejected'])} rejected |")
    w("")
    w(f"Outcome: the loop ended **{'clean' if F_res.get('clean') else 'not clean'}**: round {f_rounds[-1]['round'] if f_rounds else '?'} had no must or should.")
    w("The round-3 nits were applied after the last review round, so no reviewer of this loop read the result. The nits")
    w("pass reports: “" + md(brief(f_nits_text, 300)) + "” The cross-checks in §0 run the lint and")
    w("`check_glossary.py` on the current text."
      + (" The Phase F final verification then reviewed the final text of g61, g64 and g149 (§3.4)." if X else ""))
    w(f"The messages changed in Phase F ({glist(f_union)}) are exactly the TSV diff `{COMMIT_E}` → working tree.")
    w("")
    w("### 3.3 The 17 messages, one by one")
    w("")
    f_iss_by_msg = defaultdict(lambda: defaultdict(list))
    for h in f_hist:
        for i in h["issues"]:
            f_iss_by_msg[int(i["index"][1:])][h["round"]].append(i)
    w("| Message | Unit | Changed in Phase E | Phase F issues, round 1 · 2 · 3 (must/should/nit) | Changed in Phase F |")
    w("|---|---|---|---|---|")
    for g in CHANGED17:
        er = ("r1" if g in r1_changed else "") + (" + " if g in r1_changed and g in r2_changed else "") + ("r2" if g in r2_changed else "")
        fi = " · ".join(fmt3(smn(f_iss_by_msg[g].get(r, []))) if f_iss_by_msg[g].get(r) else "–" for r in (1, 2, 3))
        fc = [str(fr["round"]) if fr["kind"] == "revised" else "nits" for fr in f_rounds if g in fr["changed"]]
        w(f"| g{g} | {chunk_of[g]} | {er} | {fi} | {('yes (' + ', '.join(fc) + ')') if fc else 'no'} |")
    w("")
    w("What changed, as word-level differences (Phase C → Phase E, then Phase E → now; `_` is a page break):")
    w("")
    for g in CHANGED17:
        c_sv = tsv_c[("g", g)]["sv"]
        e_sv = tsv_e[("g", g)]["sv"]
        n_sv = tsv_now[("g", g)]["sv"]
        line = f"- **g{g}** ({chunk_of[g]}). Phase E: {md(hunks_text(c_sv, e_sv))}."
        if n_sv != e_sv:
            line += f" Phase F: {md(hunks_text(e_sv, n_sv))}."
        w(line)
    w("")

    # ---- §3.4 Phase F final verification, unit x01
    if X:
        w("### 3.4 Phase F final verification: the UI rows and the round-3 nits (unit x01)")
        w("")
        w(md(clean(X["why"])) + f" The Phase F final verification ({md(clean(X['label']))}) closed both gaps with one")
        w(f"more unit, `{X['chunk_file']}`, run like a Phase C round.")
        w("")
        x_ui = [k for k in x_keys if k[0] != "g"]
        x_by_arr = defaultdict(list)
        for a, i in x_ui:
            x_by_arr[a].append(i)
        x_desc = ", ".join((compress(v, a) if len(a) == 1 and len(v) > 1 else ", ".join(row_label(a, i) for i in sorted(v)))
                           for a, v in x_by_arr.items())
        nb = X["not_back_translated"]
        w(f"- **Rows ({len(x_keys)}):** {x_desc} ({len(x_ui)} UI rows) and g61, g64, g149. f5 is in the unit but has no text:"
          f" {md(clean(nb['f5']))}. g0 and E.h[4] are not in it: {md(clean(nb['g0']))}; {md(clean(nb['E.h4']))}.")
        w(f"- **Editor:** {md(clean(X['editor']['by']))}.")
        w(f"- **Blind back-translation:** {md(clean(X['backtr']['by']))} Prompt and raw answer:"
          f" `{X['backtr']['prompt_file']}`, `{X['backtr']['output_file']}`.")
        w(f"- **Meaning check:** {md(clean(X['meaning']['by']))}.")
        w("- **Deviation from the Phase C setup:** the editor and the meaning checker were one agent, and it had")
        w("  read the earlier review records. Only the back-translator was a separate, blind reader.")
        w("")
        x_bt = X["backtr"]["items"]
        x_unc = sum(len(b.get("unclear") or []) for b in x_bt)
        x_ch = X["outcome"]["changed"]
        w("| Round | Editor | Meaning | Back-translation | Then |")
        w("|---|---|---|---|---|")
        w(f"| 1 | {fmt3(smn(X['editor']['issues']))} | {fmt3(smn(X['meaning']['issues']))} | {len(x_bt)} ({x_unc}) |"
          f" {'clean: no revision and no nits pass' if X['outcome']['clean'] else 'not clean'}; changed {', '.join(x_ch) if x_ch else 'nothing'} |")
        w("")
        w(f"**Editor.** {md(clean(X['editor']['summary']))}")
        w("")
        w("**Back-translation of the UI rows** (the Swedish as stored, quotes showing any edge spaces; then the")
        w("back-translator's English):")
        w("")
        w("| Row | Swedish | Back-translation |")
        w("|---|---|---|")
        sv_of = {row_label(r["array"], int(r["index"])): r["sv"] for r in X["rows"]}
        for b in x_bt:
            rid = {"w.t": "w.t[4]", "w.u": "w.u[4]"}.get(b["id"], b["id"])
            if rid.startswith("g"):
                continue
            w(f"| {rid} | `\"{sv_of[rid]}\"` | {cell(b['english'])} |")
        w("")
        w("**Back-translation of g61, g64 and g149:**")
        w("")
        for b in x_bt:
            if b["id"].startswith("g"):
                w(f"- **{b['id']}:** {md(clean(b['english']))}")
        w("")
        w(f"**Meaning check.** It raised {fmt3(smn(X['meaning']['issues']))} must/should/nit. The {x_unc} segments the")
        w("back-translator flagged, as judged:")
        w("")
        for j in X["meaning"]["judged_unclear"]:
            w(f"- {j['id']} `{j['segment']}`. *Flag:* {md(clean(j['flag']))}. **{j['verdict'].capitalize()}:** {md(clean(j['reason']))}")
        w("")
        w("Other differences from es that the meaning check weighed and accepted:")
        w("")
        for d in X["meaning"]["differences_checked"]:
            w(f"- {md(clean(d))}")
        w("")
        w(f"**Outcome.** {md(clean(X['outcome']['summary']))}")
        w("")

    # ---- Appendix A
    w("## Appendix A. Every issue and rejection, by unit")
    w("")
    w("Each entry gives the severity, the message (or parchment line), the problem and the suggested fix,")
    w("shortened to a line or two. The whole text is in the journals. *Rejected* entries give the")
    w("reviser's or fixer's reason. In Phase C and Phase F, an issue without a rejection was applied,")
    w("sometimes with a different wording that the row's note explains. The exceptions are the nits of")
    w("whole-game pass 2, marked *not routed*. The Phase E fixers did not reject issues one by one: their")
    w("rejections and deferrals are quoted at the end of Appendix B, and round-3 issues had no fixer.")
    w("")
    for u in units:
        d = U[u]
        head = PARCH_NAME[u] if u.startswith("perg") else f"{compress(chunk_rows[u])} ({len(chunk_rows[u])} messages)"
        w(f"### {u}: {head}")
        w("")
        tr = d.get("translate")
        if tr and tr["rejected"]:
            w(f"**Translator's declined options** (`{tr['label']}`):")
            w("")
            for r in tr["rejected"]:
                w(rejection_line(r, u).replace("**rejected:**", "**declined:**"))
            w("")
        for r in sorted(d["rounds"]):
            rd = d["rounds"][r]
            for key, who in (("edit", "editor"), ("meaning", "meaning check")):
                iss = rd.get(key) or []
                if not iss:
                    w(f"**Round {r}, {who}:** no issues.")
                    w("")
                    continue
                w(f"**Round {r}, {who}** ({fmt3(smn(iss))}):")
                w("")
                for i in iss:
                    w(issue_line(i, where_g(i.get("index"), u)))
                w("")
            rev = rd.get("revise")
            if rev and rev["rejected"]:
                w(f"**Round {r}, revision rejected** (`{rev['label']}`):")
                w("")
                for x in rev["rejected"]:
                    w(rejection_line(x, u))
                w("")
        nt = d.get("nits")
        if nt:
            if nt["rejected"]:
                w(f"**Nits pass rejected** (`{nt['label']}`):")
                w("")
                for x in nt["rejected"]:
                    w(rejection_line(x, u))
                w("")
            else:
                w(f"**Nits pass** (`{nt['label']}`): {changed_text(nt, u)}, none rejected.")
                w("")
        for p in passes:
            iss = [i for i in p["issues"] if i["unit"] == u]
            if not iss:
                continue
            w(f"**Whole-game pass {p['cr']}** ({fmt3(smn(iss))}):")
            w("")
            for i in iss:
                src = i["src"] + ("" if i["routed"] else "; nit, not routed")
                w(issue_line(i, where_g(i.get("index")), src))
            w("")
            f = p["fixers"].get(u)
            if f and f["rejected"]:
                w(f"**Whole-game pass {p['cr']}, fixer rejected** (`{f['label']}`):")
                w("")
                for x in f["rejected"]:
                    w(rejection_line(x, None if not u.startswith("perg") else u))
                w("")
        ff = d.get("finalfix")
        if ff:
            w(f"**Final fix** (`{ff['label']}`): {changed_text(ff, u)} ({glist(ff['changed'])}), {len(ff['rejected'])} rejected.")
            w("")
        if e_by_unit.get(u):
            w("**Phase E critics** (translation issues naming one message of this unit):")
            w("")
            for r, lens, i, g in e_by_unit[u]:
                w(issue_line(i, f"g{g}", f"r{r} {lens}" + ("; not routed, no fixer in round 3" if r == 3 else "")))
            w("")
        f_here = [(h["round"], i) for h in f_hist for i in h["issues"] if unit_of(i["index"]) == u]
        if f_here:
            w("**Phase F re-review:**")
            w("")
            for r, i in f_here:
                w(issue_line(i, i["index"], f"r{r} {i.get('from')}"))
            w("")
            f_rej = [(fr["round"], x) for fr in f_rounds for x in fr["rejected"]
                     if unit_of((re.findall(r"g\d+", x.get("issue", "")) or [""])[0]) == u]
            for r, x in f_rej:
                w(rejection_line(x).replace("- **rejected:**", f"- Phase F r{r} **rejected:**"))
            if f_rej:
                w("")

    # ---- Appendix B
    w("## Appendix B. Phase E issues not tied to one message")
    w("")
    w("These cover several messages at once, or the build, the runtime, the docs and the repository. They")
    w("are listed for completeness. The translation entries among them are summarised in §3.1.")
    w("")
    for r in e_rounds:
        w(f"**Round {r}:**" + (" (no fixer ran after this round)" if r not in efix else ""))
        w("")
        for lens, i in e_general[r]:
            w(f"- **{i.get('severity')}** {lens}, {i.get('area')}, {md(brief(i.get('where', ''), 70))}: {md(brief(i.get('problem', ''), 160))} *Fix:* {md(brief(i.get('fix', ''), 100))}")
        w("")
    for r, fx in sorted(efix.items()):
        summ = fx.get("summary", "")
        m = re.search(r"^(?:Rejected or not done|REJECTED / DEFERRED)[^\n]*\n((?:- .*\n?)+)", summ, re.M)
        w(f"**Fixer `fix:r{r}`, rejected or deferred:**")
        w("")
        if m:
            for line in m.group(1).strip().splitlines():
                w("- " + md(brief(line[2:], 300)))
        else:
            w("- none listed")
        w("")
        if fx.get("issues"):
            w(f"**Fixer `fix:r{r}`, open items handed on:**")
            w("")
            for i in fx["issues"]:
                w(f"- **{i.get('severity')}** {i.get('area')}, {md(brief(i.get('where', ''), 70))}: {md(brief(i.get('problem', ''), 160))}")
            w("")

    text = "\n".join(o).rstrip() + "\n"
    args.out.write_text(text, encoding="utf-8")
    print(f"wrote {args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out}: {len(text.splitlines())} lines, {len(text)} characters")
    print(f"cross-checks: {sum(ok for ok, _ in CHECKS)}/{len(CHECKS)} pass")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

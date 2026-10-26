# /// script
# requires-python = ">=3.10"
# ///
"""Faithful port of abadia.j message pipeline (c(), e(), f(), b()) for analysis.

Usage:
  uv run text_sim.py strings_all.json [--lang es] [--index N] [--pages] [--json out.json]

Port notes (abadia/j.java, Vineflower lines):
  c(int)  L418-432 : cm = b[i]; cm = cm.replace("@", " _ @").substring(3); cs = cm.split(" ")
  e()     L434-483 : greedy line fill, limit len(line)+len(token) <= 35, '@N' tokens set speaker,
                     '*' in line -> end line, '_' in line or tokens exhausted -> end page,
                     a first line equal to "_ " is dropped; at most 2 lines per page
  b()     L494-570 : one char of cm per eligible tick; page switch when cu<=0 and bR==0;
                     after a page is built bR = 40-cu if cu<40; message ends when cq==len(cm),
                     then cp=17 linger ticks.
Java String.split(" ") semantics: trailing empty strings removed, leading/inner empties kept.
"""
import json, sys, argparse

LIMIT = 35


def jsplit(s):
    parts = s.split(" ")
    while parts and parts[-1] == "":
        parts.pop()
    if not parts:  # Java: "".split(" ") -> [""]
        return [""]
    return parts


class Crash(Exception):
    pass


class Msg:
    def __init__(self, text):
        self.raw = text
        cm = text.replace("@", " _ @")
        self.cm = cm[3:]
        self.cs = jsplit(self.cm)
        self.ct = 0
        self.cu = 0
        self.co = 0
        self.pages = []  # list of (speaker, [lines], cu_added)

    def e(self):
        cs = self.cs
        cw = 0
        cv = []
        cu_before = self.cu
        while True:  # label48
            restart = False
            var0 = True
            while var0:
                var1 = True
                var2 = ""
                while var1:
                    if self.ct >= len(cs):
                        raise Crash(f"ArrayIndexOutOfBounds cs[{self.ct}] (len {len(cs)}) in e()")
                    tok = cs[self.ct]
                    if len(var2) + len(tok) <= LIMIT:
                        if tok.startswith("@"):
                            tok = tok.replace("@", "")
                            cs[self.ct] = tok
                            try:
                                self.co = int(tok)
                            except ValueError:
                                raise Crash(f"NumberFormatException parseInt({tok!r})")
                            self.cu += len(tok) + 2
                        else:
                            var2 += tok + " "
                            self.cu += len(tok) + 1
                        self.ct += 1
                        if "*" in var2:
                            var1 = False
                        if self.ct == len(cs) or "_" in var2:
                            var1 = False
                            var0 = False
                    else:
                        var1 = False
                if var2.lower() == "_ " and cw == 0:
                    restart = True
                    break
                cv.append(var2)
                cw += 1
                if cw == 2:
                    var0 = False
            if restart:
                continue
            break
        self.pages.append({"speaker": self.co, "lines": cv, "cu_added": self.cu - cu_before})
        return cv


def simulate(text, bR0=0, max_ticks=200000):
    """Returns dict with pages, ticks until bP=false, problems."""
    m = Msg(text)
    res = {"problems": []}
    if not text.startswith("@"):
        res["problems"].append("does not start with '@' (c() substring(3) eats 3 chars)")
    try:
        m.e()
    except Crash as ex:
        res["problems"].append("CRASH in first e(): " + str(ex))
        res["pages"] = m.pages
        return res
    cq = 0
    cu = m.cu
    m.cu = cu
    bR = bR0
    cl = False
    cp = 0
    ticks = 0
    page_start_tick = [0]
    try:
        while True:
            ticks += 1
            if ticks > max_ticks:
                res["problems"].append("no termination")
                break
            if m.cu == 0 and bR != 0:
                bR -= 1
                continue
            if not cl:
                if cq >= len(m.cm):
                    raise Crash(f"StringIndexOutOfBounds charAt({cq}) len {len(m.cm)}")
                cq += 1
                if cq == len(m.cm):
                    cl = True
                    cp = 17
                m.cu -= 1
                if m.cu <= 0 and bR == 0:
                    m.e()
                    page_start_tick.append(ticks)
                    if m.cu < 40:
                        bR = 40 - m.cu
                    else:
                        bR = 0
            elif cp != 0:
                cp -= 1
                if cp == 0:
                    break
    except Crash as ex:
        res["problems"].append("CRASH during display: " + str(ex))
    res["ticks"] = ticks
    res["leftover_bR"] = bR
    res["pages"] = m.pages
    res["page_start_tick"] = page_start_tick
    for p in m.pages:
        for ln in p["lines"]:
            vis = ln.rstrip(" ")
            if len(vis) > LIMIT:
                res["problems"].append(f"line > {LIMIT}: {vis!r}")
    for tok in m.cs:
        if len(tok) > LIMIT:
            res["problems"].append(f"token longer than {LIMIT}: {tok!r}")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--index", type=int, default=None)
    ap.add_argument("--pages", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    d = json.load(open(a.json, encoding="utf-8"))
    langs = [a.lang] if a.lang else ["es", "en", "it", "fr", "de", "pl"]
    allres = {}
    for l in langs:
        g = d[l]["g"]
        allres[l] = {}
        for i, s in enumerate(g):
            if a.index is not None and i != a.index:
                continue
            if s == "":
                allres[l][i] = {"empty": True}
                continue
            r = simulate(s)
            allres[l][i] = r
            maxline = max((len(ln.rstrip(' ')) for p in r.get("pages", []) for ln in p["lines"]), default=0)
            print(f"{l} g[{i}] len={len(s)} pages={len(r.get('pages', []))} ticks={r.get('ticks')} maxline={maxline} problems={r['problems']}")
            if a.pages:
                for p in r.get("pages", []):
                    print(f"    @{p['speaker']} cu+={p['cu_added']}")
                    for ln in p["lines"]:
                        print(f"      |{ln.rstrip(' ')}|  ({len(ln.rstrip(' '))})")
    if a.out:
        json.dump(allres, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

"""Minimal, dependency-free Java class-file reader (stdlib only) for the Swedish build's checkers.

  clinit_strings(data) -> [(field, index, value)]

Every String constant that <clinit> stores into an array slot: an LDC/LDC_W of a String whose
previous instruction pushes an int (iconst_m1..5, bipush, sipush) is the value of that slot, and the
next PUTSTATIC names the field. The same rule as `ClassDiff clinit-strings` (tools/java/), so
render_strings.py can read E.h[4] (the window title, which is never drawn) from the built jar
without a JVM and without initialising the class. Values are the decoded Java strings (modified
UTF-8, surrogate pairs joined).
"""
from __future__ import annotations

import struct

_CP_SIZE = {3: 4, 4: 4, 5: 8, 6: 8, 7: 2, 8: 2, 9: 4, 10: 4, 11: 4, 12: 4, 15: 3, 16: 2, 17: 4, 18: 4, 19: 2, 20: 2}


class ClassFormatError(Exception):
    pass


def _mutf8(b: bytes) -> str:
    s = b.replace(b"\xc0\x80", b"\x00").decode("utf-8", "surrogatepass")
    return s.encode("utf-16-le", "surrogatepass").decode("utf-16-le")


def _insn_len(code: bytes, pc: int) -> int:
    op = code[pc]
    if op in (0x10, 0x12, 0xA9, 0xBC) or 0x15 <= op <= 0x19 or 0x36 <= op <= 0x3A:
        return 2
    if op in (0x11, 0x13, 0x14, 0x84, 0xBB, 0xBD, 0xC0, 0xC1, 0xC6, 0xC7) or 0x99 <= op <= 0xA8 or 0xB2 <= op <= 0xB8:
        return 3
    if op == 0xC5:
        return 4
    if op in (0xB9, 0xBA, 0xC8, 0xC9):
        return 5
    if op == 0xC4:                       # wide
        return 6 if code[pc + 1] == 0x84 else 4
    if op in (0xAA, 0xAB):               # tableswitch / lookupswitch
        p = (pc + 4) & ~3
        if op == 0xAA:
            lo, hi = struct.unpack_from(">ii", code, p + 4)
            return p + 12 + 4 * (hi - lo + 1) - pc
        (n,) = struct.unpack_from(">i", code, p + 4)
        return p + 8 + 8 * n - pc
    if op <= 0xC3:
        return 1
    raise ClassFormatError(f"unknown opcode 0x{op:02x} at pc {pc}")


def _pushed_int(code: bytes, pc: int) -> int | None:
    op = code[pc]
    if 0x02 <= op <= 0x08:
        return op - 0x03
    if op == 0x10:
        return struct.unpack_from(">b", code, pc + 1)[0]
    if op == 0x11:
        return struct.unpack_from(">h", code, pc + 1)[0]
    return None


def parse(data: bytes) -> dict:
    """{'cp': {index: (tag, value)}, 'methods': [(name, desc, code bytes or None)]}"""
    if data[:4] != b"\xca\xfe\xba\xbe":
        raise ClassFormatError("not a class file")
    pos = 8
    (n,) = struct.unpack_from(">H", data, pos)
    pos += 2
    cp: dict[int, tuple] = {}
    i = 1
    while i < n:
        tag = data[pos]
        pos += 1
        if tag == 1:
            (ln,) = struct.unpack_from(">H", data, pos)
            cp[i] = (1, _mutf8(data[pos + 2:pos + 2 + ln]))
            pos += 2 + ln
        elif tag in _CP_SIZE:
            size = _CP_SIZE[tag]
            if tag in (7, 8, 16, 19, 20):
                cp[i] = (tag, struct.unpack_from(">H", data, pos)[0])
            elif tag in (9, 10, 11, 12, 17, 18):
                cp[i] = (tag, struct.unpack_from(">HH", data, pos))
            else:
                cp[i] = (tag, data[pos:pos + size])
            pos += size
            if tag in (5, 6):
                i += 1
        else:
            raise ClassFormatError(f"unknown constant-pool tag {tag} at {pos - 1}")
        i += 1
    pos += 6                                          # access, this, super
    (ni,) = struct.unpack_from(">H", data, pos)
    pos += 2 + 2 * ni

    def members(pos):
        (cnt,) = struct.unpack_from(">H", data, pos)
        pos += 2
        out = []
        for _ in range(cnt):
            _acc, ni_, di, na = struct.unpack_from(">HHHH", data, pos)
            pos += 8
            code = None
            for _ in range(na):
                an, alen = struct.unpack_from(">HI", data, pos)
                if cp.get(an) == (1, "Code"):
                    (clen,) = struct.unpack_from(">I", data, pos + 10)
                    code = data[pos + 14:pos + 14 + clen]
                pos += 6 + alen
            out.append((cp[ni_][1], cp[di][1], code))
        return out, pos

    _fields, pos = members(pos)
    methods, pos = members(pos)
    return {"cp": cp, "methods": methods}


def clinit_strings(data: bytes) -> list[tuple[str, int, str]]:
    cf = parse(data)
    cp = cf["cp"]
    res: list[tuple[str, int, str]] = []
    for name, _desc, code in cf["methods"]:
        if name != "<clinit>" or code is None:
            continue
        pending: list[tuple[int, str]] = []
        pc, prev = 0, None
        while pc < len(code):
            op = code[pc]
            if op in (0x12, 0x13):
                idx = code[pc + 1] if op == 0x12 else struct.unpack_from(">H", code, pc + 1)[0]
                ent = cp.get(idx)
                if ent and ent[0] == 8 and prev is not None:
                    k = _pushed_int(code, prev)
                    if k is not None:
                        pending.append((k, cp[ent[1]][1]))
            elif op == 0xB3:                          # putstatic
                (fi,) = struct.unpack_from(">H", code, pc + 1)
                _cls, nat = cp[fi][1]
                fname = cp[cp[nat][1][0]][1]
                res += [(fname, k, v) for k, v in pending]
                pending = []
            prev = pc
            pc += _insn_len(code, pc)
        res += [("?", k, v) for k, v in pending]
    return res


def array_value(data: bytes, field: str, index: int) -> str | None:
    for f, i, v in clinit_strings(data):
        if (f, i) == (field, index):
            return v
    return None

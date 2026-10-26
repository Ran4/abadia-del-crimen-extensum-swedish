"""Minimal, dependency-free PNG helpers for the Swedish build (stdlib only).

Used for res/fuente.png, which must stay an 8-bit palette PNG (colour type 3) whose PLTE starts
within the first 1000 bytes and keeps its tRNS chunk (FORMAT §3.1): abadia.b.a() patches the raw
PLTE bytes to make the black menu font, and an RGBA file crashes the game at startup.

  chunks(data)            -> [(type, body, offset)]
  ihdr(data)              -> dict(width, height, bit_depth, color_type, interlace)
  decode_indexed8(data)   -> (width, height, rows)   rows = list of bytearray of palette indices
  check_image_data(data)  -> None   any colour type / bit depth / interlace: the IHDR combination is
                                     legal, PLTE is present for colour type 3, the IDAT zlib stream is
                                     complete with nothing after it, it inflates to exactly the bytes
                                     the geometry needs, and every row filter byte is 0..4 (PngError)
  encode_indexed8(...)    -> bytes   deterministic writer: IHDR, PLTE, tRNS (bodies copied verbatim),
                                     one IDAT (filter 0 on every row, zlib level 9), IEND
"""
from __future__ import annotations

import struct
import zlib

SIGNATURE = b"\x89PNG\r\n\x1a\n"


class PngError(Exception):
    pass


def chunks(data: bytes) -> list[tuple[bytes, bytes, int]]:
    if data[:8] != SIGNATURE:
        raise PngError("not a PNG (bad signature)")
    out = []
    pos = 8
    while pos < len(data):
        if pos + 8 > len(data):
            raise PngError(f"truncated chunk header at {pos}")
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if len(body) != length or pos + 12 + length > len(data):
            raise PngError(f"truncated chunk {typ!r} at {pos}")
        (crc,) = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        if zlib.crc32(typ + body) & 0xFFFFFFFF != crc:
            raise PngError(f"bad CRC in chunk {typ!r} at {pos}")
        out.append((typ, body, pos))
        pos += 12 + length
        if typ == b"IEND":
            break
    if not out or out[0][0] != b"IHDR" or out[-1][0] != b"IEND":
        raise PngError("missing IHDR/IEND")
    return out


def ihdr(data: bytes) -> dict:
    typ, body, _ = chunks(data)[0]
    w, h, bd, ct, comp, flt, il = struct.unpack(">IIBBBBB", body)
    return {"width": w, "height": h, "bit_depth": bd, "color_type": ct, "compression": comp,
            "filter": flt, "interlace": il}


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def decode_indexed8(data: bytes) -> tuple[int, int, list[bytearray]]:
    """Palette indices of an 8-bit, non-interlaced colour-type-3 PNG."""
    info = ihdr(data)
    if info["color_type"] != 3 or info["bit_depth"] != 8 or info["interlace"] != 0:
        raise PngError(f"expected 8-bit non-interlaced palette PNG, got {info}")
    w, h = info["width"], info["height"]
    raw = zlib.decompress(b"".join(body for typ, body, _ in chunks(data) if typ == b"IDAT"))
    stride = w
    if len(raw) != h * (stride + 1):
        raise PngError(f"IDAT size {len(raw)} != {h}*({stride}+1)")
    rows: list[bytearray] = []
    prev = bytearray(stride)
    for y in range(h):
        ft = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for x in range(stride):
            a = line[x - 1] if x >= 1 else 0
            b = prev[x]
            c = prev[x - 1] if x >= 1 else 0
            if ft == 0:
                pass
            elif ft == 1:
                line[x] = (line[x] + a) & 255
            elif ft == 2:
                line[x] = (line[x] + b) & 255
            elif ft == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif ft == 4:
                line[x] = (line[x] + _paeth(a, b, c)) & 255
            else:
                raise PngError(f"bad filter type {ft} in row {y}")
        rows.append(line)
        prev = line
    return w, h, rows


def _chunk(typ: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + typ + body + struct.pack(">I", zlib.crc32(typ + body) & 0xFFFFFFFF)


def encode_indexed8(width: int, height: int, rows: list[bytes], plte_body: bytes, trns_body: bytes | None) -> bytes:
    if len(rows) != height or any(len(r) != width for r in rows):
        raise PngError("row geometry does not match width/height")
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    out = SIGNATURE + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0))
    out += _chunk(b"PLTE", plte_body)
    if trns_body is not None:
        out += _chunk(b"tRNS", trns_body)
    out += _chunk(b"IDAT", zlib.compress(raw, 9))
    out += _chunk(b"IEND", b"")
    return out


def chunk_body(data: bytes, typ: bytes) -> bytes | None:
    for t, body, _ in chunks(data):
        if t == typ:
            return body
    return None


_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
_DEPTHS = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
_ADAM7 = ((0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2))


def check_image_data(data: bytes) -> None:
    """Raise PngError unless the pixel data decodes exactly (see the module docstring)."""
    info = ihdr(data)
    ct, bd, w, h = info["color_type"], info["bit_depth"], info["width"], info["height"]
    if ct not in _CHANNELS or bd not in _DEPTHS[ct]:
        raise PngError(f"illegal colour type {ct} / bit depth {bd}")
    if info["compression"] != 0 or info["filter"] != 0 or info["interlace"] not in (0, 1):
        raise PngError(f"bad IHDR compression/filter/interlace {info}")
    if w == 0 or h == 0:
        raise PngError("zero width or height")
    types = [t for t, _, _ in chunks(data)]
    if ct == 3 and b"PLTE" not in types:
        raise PngError("palette image without PLTE")
    idat_pos = [k for k, t in enumerate(types) if t == b"IDAT"]
    if not idat_pos:
        raise PngError("no IDAT")
    if idat_pos != list(range(idat_pos[0], idat_pos[-1] + 1)):
        raise PngError("IDAT chunks are not consecutive")
    bits = _CHANNELS[ct] * bd
    d = zlib.decompressobj()
    try:
        raw = d.decompress(b"".join(body for t, body, _ in chunks(data) if t == b"IDAT"))
    except zlib.error as ex:
        raise PngError(f"IDAT does not inflate: {ex}")
    if not d.eof:
        raise PngError("IDAT zlib stream is truncated")
    if d.unused_data:
        raise PngError(f"{len(d.unused_data)} bytes after the end of the IDAT zlib stream")
    passes = _ADAM7 if info["interlace"] else ((0, 0, 1, 1),)
    pos = 0
    for xs, ys, xstep, ystep in passes:
        pw = (w - xs + xstep - 1) // xstep if w > xs else 0
        ph = (h - ys + ystep - 1) // ystep if h > ys else 0
        if pw == 0 or ph == 0:
            continue
        stride = (pw * bits + 7) // 8
        for y in range(ph):
            if pos >= len(raw):
                raise PngError(f"IDAT inflates to {len(raw)} bytes, too few for {w}x{h}")
            if raw[pos] > 4:
                raise PngError(f"bad filter type {raw[pos]} at inflated offset {pos}")
            pos += 1 + stride
    if pos != len(raw):
        raise PngError(f"IDAT inflates to {len(raw)} bytes, {w}x{h} colour type {ct} depth {bd} needs {pos}")

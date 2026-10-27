# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-docx==1.1.2",
#     "lxml==5.3.0",
#     "pillow==11.3.0",
#     "pymupdf==1.28.2",
# ]
# ///
"""Build the Swedish user manual: manual/Användarmanual.docx and manual/Användarmanual.pdf.

Translated from the English manual (original/User's manual (English).pdf), with the
Spanish one used only to check meaning, and kept consistent with the game's Swedish:
names and terms from docs/GLOSSARY.md, the menu labels and values read straight from
translation/strings_sv.tsv (rows f, c, d, e), the HUD hour names (rows b), and the
prologue taken from translation/pergamino1_sv.txt (the intro parchment, unwrapped).

Pictures:
  * game frames from screenshots/runtime_sv/ (and its opening/ subfolder), scaled up
    4x with nearest-neighbour so the pixels stay sharp;
  * the game-screen picture gets the HUD extras (lamp gauge, sleeping abbot, camera)
    drawn on it from the game's own icon files, at the positions and in the way the
    game draws them (abadia.e / abadia.h), because no Swedish run reached a moment
    with all three on screen; the English manual's picture is a composite too;
  * numbered callouts (red boxes, yellow discs) drawn with Pillow in the English style;
  * the menu picture is screenshots/runtime_sv/49_menu_no_dialogue.png, the menu opened
    before anyone speaks (tools/drivers/manual_menu.sh), so no dialogue lies under it;
  * the monk sprites, the photo of the authors and the Retroworks logo are taken
    unchanged from the English PDF (pdfimages, into work/phaseF/manual_src/img/).

The .docx embeds Junicode (regular and bold, obfuscated as Word does), so it keeps its
layout on a machine without that font. The PDF is still the reference layout.

Run from the repository root (never opens a viewer):
    uv run tools/manual/build_manual.py
This writes the .docx, converts it with
    soffice --headless --convert-to pdf --outdir manual manual/Användarmanual.docx
(with a private LibreOffice profile in work/phaseF/lo_profile/, so a LibreOffice the user
has open is neither used nor disturbed), then adds the PDF's link annotations, which
LibreOffice 7.3 drops on export, and checks the result.
    --no-pdf       write only the .docx
    --links-only   only add the links to an existing manual/Användarmanual.pdf
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import io
import os
import re
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path

import pymupdf
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Emu, Pt, RGBColor
from lxml import etree
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
EN_PDF = ROOT / "original" / "User's manual (English).pdf"
JAR = ROOT / "original" / "TheAbbeyOfCrimeExtensum.jar"
SHOTS = ROOT / "screenshots" / "runtime_sv"
TSV = ROOT / "translation" / "strings_sv.tsv"
PARCHMENT = ROOT / "translation" / "pergamino1_sv.txt"
SRC_IMG = ROOT / "work" / "phaseF" / "manual_src" / "img"
BUILD_IMG = ROOT / "work" / "phaseF" / "manual_build"
OUT = ROOT / "manual" / "Användarmanual.docx"
OUT_PDF = OUT.with_suffix(".pdf")
LO_PROFILE = ROOT / "work" / "phaseF" / "lo_profile"

SITE = "http://www.abadiadelcrimenextensum.com/"
SITE_TEXT = "http://www.abadiadelcrimenextensum.com"
MAIL = "contact@abadiadelcrimenextensum.com"
FACEBOOK = "http://facebook.com/abadiaextensum"
TWITTER = "http://twitter.com/abadiaextensum"
JAVA_URL = "http://www.java.com/"
JAVA_TEXT = "www.java.com"

# Link text as printed -> target, for the PDF's link annotations (LibreOffice drops the .docx
# hyperlinks on export). Longest text first: a later, shorter match that overlaps an earlier
# link is skipped (the footer address is a prefix of the KONTAKT one).
PDF_LINKS = [
    (SITE, SITE),
    (SITE_TEXT, SITE),
    (MAIL, "mailto:" + MAIL),
    (FACEBOOK, FACEBOOK),
    (TWITTER, TWITTER),
    (JAVA_TEXT, JAVA_URL),
]

# The black-bar section headings, in order (check_pdf looks for each as a whole word).
HEADINGS = ["Bakgrund", "Systemkrav", "Styrning", "Spelskärmen", "Menyn", "Mellansekvenser",
            "Kontakt", "Medverkande", "Tack"]

# Fonts embedded in the .docx: family -> {Word embed style: fontconfig pattern}.
EMBED_FONTS = {"Junicode": {"Regular": "Junicode:style=Regular", "Bold": "Junicode:style=Bold"}}

BODY_FONT = "Junicode"
FOOTER_FONT = "Times New Roman"
MONO_FONT = "Courier New"
RED = RGBColor(0xC0, 0x12, 0x12)
INK = RGBColor(0x1A, 0x1A, 0x1A)
LINK_BLUE = "1F3FBF"

BODY_SIZE = 13    # pt
LEADING = 1.45  # exact line height as a multiple of the font size
SCALE = 4  # game frames are 320x208; drawn 4x so the PDF keeps the pixels sharp


# --------------------------------------------------------------------------- inputs


def read_tsv() -> dict[tuple[str, int], str]:
    rows: dict[tuple[str, int], str] = {}
    with TSV.open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE)
        header = next(reader)
        i_arr, i_idx, i_sv = header.index("array"), header.index("index"), header.index("sv")
        for row in reader:
            if len(row) > i_sv:
                rows[(row[i_arr], int(row[i_idx]))] = row[i_sv]
    return rows


def ui_strings() -> dict[str, str]:
    """Menu labels/values and HUD hours exactly as shipped (labels without ': ')."""
    t = read_tsv()

    def label(i: int) -> str:
        return t[("f", i)].rstrip().rstrip(":").strip()

    ui = {
        "CONTINUE": label(0),
        "SAVE": label(1),
        "LOAD": label(2),
        "SOUND": label(3),
        "MUSIC": label(4),
        "FULLSCREEN": label(6),
        "EXTRAS": label(7),
        "RESTART": label(8),
        "EXIT": label(9),
        "OFF": t[("c", 0)],
        "ON": t[("c", 1)],
        "CLASSIC": t[("d", 0)],
        "DIRECTIONAL": t[("d", 1)],
        "VOICES_SFX": t[("e", 0)],
        "SFX": t[("e", 1)],
        "SILENCE": t[("e", 2)],
        "EMPTY": t[("w.u", 4)],
    }
    hours = []
    for i in range(7):
        cell = t[("b", i)]
        if len(cell) != 7:
            sys.exit(f"strings_sv.tsv b[{i}] is not 7 cells: {cell!r}")
        hours.append(cell.strip())
    ui["HOURS"] = hours
    # The manual's sentences were written around these exact strings; stop if they move.
    expected = {
        "CONTINUE": "FORTSÄTT", "SAVE": "SPARA SPEL", "LOAD": "LADDA SPEL", "SOUND": "LJUD",
        "MUSIC": "MUSIK", "FULLSCREEN": "HELSKÄRM", "EXTRAS": "VISA INDIKATORER",
        "RESTART": "STARTA OM", "EXIT": "AVSLUTA", "OFF": "AV", "ON": "PÅ",
        "CLASSIC": "KLASSISK STYRNING", "DIRECTIONAL": "RIKTNINGSSTYRNING",
        "VOICES_SFX": "RÖSTER, EFFEKTER", "SFX": "EFFEKTER", "SILENCE": "AV", "EMPTY": "TOM",
        "HOURS": ["NATT", "PRIM", "TERS", "SEXT", "NON", "VESPER", "NATTBÖN"],
    }
    for key, want in expected.items():
        if ui[key] != want:
            sys.exit(f"strings_sv.tsv changed: {key} is {ui[key]!r}, the manual expects {want!r}; "
                     "update the manual text in tools/manual/build_manual.py")
    if t[("f", 5)] != "":
        sys.exit("strings_sv.tsv f[5] is no longer empty; update the menu section")
    return ui


def prologue() -> list[str]:
    """pergamino1_sv.txt up to the credits block, unwrapped into normal prose."""
    raw = PARCHMENT.read_text(encoding="utf-8")
    paras: list[str] = []
    for block in re.split(r"\n[ \t]*\n", raw):
        if not block.strip():
            continue
        if block.strip().startswith("Efter spelet av"):
            break
        text = ""
        for line in (ln.strip() for ln in block.strip("\n").split("\n")):
            if text.endswith("-"):
                text = text[:-1] + line  # undo the hand hyphenation
            elif text:
                text += " " + line
            else:
                text = line
        paras.append(text)
    if len(paras) != 3 or not paras[-1].endswith("..."):
        sys.exit(f"unexpected parchment layout: {len(paras)} paragraphs")
    paras[-1] = paras[-1][:-3] + "…"
    for p in paras:
        if re.search(r"\w-\s|\s-\w", p):
            sys.exit(f"hyphen left after unwrapping: {p[:60]!r}")
    return paras


# --------------------------------------------------------------------------- images


def font_file(pattern: str) -> str:
    return subprocess.run(["fc-match", "-f", "%{file}", pattern], check=True,
                          capture_output=True, text=True).stdout.strip()


def extract_pdf_images() -> None:
    """The decorative images of the English manual (sprites, photo, logo)."""
    want = {"i-001.png": (160, 80), "i-002.png": (160, 80), "i-003.png": (80, 72),
            "i-004.png": (80, 72), "i-010.png": (1024, 576), "i-011.png": (152, 70),
            "i-012.png": (152, 70)}
    if not all((SRC_IMG / n).exists() for n in want):
        SRC_IMG.mkdir(parents=True, exist_ok=True)
        subprocess.run(["pdfimages", "-png", str(EN_PDF), str(SRC_IMG / "i")], check=True)
    for name, size in want.items():
        with Image.open(SRC_IMG / name) as im:
            if im.size != size:
                sys.exit(f"{name}: expected {size}, got {im.size}")


def masked(rgb_name: str, mask_name: str, scale: int) -> Image.Image:
    rgb = Image.open(SRC_IMG / rgb_name).convert("RGB")
    mask = Image.open(SRC_IMG / mask_name).convert("L")
    im = rgb.convert("RGBA")
    im.putalpha(mask)
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def jar_png(name: str) -> Image.Image:
    with zipfile.ZipFile(JAR) as z:
        return Image.open(io.BytesIO(z.read(f"res/{name}"))).convert("RGBA")


def frame(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    if im.size != (320, 208):
        sys.exit(f"{path} is not a 320x208 game frame")
    return im


def up(im: Image.Image, s: int = SCALE) -> Image.Image:
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def with_hud_extras(base: Image.Image) -> Image.Image:
    """Draw the three 'extras' as the game does (e_0.java:774-781, h_0.java:107-125)."""
    im = base.copy()
    lamp = jar_png("lampara.png")             # 80x24: top half gauge, bottom half its frame
    w, h = lamp.size
    im.alpha_composite(lamp.crop((0, 0, w, h // 2)), (4, 4))       # full oil
    im.alpha_composite(lamp.crop((0, h // 2, w, h)), (4, 4))
    sleep = jar_png("sleep.png")              # 24x72: four 18-px frames, abbot asleep
    im.alpha_composite(sleep.crop((0, 36, 24, 54)), (288, 8))       # frame 2 (with bubble)
    im.alpha_composite(jar_png("cam.png"), (256, 8))                # alternate camera
    return im


def callouts(native: Image.Image, boxes, discs) -> Image.Image:
    """Numbered callouts in the English manual's style, in native-pixel coordinates."""
    s = SCALE
    big = up(native)
    lines = Image.new("RGBA", big.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lines)
    for x0, y0, x1, y1 in boxes:
        d.rounded_rectangle([x0 * s, y0 * s, x1 * s, y1 * s], radius=3 * s,
                            outline=(236, 18, 18, 255), width=int(1.6 * s))
    glow = lines.filter(ImageFilter.GaussianBlur(0.9 * s))
    big = Image.alpha_composite(Image.alpha_composite(big, glow), lines)
    d = ImageDraw.Draw(big)
    font = ImageFont.truetype(font_file("Liberation Serif:bold"), int(10.5 * s))
    r = 5.7 * s
    for text, cx, cy in discs:
        x, y = cx * s, cy * s
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 236, 0, 255),
                  outline=(120, 100, 0, 255), width=max(1, s // 4))
        d.text((x, y + 0.2 * s), text, font=font, fill=(0, 0, 0, 255), anchor="mm")
    return big.convert("RGB")


def build_images() -> dict[str, Path]:
    extract_pdf_images()
    BUILD_IMG.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}

    def save(key: str, im: Image.Image) -> None:
        path = BUILD_IMG / f"{key}.png"
        im.save(path, optimize=True)
        out[key] = path

    save("cover", up(frame(SHOTS / "07_intro_logo.png")).convert("RGB"))
    # Opened before anyone speaks: the tour's menu frames (24-41) all have a dialogue box
    # under the menu scroll, which shows as a half-covered, garbled line.
    save("menu", up(frame(SHOTS / "49_menu_no_dialogue.png")).convert("RGB"))

    game = with_hud_extras(frame(SHOTS / "20_play_start_hud.png"))
    save("game_screen", callouts(
        game,
        boxes=[
            (136, 88, 157, 126),   # 1 Vilhelm
            (110, 86, 131, 122),   # 2 Adso
            (66, 176, 252, 207),   # 3 föremål
            (1, 177, 62, 194),     # 4 dag
            (1, 196, 62, 207),     # 5 timme
            (255, 176, 319, 207),  # 6 obsequium
            (2, 2, 87, 18),        # 7 olja
            (286, 4, 317, 29),     # 8 abboten
            (252, 4, 283, 34),     # 9 alternativ kamera
        ],
        discs=[
            ("1", 147, 127), ("2", 120, 123), ("3", 159, 175), ("4", 62, 185),
            ("5", 62, 201), ("6", 300, 175), ("7", 45, 20), ("8", 301, 30),
            ("9", 267, 35),
        ],
    ))

    cut = frame(SHOTS / "opening" / "pages" / "035_g001_p21.png")
    save("cutscene", callouts(
        cut, boxes=[],
        discs=[("1", 160, 8), ("2", 15, 146), ("3", 299, 167)],
    ))

    save("sprites_two", masked("i-003.png", "i-004.png", 4))     # Vilhelm and Adso
    save("sprites_three", masked("i-001.png", "i-002.png", 4))   # three monks
    save("retroworks", masked("i-011.png", "i-012.png", 3))
    out["photo"] = SRC_IMG / "i-010.png"
    return out


# --------------------------------------------------------------------------- docx helpers

PPR_ORDER = [
    "pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
    "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
    "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
    "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
    "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle",
    "rPr", "sectPr", "pPrChange",
]
TBLPR_ORDER = [
    "tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
    "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd",
    "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription", "tblPrChange",
]
RPR_ORDER = [
    "rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike",
    "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden",
    "color", "spacing", "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect", "bdr",
    "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish",
    "oMath",
]


def _sort_children(el, order: list[str]) -> None:
    rank = {qn(f"w:{n}"): i for i, n in enumerate(order)}
    kids = list(el)
    kids.sort(key=lambda k: rank.get(k.tag, len(order)))
    for k in kids:
        el.remove(k)
    for k in kids:
        el.append(k)


def normalize(root) -> None:
    """Word is strict about child order in pPr/rPr; raw appends must be put in place."""
    for el in root.iter(qn("w:pPr")):
        _sort_children(el, PPR_ORDER)
    for el in root.iter(qn("w:rPr")):
        _sort_children(el, RPR_ORDER)
    for el in root.iter(qn("w:tblPr")):
        _sort_children(el, TBLPR_ORDER)


def set_fonts(rpr, name: str) -> None:
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        fonts.attrib.pop(qn(f"w:{attr}"), None)
    for attr in ("ascii", "hAnsi", "cs", "eastAsia"):
        fonts.set(qn(f"w:{attr}"), name)


def el(tag: str, **attrs) -> OxmlElement:
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn(f"w:{k}"), str(v))
    return e


class Manual:
    def __init__(self) -> None:
        self.doc = Document()
        self.headings: list[str] = []
        self._setup()

    # ---- setup
    def _setup(self) -> None:
        doc = self.doc
        sec = doc.sections[0]
        sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
        sec.left_margin = sec.right_margin = Cm(2.2)
        sec.top_margin, sec.bottom_margin = Cm(1.8), Cm(2.2)
        sec.header_distance, sec.footer_distance = Cm(1.0), Cm(1.0)
        self.text_width = sec.page_width - sec.left_margin - sec.right_margin

        styles = doc.styles.element
        rpr_default = styles.find(qn("w:docDefaults")).find(qn("w:rPrDefault")).find(qn("w:rPr"))
        set_fonts(rpr_default, BODY_FONT)
        lang = rpr_default.find(qn("w:lang"))
        if lang is None:
            lang = el("w:lang")
            rpr_default.append(lang)
        lang.set(qn("w:val"), "sv-SE")
        lang.set(qn("w:eastAsia"), "sv-SE")
        lang.set(qn("w:bidi"), "ar-SA")

        normal = doc.styles["Normal"]
        normal.font.name = BODY_FONT
        set_fonts(normal.element.get_or_add_rPr(), BODY_FONT)
        normal.font.size = Pt(BODY_SIZE)
        normal.font.color.rgb = INK
        pf = normal.paragraph_format
        pf.space_before, pf.space_after = Pt(0), Pt(7)
        pf.line_spacing = Pt(round(BODY_SIZE * LEADING, 1))  # exact: bold runs must not open the lines
        pf.widow_control = True

        h1 = doc.styles["Heading 1"]
        set_fonts(h1.element.get_or_add_rPr(), BODY_FONT)
        h1.font.name = BODY_FONT
        h1.font.size = Pt(15)
        h1.font.bold = True
        h1.font.italic = False
        h1.font.all_caps = True
        h1.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        rpr = h1.element.get_or_add_rPr()
        # 0.5 pt letter spacing. 1.5 pt split the PDF text layer into fragments
        # ("BA KG RU ND"), so the headings could not be searched; main() checks this.
        rpr.append(el("w:spacing", val=10))
        hpf = h1.paragraph_format
        hpf.space_before, hpf.space_after = Pt(0), Pt(16)
        hpf.line_spacing = 1.0
        hpf.page_break_before = True
        hpf.keep_with_next = True
        ppr = h1.element.get_or_add_pPr()
        ppr.append(el("w:shd", val="clear", color="auto", fill="000000"))

        sub = doc.styles.add_style("Underrubrik", WD_STYLE_TYPE.PARAGRAPH)
        sub.base_style = normal
        sub.font.bold = True
        sub.font.underline = True
        sub.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sub.paragraph_format.space_before = Pt(10)
        sub.paragraph_format.space_after = Pt(6)
        sub.paragraph_format.keep_with_next = True

        footer_style = doc.styles["Footer"]
        footer_style.font.name = FOOTER_FONT
        set_fonts(footer_style.element.get_or_add_rPr(), FOOTER_FONT)
        footer_style.font.size = Pt(10)

        self._footer(sec)

        cp = doc.core_properties
        cp.title = "La Abadía del Crimen Extensum – Användarmanual"
        cp.subject = "Svensk användarmanual (inofficiell översättning för privat bruk)"
        cp.author = ""
        cp.last_modified_by = ""
        cp.language = "sv-SE"
        cp.keywords = ""
        cp.comments = ""
        cp.revision = 1
        # The template's own dates are from 2013; use the build time (UTC).
        now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None, microsecond=0)
        cp.created = cp.modified = now

    def _footer(self, sec) -> None:
        p = sec.footer.paragraphs[0]
        p.style = self.doc.styles["Footer"]
        p.paragraph_format.tab_stops.add_tab_stop(Emu(int(self.text_width / 2)),
                                                  WD_TAB_ALIGNMENT.CENTER)
        self.field(p, "PAGE", "1")
        p.add_run("\t")
        self.link(p, SITE, SITE_TEXT, font=FOOTER_FONT, size=10)

    # ---- inline pieces
    @staticmethod
    def field(p, instr: str, placeholder: str) -> None:
        r = p.add_run()
        r._r.append(el("w:fldChar", fldCharType="begin"))
        r = p.add_run()
        t = OxmlElement("w:instrText")
        t.set(qn("xml:space"), "preserve")
        t.text = f" {instr} "
        r._r.append(t)
        r = p.add_run()
        r._r.append(el("w:fldChar", fldCharType="separate"))
        p.add_run(placeholder)
        r = p.add_run()
        r._r.append(el("w:fldChar", fldCharType="end"))

    @staticmethod
    def link(p, url: str, text: str, *, font: str | None = None, size: float | None = None,
             bold: bool = False) -> None:
        r_id = p.part.relate_to(url, RT.HYPERLINK, is_external=True)
        h = OxmlElement("w:hyperlink")
        h.set(qn("r:id"), r_id)
        r = OxmlElement("w:r")
        rpr = OxmlElement("w:rPr")
        if font:
            set_fonts(rpr, font)
        if bold:
            rpr.append(el("w:b"))
        rpr.append(el("w:color", val=LINK_BLUE))
        if size:
            rpr.append(el("w:sz", val=int(size * 2)))
            rpr.append(el("w:szCs", val=int(size * 2)))
        rpr.append(el("w:u", val="single"))
        r.append(rpr)
        t = OxmlElement("w:t")
        t.set(qn("xml:space"), "preserve")
        t.text = text
        r.append(t)
        h.append(r)
        p._p.append(h)

    @staticmethod
    def rich(p, text: str, *, size: float | None = None, color: RGBColor | None = None,
             font: str | None = None) -> None:
        """Add text where **…** is bold."""
        for i, part in enumerate(re.split(r"\*\*", text)):
            if not part:
                continue
            r = p.add_run(part)
            r.bold = bool(i % 2) or None
            if size:
                r.font.size = Pt(size)
            if color is not None:
                r.font.color.rgb = color
            if font:
                r.font.name = font
                set_fonts(r._r.get_or_add_rPr(), font)

    # ---- blocks
    def heading(self, text: str) -> None:
        self.headings.append(text)
        self.doc.add_paragraph("\u00a0" + text, style="Heading 1")

    def para(self, text: str = "", *, align=None, size=None, color=None, before=None, after=None,
             indent=None, first=None, keep=False, page_break=False, line=None):
        p = self.doc.add_paragraph()
        if text:
            self.rich(p, text, size=size, color=color)
        pf = p.paragraph_format
        if align is not None:
            pf.alignment = align
        if before is not None:
            pf.space_before = Pt(before)
        if after is not None:
            pf.space_after = Pt(after)
        if indent is not None:
            pf.left_indent = Cm(indent)
        if first is not None:
            pf.first_line_indent = Cm(first)
        if keep:
            pf.keep_with_next = True
        if page_break:
            pf.page_break_before = True
        if line is not None:
            pf.line_spacing = line
        elif size:
            pf.line_spacing = Pt(round(size * LEADING, 1))
        return p

    def numbered(self, n: int, text: str, *, after: float):
        """'n.' hanging in the margin like the bullets, wrapped lines under the text."""
        return self.para(f"{n}.\t{text}", indent=1.0, first=-0.5, after=after)

    def dropcap(self, text: str, *, page_break: bool = False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                after: float = 7):
        """A red initial dropped three lines, as in the English manual."""
        letter, rest = text[0], text[1:]
        p = self.doc.add_paragraph()
        ppr = p._p.get_or_add_pPr()
        ppr.append(el("w:framePr", dropCap="drop", lines=3, wrap="around", vAnchor="text",
                      hAnchor="text"))
        if page_break:
            p.paragraph_format.page_break_before = True
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = Pt(46)
        r = p.add_run(letter)
        r.font.size = Pt(56)
        r.font.color.rgb = RED
        r._r.get_or_add_rPr().append(el("w:position", val=-4))
        body = self.para(rest, align=align, after=after)
        return body

    def picture(self, path: Path, width_cm: float, *, before=4, after=8, align=WD_ALIGN_PARAGRAPH.CENTER):
        p = self.doc.add_paragraph()
        p.paragraph_format.alignment = align
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.line_spacing = 1.0   # auto: an exact leading would clip the image
        p.add_run().add_picture(str(path), width=Cm(width_cm))
        return p

    def side_by_side(self, left, right, widths_cm: tuple[float, float], *, flush: str) -> None:
        """A borderless two-cell row: each side is ('text', str) or ('image', path, width_cm).

        The row is exactly the text width. flush ('left' or 'right') is the outer side of the
        text cell: its cell margin is set to 0 there, so the text lines up with the body text
        and the heading bar instead of sitting a cell margin (about 2 mm) inside them.
        """
        table = self.doc.add_table(rows=1, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        tbl_pr = table._tbl.tblPr
        tbl_pr.append(el("w:tblLayout", type="fixed"))
        borders = el("w:tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            borders.append(el(f"w:{side}", val="nil"))
        tbl_pr.append(borders)
        if flush not in ("left", "right"):
            raise ValueError(flush)
        margins = el("w:tblCellMar")
        margins.append(el(f"w:{flush}", w=0, type="dxa"))
        tbl_pr.append(margins)
        for i, (cell, spec) in enumerate(zip(table.rows[0].cells, (left, right))):
            cell.width = Cm(widths_cm[i])
            table.columns[i].width = Cm(widths_cm[i])
            p = cell.paragraphs[0]
            if spec[0] == "text":
                self.rich(p, spec[1])
                p.paragraph_format.space_after = Pt(0)
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            else:
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0
                p.add_run().add_picture(str(spec[1]), width=Cm(spec[2]))
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        self.para("", after=4)

    def save(self, path: Path) -> None:
        for part_el in [self.doc.element, self.doc.styles.element] + [
            s.footer._element for s in self.doc.sections
        ]:
            normalize(part_el)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(str(path))
        finish_package(path)


# --------------------------------------------------------------------------- package

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
REL_FONT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"
REL_THUMB = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"
CT_ODTTF = "application/vnd.openxmlformats-officedocument.obfuscatedFont"
APP_XML = (
    "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>\n"
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
    'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
    "<Application>python-docx</Application><DocSecurity>0</DocSecurity><ScaleCrop>false</ScaleCrop>"
    "<LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc>"
    "<HyperlinksChanged>false</HyperlinksChanged></Properties>"
)


def w(tag: str) -> str:
    return f"{{{NS_W}}}{tag}"


def xml_bytes(root) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def obfuscate_font(data: bytes, font_key: str) -> bytes:
    """ECMA-376 Part 1, 17.8.1: XOR the first 32 bytes with the fontKey GUID, read as 16
    bytes in reverse order of its hex digits (the key repeated twice)."""
    key = bytes.fromhex(font_key.strip("{}").replace("-", ""))[::-1]
    head = bytes(b ^ key[i % 16] for i, b in enumerate(data[:32]))
    return head + data[32:]


def finish_package(path: Path) -> None:
    """Fix what python-docx's default template leaves behind, and embed the body font.

    * drop the template's generic docProps/thumbnail.jpeg (and Word's savePreviewPicture,
      which would write a new one), and replace its app.xml ('Microsoft Macintosh Word',
      'Pages 1', 'Normal.dotm') with a minimal one;
    * embed Junicode regular and bold as obfuscated fonts (word/fonts/*.odttf, the
      fontTable entry, embedTrueTypeFonts), so Word on a machine without Junicode keeps the
      font and the page breaks. Junicode's OS/2 fsType is 0 (installable embedding).
    """
    with zipfile.ZipFile(path) as z:
        names = [i.filename for i in z.infolist()]
        parts = {n: z.read(n) for n in names}

    rels = etree.fromstring(parts["_rels/.rels"])
    for rel in list(rels):
        if rel.get("Type") == REL_THUMB:
            target = rel.get("Target").lstrip("/")
            parts.pop(target, None)
            names.remove(target)
            rels.remove(rel)
    parts["_rels/.rels"] = xml_bytes(rels)
    parts["docProps/app.xml"] = APP_XML.encode("utf-8")

    settings = etree.fromstring(parts["word/settings.xml"])
    for e in settings.findall(w("savePreviewPicture")):
        settings.remove(e)
    if settings.find(w("embedTrueTypeFonts")) is None:
        anchor = settings.find(w("zoom"))   # CT_Settings order: ..., zoom, ..., embedTrueTypeFonts
        if anchor is None:
            sys.exit("settings.xml has no w:zoom to place w:embedTrueTypeFonts after")
        anchor.addnext(etree.Element(w("embedTrueTypeFonts")))
    parts["word/settings.xml"] = xml_bytes(settings)

    fonts = etree.fromstring(parts["word/fontTable.xml"])
    if "word/_rels/fontTable.xml.rels" in parts:
        sys.exit("the template's fontTable already has relationships; update finish_package")
    font_rels = etree.Element(f"{{{NS_PKG_REL}}}Relationships", nsmap={None: NS_PKG_REL})
    n = 0
    for family, styles in EMBED_FONTS.items():
        for old in fonts.findall(w("font")):
            if old.get(w("name")) == family:
                fonts.remove(old)
        font = etree.SubElement(fonts, w("font"))
        font.set(w("name"), family)
        for tag, val in (("charset", "00"), ("family", "roman"), ("pitch", "variable")):
            etree.SubElement(font, w(tag)).set(w("val"), val)
        for style, pattern in styles.items():   # Regular, Bold: the schema order of embed*
            n += 1
            data = Path(font_file(pattern)).read_bytes()
            key = "{" + str(uuid.UUID(bytes=hashlib.sha256(data).digest()[:16])).upper() + "}"
            target = f"fonts/font{n}.odttf"
            parts[f"word/{target}"] = obfuscate_font(data, key)
            names.append(f"word/{target}")
            rid = f"rId{n}"
            etree.SubElement(font_rels, f"{{{NS_PKG_REL}}}Relationship",
                             Id=rid, Type=REL_FONT, Target=target)
            embed = etree.SubElement(font, w(f"embed{style}"))
            embed.set(f"{{{NS_R}}}id", rid)
            embed.set(w("fontKey"), key)
    parts["word/fontTable.xml"] = xml_bytes(fonts)
    parts["word/_rels/fontTable.xml.rels"] = xml_bytes(font_rels)
    names.append("word/_rels/fontTable.xml.rels")

    types = etree.fromstring(parts["[Content_Types].xml"])
    if not any(d.get("Extension") == "odttf" for d in types.findall(f"{{{NS_CT}}}Default")):
        d = etree.Element(f"{{{NS_CT}}}Default", Extension="odttf", ContentType=CT_ODTTF)
        types.insert(0, d)
    parts["[Content_Types].xml"] = xml_bytes(types)

    tmp = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ["[Content_Types].xml"] + [n for n in names if n != "[Content_Types].xml"]:
            z.writestr(name, parts[name])
    os.replace(tmp, path)


# --------------------------------------------------------------------------- pdf


def convert_pdf() -> None:
    """soffice --headless --convert-to pdf --outdir manual manual/Användarmanual.docx,
    with a private profile so it neither hands the job to nor disturbs a running LibreOffice."""
    LO_PROFILE.mkdir(parents=True, exist_ok=True)
    before = OUT_PDF.stat().st_mtime_ns if OUT_PDF.exists() else None
    cmd = ["soffice", f"-env:UserInstallation={LO_PROFILE.as_uri()}", "--headless",
           "--convert-to", "pdf", "--outdir", str(OUT.parent.relative_to(ROOT)),
           str(OUT.relative_to(ROOT))]
    res = subprocess.run(cmd, check=False, cwd=ROOT, capture_output=True, text=True, timeout=300)
    if res.returncode != 0 or not OUT_PDF.exists() or OUT_PDF.stat().st_mtime_ns == before:
        sys.exit(f"soffice did not write {OUT_PDF.relative_to(ROOT)}:\n{res.stdout}{res.stderr}")
    print(f"wrote {OUT_PDF.relative_to(ROOT)} (soffice --headless)")


def add_pdf_links(pdf: Path) -> dict[str, int]:
    """URI link annotations over every printed address (and 'www.java.com')."""
    doc = pymupdf.open(pdf)
    counts: dict[str, int] = {}
    for page in doc:
        taken = []
        for lk in page.get_links():   # already there (a second run, or a future LibreOffice)
            taken.append(pymupdf.Rect(lk["from"]))
            counts[lk.get("uri", "")] = counts.get(lk.get("uri", ""), 0) + 1
        for text, uri in PDF_LINKS:
            for rect in page.search_for(text):
                if any(rect.intersects(t) for t in taken):
                    continue
                page.insert_link({"kind": pymupdf.LINK_URI, "from": rect, "uri": uri})
                taken.append(rect)
                counts[uri] = counts.get(uri, 0) + 1
    pages = doc.page_count
    tmp = pdf.with_suffix(".tmp.pdf")
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    os.replace(tmp, pdf)

    want = {SITE: pages + 1, "mailto:" + MAIL: 1, FACEBOOK: 1, TWITTER: 1, JAVA_URL: 1}
    if counts != want:
        sys.exit(f"PDF links: got {counts}, expected {want}")
    return counts


def check_pdf(pdf: Path, headings: list[str]) -> None:
    """Every page has its link annotations, and the headings are whole words in the text layer."""
    doc = pymupdf.open(pdf)
    no_links = [p.number + 1 for p in doc if not list(p.links())]
    doc.close()
    if no_links:
        sys.exit(f"PDF pages without links: {no_links}")
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True,
                          capture_output=True, text=True).stdout
    words = set(re.findall(r"\w+", text.upper()))
    broken = [h for h in headings if h.upper() not in words]
    if broken:
        sys.exit(f"headings not found as whole words in the PDF text layer: {broken}")


# --------------------------------------------------------------------------- content


def build(img: dict[str, Path], ui: dict, prolog: list[str]) -> Manual:
    m = Manual()
    C, J, R = WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.JUSTIFY, WD_ALIGN_PARAGRAPH.RIGHT

    # ---- 1. cover
    m.para("La Abadía del Crimen Extensum", align=C, size=30, color=RED, before=48, after=6)
    m.para("nyversion av ”La Abadía del Crimen”", align=C, size=16, color=RED, after=26)
    m.picture(img["cover"], 16.0, after=26)
    m.para("Användarmanual", align=C, size=17, color=RED)

    # ---- 2. prologue (the intro parchment, Adso's voice)
    m.dropcap(prolog[0], page_break=True, after=18)
    m.para(prolog[1], align=J, after=18)
    m.para(prolog[2], align=J, after=18)
    m.para("Adso av Melk", align=R, before=6)

    # ---- 3. background
    m.heading("Bakgrund")
    m.dropcap("Följ inte allehanda främmande och sofistiska läror som sår pestens frö – så skrev "
              "ingen mindre än Clemens VI år 1346 till magistrarna och studenterna vid "
              "universitetet i Paris.", align=WD_ALIGN_PARAGRAPH.LEFT, after=14)
    m.side_by_side(
        ("text", ("Påven syftade i sitt brev på lärorna hos en framstående franciskanermunk av "
                 "engelsk börd, Vilhelm av Occam, som flera år tidigare hade flytt ur fängelset i "
                 "Avignon, där han satt anklagad för kätteri. I fyra år hade han hållits fången, "
                 "tills han lyckades fly och söka skydd vid kejsar Ludvig av Bayerns hov. "
                 "Kejsaren låg då i fejd med påven Johannes XXII.")),
        ("image", img["sprites_two"], 2.3),
        (13.8, 2.8),
        flush="left",
    )
    m.side_by_side(
        ("image", img["sprites_three"], 4.2),
        ("text", ("När kejsaren hade dött ville Vilhelm återuppta sitt uppdrag i ordens och "
                 "kyrkans tjänst. Därför reste han till Italien med sin unge novis för att möta "
                 "Bernardo Gui, som vid den tiden ledde inkvisitionen i den trakten och därmed "
                 "ytterst var påvens företrädare.")),
        (4.6, 12.0),
        flush="right",
    )
    m.para("Om Vilhelm verkligen nådde sitt mål vet vi dock inte säkert. Det enda som finns kvar "
           "är det vittnesbörd som hans lärjunge skrev ned många år senare, i en samling pergament "
           "som skildrar de förunderliga och fruktansvärda händelser som inträffade under den "
           "vecka de båda tillbringade i klostret där mötet skulle äga rum.", after=14)
    m.para("Vittnesbördet om den historia som du nu ska återuppleva…")

    # ---- 4. requirements
    m.heading("Systemkrav")
    m.para("Spelet fungerar i Windows, macOS och Linux.")
    p = m.para("Du behöver ha **Java** (")
    m.link(p, JAVA_URL, JAVA_TEXT)
    m.rich(p, ") installerat och uppdaterat på datorn.")
    m.para("Den svenska versionen startar du med ett eget startskript i mappen **game**:",
           before=6, keep=True)
    m.para("•\t**Linux och macOS:** öppna en terminal i mappen **game** och skriv:",
           indent=1.0, first=-0.5, after=4, keep=True)
    p = m.para(indent=1.6, after=4, keep=True)
    m.rich(p, 'bash "TheAbbeyOfCrimeExtensum(Swedish).sh"', font=MONO_FONT, size=11)
    m.para("Citattecknen behövs, eftersom skalet annars tolkar parenteserna som specialtecken.",
           indent=1.0)
    m.para("•\t**Windows:** dubbelklicka på **TheAbbeyOfCrimeExtensum(Swedish).bat**.",
           indent=1.0, first=-0.5)
    m.para("Dubbelklickar du i stället direkt på **TheAbbeyOfCrimeExtensum.jar** startar spelet "
           "på engelska. Det är startskriptet som väljer svenska.", before=6)

    # ---- 5. controls
    m.heading("Styrning")
    m.para("ALLMÄNT").style = m.doc.styles["Underrubrik"]
    m.para("**F1**: Växla mellan helskärm och fönster")
    m.para("**Esc**: Paus/meny")
    m.para("**Enter**: Visa kartan (när den finns)")
    m.para("**Mellanslag**: Visa nästa replik i ett samtal (bara i mellansekvenser)")
    m.para(ui["CLASSIC"]).style = m.doc.styles["Underrubrik"]
    m.para("**Högerpil/vänsterpil**: Vänd dig")
    m.para("**Uppåtpil**: Gå framåt")
    m.para("**Nedåtpil**: Låt Adso gå åt det håll du är vänd åt")
    m.para(ui["DIRECTIONAL"]).style = m.doc.styles["Underrubrik"]
    m.para("**Piltangenterna**: Gå åt det håll du väljer")
    m.para("**Högerklick**: Vänd dig mot muspekaren")
    m.para("**W**: Gå åt det håll du väljer")
    m.para("**Vänsterklick**: Gå mot muspekaren")
    m.para("**Mellanslag**: Styr Adso")
    m.para("ADSO").style = m.doc.styles["Underrubrik"]
    m.para("Du kan styra Adso, men bara när han är i samma bild som Vilhelm. Så länge du håller "
           "ned **nedåtpilen** (**mellanslag** med " + ui["DIRECTIONAL"] + ") går Adso åt det håll "
           "som Vilhelm är vänd åt, om inget hinder står i vägen. Du plockar upp ett föremål genom "
           "att helt enkelt ställa dig framför det. Vissa föremål måste Vilhelm ta, andra Adso.")

    # ---- 6. game screen
    m.heading("Spelskärmen")
    m.picture(img["game_screen"], 15.0, before=0, after=8)
    m.para("På skärmen syns följande:", keep=True)
    hours = ui["HOURS"]
    items = [
        "**Vilhelm av Occam**: figuren som du styr.",
        "**Adso av Melk**: Vilhelms novis. I vissa lägen måste du styra honom för att komma vidare.",
        "**Föremål**: det du bär på för tillfället.",
        "**Dag**: Spelet pågår i sju dagar, och det är den tid du har på dig att lösa gåtan.",
        "**Timme**: Varje dag är indelad i " + ", ".join(hours[:-1]) + " och " + hours[-1] + ".",
        ("**Obsequium**: lydnadsmätaren, som sjunker varje gång du blir tillrättavisad för att ha "
        "brutit mot någon regel. Om den töms är spelet slut."),
        ("**Olja**: en mätare som visar hur mycket olja det finns kvar i lampan. Varje dag i "
        "gryningen förlorar du lampan om du har använt den, och då måste du skaffa en ny."),
        "**Abboten**: visar om abboten sover i sin cell.",
        ("**Alternativ kamera**: När den här symbolen syns kan du se vad som händer på andra "
        "platser i klostret, om du står stilla en stund."),
    ]
    for n, text in enumerate(items, 1):
        m.numbered(n, text, after=3)
    m.para(f"Obs! Punkt 7, 8 och 9 kan stängas av i menyn med alternativet **{ui['EXTRAS']}**.",
           before=4)

    # ---- 7. menu
    m.heading("Menyn")
    m.picture(img["menu"], 16.0, before=0, after=10)
    m.para("Med **Esc** pausar du spelet och menyn visas. Där finns följande val:", keep=True)
    bullets = [
        f"**{ui['CONTINUE']}**: spela vidare.",
        (f"**{ui['SAVE']}** och **{ui['LOAD']}**: spara spelet och ladda in det igen. Det finns "
        "plats för sju sparade spel."),
        # The first value has a comma of its own, so each value gets its explanation in
        # parentheses and the list runs 'mellan X (…), Y (…) och Z (…)'.
        (f"**{ui['SOUND']}**: välj mellan **{ui['VOICES_SFX']}** (figurernas ordlösa mummel när "
        f"de talar, plus effekter och omgivningsljud), **{ui['SFX']}** (bara effekter och "
        f"omgivningsljud) och **{ui['SILENCE']}** (varken röster eller effekter)."),
        f"**{ui['MUSIC']}**: slå på (**{ui['ON']}**) eller stäng av (**{ui['OFF']}**) musiken.",
        (f"**{ui['CLASSIC']}** eller **{ui['DIRECTIONAL']}**: välj hur du vill styra "
        "(se avsnittet Styrning)."),
        (f"**{ui['FULLSCREEN']}**: spela i helskärm (**{ui['ON']}**) eller i fönster "
        f"(**{ui['OFF']}**)."),
        f"**{ui['EXTRAS']}**: visa eller dölj punkt 7, 8 och 9 i föregående avsnitt.",
        f"**{ui['RESTART']}**: börja om från början.",
        f"**{ui['EXIT']}**: avsluta spelet.",
    ]
    for b in bullets:
        m.para("•\t" + b, indent=1.0, first=-0.5, after=4)
    m.para(f"Väljer du **{ui['RESTART']}** eller **{ui['EXIT']}** förlorar du allt som du inte "
           "har sparat.", before=8)

    # ---- 8. cutscenes
    m.heading("Mellansekvenser")
    m.picture(img["cutscene"], 16.0, before=0, after=10)
    m.para("Ibland visar spelet mellansekvenser som fördjupar delar av handlingen. Medan en sådan "
           "pågår kan du inte styra figurerna.")
    for n, text in enumerate([
        "När en mellansekvens pågår syns ett svart fält överst i spelytan.",
        "Figuren som talar.",
        ("När den här symbolen syns kan du trycka på **mellanslag** för att visa nästa replik "
        "direkt, om du inte vill vänta tills texten går vidare av sig själv."),
    ], 1):
        m.numbered(n, text, after=5)

    # ---- 9. contact
    m.heading("Kontakt")
    m.para("Kontakta oss om du har synpunkter, frågor eller problem som gäller spelet.", after=6)
    # A translator's note in smaller type (not italic: the .docx embeds only Junicode
    # regular and bold).
    m.para("Den svenska översättningen är inofficiell och inte gjord av spelets upphovsmän. "
           "Skicka därför inte frågor om den till adresserna nedan.", size=11.5, after=14)
    for label, url, text in [
        ("webb", SITE, SITE),
        ("e-post", "mailto:" + MAIL, MAIL),
        ("Facebook", FACEBOOK, FACEBOOK),
        ("Twitter", TWITTER, TWITTER),
    ]:
        m.para(label, align=C, after=2, keep=True)
        p = m.para(align=C, after=12)
        m.link(p, url, text)

    # ---- 10. credits
    m.heading("Medverkande")
    # Left-aligned like the BAKGRUND drop cap: justified, the short lines beside the initial
    # opened very wide word gaps (no Swedish hyphenation dictionary for LibreOffice here).
    m.dropcap("Detta är vår hyllning till en guldålder med nutellamackor, kulspel, utflykter till "
              "mystiska platser, nyupptäckta känslor, lek ute på gatan, bra musik och bra film. "
              "En tid då datorspel var magi gjord av prickar på en skärm, en magi som förändrade "
              "våra liv för alltid och som ledde fram till det spel som vi nu i all ödmjukhet har "
              "försökt tolka på nytt.", align=WD_ALIGN_PARAGRAPH.LEFT, after=8)
    m.para("En tid och ett sätt att se på livet. Kalla det gärna nostalgi.", size=14, after=8)
    m.picture(img["photo"], 15.0, before=2, after=4)
    m.para("Från vänster: Manuel Pazos, Juan Delcán, Daniel Celemín (Retro Barcelona 2014)",
           align=C, size=10, after=10)
    p = m.para(align=C, after=4)
    m.rich(p, "Efter spelet ”")
    r = p.add_run("LA ABADÍA DEL CRIMEN")
    r.bold = True
    r.font.color.rgb = RED
    m.rich(p, "”")
    m.para("skapat av Paco Menéndez och Juan Delcán 1987", align=C, size=13.5)

    credits = [
        ("PROGRAMMERING", ["Manuel Pazos"]),
        ("GRAFIK", ["Daniel Celemín"]),
        ("MUSIK", ["David Cañadas"]),
        ("LADDNINGSBILD", ["Antonio Giner och Daniel Celemín"]),
        ("SLUTBILD", ["Juan Delcán"]),
        ("PRODUKTION AV TEASERTRAILER", ["Christian Catalán"]),
        ("BERÄTTARRÖST I TEASERN", ["José María Carnicero"]),
        ("ENGELSK ÖVERSÄTTNING", ["Augusto Ruiz"]),
        ("TESTARE", ["Sandro Celemín", "Javier Pazos", "Augusto Ruiz", "Fran Loscos Gil (Metr81)"]),
    ]
    first = True
    for role, names in credits:
        p = m.para(align=C, before=10, after=3, keep=True, page_break=first)
        r = p.add_run(role)
        r.bold = True
        r.font.size = Pt(11.5)
        first = False
        for name in names:
            m.para(name, align=C, after=3)

    # ---- 11. greetings
    m.heading("Tack")
    m.para("**Från Daniel Celemín:**", keep=True, after=4)
    m.para("Jag vill tacka hela min familj, min fru Emma och mina två söner, för att de har stått "
           "ut med mina upp- och nedgångar. Pojkarna har inte slutat sjunga teaserns melodi sedan "
           "vi gjorde den, och de har testat spelet… Sandro: ”tryck på Z”, och Hugo: ”Nej”… Tack "
           "också till Dani, som var med när idén föddes… och till Manuel, som jag till slut "
           "lyckades övertala och som gick med på att arbeta med projektet!!!… Jag har lagt så "
           "många år på det här spelet att jag skulle behöva tacka alla som har delat den tiden "
           "med mig… men platsen räcker inte till. Tack.", after=10)
    m.para("**Från Manuel Pazos:**", keep=True, after=4)
    for t in [
        ("Tack till min fru Raquel och mina barn, som lät mig lägga min knappa fritid på det här "
        "projektet i stället för att vara mer med dem."),
        ("Tack till min bror Javi, för att han alltid finns där och lyssnar på mitt svammel, "
        "ibland utan att förstå vad jag pratar om."),
        ("Tack till Antonio Giner, för att han hängde med och hjälpte mig att lägga dit och plocka "
        "bort stenar i klostrets murar."),
        "Tack till VIGASOCO för hans utmärkta arbete.",
        ("Tack till José Antonio Morales, som alltid tog emot mig med ett leende och lånade mig "
        "spelets originalomslag."),
    ]:
        m.para(t, after=6)
    m.para("**Från oss båda:**", keep=True, before=4, after=4)
    for t in [
        "Tack till Paco Menéndez och Juan Delcán för att de skapade **Spelet**.",
        "Tack till Jaume Esteve och Enrique Collinet för deras hjälp.",
        ("Tack till våra vänner, kolleger, bekanta och följare, som har stöttat oss under alla "
        "dessa år, och till medlemmarna i Retroworks för deras synpunkter."),
    ]:
        m.para(t, after=6)
    m.picture(img["retroworks"], 3.4, before=2, after=0)

    # ---- 12. in memoriam and copyright
    m.para("**Till minne av Paco Menéndez**", align=C, before=250, after=2, page_break=True,
           size=13.5)
    m.para("”I skuggan dör genier utan att veta om sin magi”", align=C, size=13.5, after=26)
    m.para("**Till minne av Umberto Eco**", align=C, size=13.5, after=2)
    m.para("Utan att själv veta om det satte han med sitt verk sin prägel på en hel generation.",
           align=C, size=13.5)
    for i, t in enumerate([
        "La Abadía del Crimen copyright 1987 Opera soft",
        "La Abadía del Crimen Extensum copyright 2016 Daniel Celemín och Manuel Pazos.",
        "Kommersiell användning av denna produkt är förbjuden.",
        "Den svenska översättningen är en inofficiell version för privat bruk.",
    ]):
        m.para(t, align=C, size=9, before=230 if i == 0 else 0, after=5)
    return m


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the Swedish user manual (.docx and .pdf).")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--no-pdf", action="store_true", help="write only the .docx")
    mode.add_argument("--links-only", action="store_true",
                      help="only add the link annotations to an existing manual/Användarmanual.pdf")
    args = ap.parse_args()

    if args.links_only:
        if not OUT_PDF.exists():
            sys.exit(f"{OUT_PDF.relative_to(ROOT)} does not exist")
    else:
        ui = ui_strings()
        prolog = prologue()
        img = build_images()
        manual = build(img, ui, prolog)
        if manual.headings != HEADINGS:
            sys.exit(f"section headings changed: {manual.headings}; update HEADINGS")
        manual.save(OUT)
        print(f"wrote {OUT.relative_to(ROOT)}")
        for k, v in img.items():
            print(f"  image {k}: {v.relative_to(ROOT)}")
        if args.no_pdf:
            return
        convert_pdf()
    counts = add_pdf_links(OUT_PDF)
    check_pdf(OUT_PDF, HEADINGS)
    print(f"PDF links: {sum(counts.values())} ({', '.join(f'{u} x{n}' for u, n in counts.items())})")
    print("PDF checked: a link on every page, headings searchable as whole words")


if __name__ == "__main__":
    main()

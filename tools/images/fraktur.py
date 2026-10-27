# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Fraktur typesetting kit for the Swedish credit screens (images.md §3.1, FORMAT §6.2).

Read-only library for the intro image builders (novela, pacoyjuan, pelicula) plus a small CLI.
Pure Python + Pillow, integer glow arithmetic, no randomness: the same inputs give byte-identical
output. Nothing is computed at import; the font is built on first use (~1 s). Inputs (read-only):
work/jar/res/<lang>/intro/*.png and the Phase A inventory
work/phaseA/images/glyphs/{index.json,font_metrics.json,fraktur/*_mask.png}. Writes nothing
except where a CLI command or save_rgba_png() is told to.

USE FROM A BUILDER in tools/images/ (its PEP 723 header needs "pillow==11.3.0"; the script's own
directory is on sys.path, so):   import fraktur as fk

THE COLOUR MODEL (measured on all 16 es/en/it/fr credit images, not assumed)
  Every pixel is cream text F=(253,246,231) with coverage c, composited OVER a glow of colour
  G=(29,8,27) with alpha g:   A = c + g(1-c),   RGB = (F c + G g (1-c)) / A.
  The glow is   g = min(1, 2 * T(c))   where T is a 7-px box blur applied twice per axis
  (a 13x13 separable tent, weights 1..7..1 / 49 per axis, zero outside the image). That gives
  the documented median glow alpha 226/153/91/51/24/11/3/0 at 1..8 px from the core.
  Re-rendering the shipped images from their own decomposed coverage with this rule gives an
  alpha error of at most 2 levels (4 next to a script conjunction) and an RGB error of at most 2
  (`selftest` gates both: alpha <= 4, RGB <= 2, over every pixel outside HAND_PAINTED, the
  hand-painted í accent of es manuydani, whose weaker glow is reported but not gated).
  The script conjunctions (y/and/e/et) are cream coverage WITHOUT glow: pass their boxes as
  `script_boxes` (SCRIPT_BOXES holds the shipped ones) so their coverage stays out of the glow.

  So edits happen in coverage space and the glow is regenerated from the union of all cores
  (never stacked per glyph). render() rewrites a pixel only if its coverage or its model glow
  changed: pixels farther than 6 px from every changed coverage pixel are the base's bytes, and
  pixels whose coverage did not change keep the base's own glow plus the model's glow delta, so
  kept text keeps its exact pixels except where removed or added text's glow overlapped it.

THE GLYPHS AND THE SPACING
  The credits were rendered with half-pixel horizontal positioning: every letter exists in two
  phase variants (0 and 1, half a pixel apart), and the clean occurrences of one (char, phase)
  are identical to within 1 level. A Font builds each variant on a common (pen x, baseline)
  frame, free of fragments of old neighbours: where the Phase A ownership gives a pixel to two
  letters (a join or an overlap: the shipped value is their union, and a fragment only adds
  coverage), only the occurrences that own that pixel alone vote (per-pixel lower median), and
  members whose own pixels disagree by more than 3 levels are dropped; a pixel shared in EVERY
  occurrence (P before a in 'Pazos', U after ’ in 'd’Umberto') is the union minus the
  neighbour's own shape, wherever that shape is known from occurrences owning the pixel alone
  (fragment_audit() checks it: every word-initial/final occurrence equals its variant within 2
  levels on its own pixels, and no variant keeps a neighbour's ink). A copy (the same word at
  nearly the same place in another language's version of the image, or the same letter there
  with identical pixels, as en 'Celemin' / es 'Celemín') counts once, in the medians and in the
  spacing fit.
  Spacing: pen positions accumulate fractional advances R[a] + L[b] fitted by least squares on
  every shipped line (409 letter pairs, copied pairs once; mean residual 0.1 px), plus each observed pair's mean
  residual shrunk by n/(n+1) (the font's own kerning); rounding the pen to half pixels picks the
  phase. The WORD SPACE is the font's too: on the es/en/fr lines, a fit with one start per line,
  one space advance and no kerning places the 60 word starts (|residual| mean 0.1 px, max 0.3)
  as exactly as the 274 letters inside words (mean 0.1 px, max 0.4), so the lines were typeset
  as whole strings, not spaced by hand; the 10-12 px ink gaps Phase A
  measured are that space plus the letters' side bearings. word_gap=None (default) reproduces
  it; an explicit word_gap (ink px) is for hand-fitting a word into a fixed place.
  ALTERNATES lists occurrences that are not plain letters (the swash 'by' of en novela, and T, L,
  the 'El' E carrying the second stroke of “, which was cut into the next capital; “ itself has
  only its first stroke): they are out of the medians and out of every 'lang:image' source,
  reachable only by occurrence id; their spacing uses Font.pen_offset() (the pen a plain glyph
  of the same char would have in their place).
  Sides no shipped pair shows (in the full font only the left of 'à' and the right of '”') are
  guessed from the ink extent plus the median side bearing; line() flags every glyph placed with
  such an advance (glyph dict spacing_guessed=True) and issues a FrakturSpacingWarning.

API (all boxes inclusive x0,y0,x1,y1 with x1 >= x0 and y1 >= y0: an inverted box raises
  ValueError everywhere; images are PIL images or paths; coverage is 0..255)
  Typical builder (de = en base; the shipped intro images are shipped(lang, image)):
      L3 = "by Umberto Eco"                               # Phase A line texts: see occurrences()
      cv = fk.Canvas.shipped("en", "novela")              # base + its SCRIPT_BOXES, the safe way
      cv.erase((21, 88, 300, 122))                        # old line 1: its words + their glow
      cv.draw(fk.line("efter romanen", 28, 114))          # x = left ink edge, baseline row
      um = fk.letters("en", "novela", L3, "Umberto Eco")  # the kept name, letter-exact pixels
      u_id = um.glyphs[0]["source"]                       # its 'U' (an occurrence id)
      dx = fk.align_before(u_id, "av ", 40)               # 'av' on the left edge of line 2 (x 40)
      cv.erase_letters("en", "novela", L3)                # the whole old line 3, letter-exact
      cv.draw(um.moved(dx, 0))                            # the name, moved whole pixels
      cv.draw(fk.line_before(u_id, "av ", dx))            # 'av' + the font's space before the 'U'
      img = cv.render()
      assert fk.moon_pixels(img) == []                    # no ink or glow in the moon window
      fk.save_rgba_png(img, out_path)

  ERASE vs CUT vs LETTERS (one meaning each, everywhere):
    erase   = remove connected components: every 8-connected coverage component (c > 0) with at
              least half of its mass inside the box goes, including its anti-aliased fringe
              outside the box. Inside a word a component is often 2-4 joined letters ('ins',
              'Rose', 'Anna'), never a whole line, and no component crosses a word gap or a line
              in the shipped images, so box WHOLE WORDS or lines. If the box splits a component
              (one left in place has ink, coverage >= 128, inside the box, or one taken has ink
              outside it) erase raises ValueError and changes nothing, unless partial_ok=True.
              Canvas.erase, Canvas.erase_text (the same), composite(erase=...), module erase().
              whole_letters=False turns it into a cut.
    letters = letter-exact, from the Phase A ownership of every shipped letter: letters() cuts
              them as a block, Canvas.erase_letters() removes them (a pixel shared with a kept,
              joined letter stays with that letter), block(..., letters=True) selects them by box.
    cut     = zero every coverage pixel inside the box and nothing outside it (it CAN slice a
              kept letter's fringe). Canvas.cut, composite(cut=...).
    All take the removed text's glow away and regenerate the kept neighbours' glow from the
    remaining cores (never eaten).

  font = default_font()                 # Font(exclude=pred) builds one without some occurrences
  font.chars(), font.phases(ch)         # typesettable chars (incl. composed ä ö å; line() takes
                                        # å only with allow_ring=True), phases 0/1
  font.glyph(ch, phase=0, source=None)  # Glyph: coverage patch + offsets to (pen x, baseline);
                                        # source = an occurrence id or "lang:image" (preferred crop);
                                        # immutable (data/members are tuples), shared by every line
  fragment_audit(font=None)             # the fragment checks the selftest gates (see THE GLYPHS)
  font.advance(a, b, spaces=0)          # pen advance a -> b in px (the font's kerning included)
  font.side_n(ch, "L"/"R"), font.advance_guessed(a, b)   # spacing evidence: pairs seen per side;
                                        # the unobserved sides an advance uses ([] = none)
  font.image_candidates(ch, lang, image, phase=None)     # the plain occurrences a "lang:image"
                                        # source picks from, in the order it picks them
  lay = line(text, x, baseline, kern=None, prefer=None, word_gap=None, first_phase=None, pen=None,
             allow_ring=False)
        x = left ink edge of the first glyph, an int (or pen = its fractional pen x instead; not
        both), baseline = last ink row of the x-height letters, an int (shipped: 114/144/174, or
        126/156; pitch 30); a float x or baseline raises ValueError (centre with //).
        first_phase = None (0 where the first letter has it) / 0 / 1 (ValueError if the letter
        lacks it, with pen=, or with a half-pixel kern on the first glyph; as word_gap phases).
        kern = {index: px} (index into text, not a space) and/or {"ab": px} (a pair
        that occurs in text as two adjacent glyphs), px an int or float; any other key or value
        raises ValueError; a kern
        moves that glyph's pen and everything after it, 0.5-px steps select the other half-pixel
        phase (also on the first glyph and on a word start placed by word_gap).
        prefer = {char or index: occurrence id or "lang:image"} (a char key must occur in text);
        a "lang:image" source picks a plain occurrence of that image (variant members first,
        never an ALTERNATES shape) and puts the letter on a half pixel the image has it at
        (KeyError up front if it has none). Two adjacent letters of one shipped line given by id
        keep their shipped relative position (a kern moves the second, snapped to its phase).
        word_gap = None (the font's own space) / ink px (>= 0) for every gap / a list with exactly
        one entry per gap, each px or (px, phase) (ValueError for a wrong length, a negative gap,
        a phase the letter lacks, or a phase plus a half-pixel kern). -> Layer; lay.glyphs = one
        dict per glyph: char, index (into text, spaces counted: what kern=/prefer= take),
        letter_index (spaces not counted), x, phase, pen, model_pen, baseline, ink_left,
        ink_right, source, glyph, mark_fit, mark_gap, mark_crowded, spacing_guessed (the last
        two + a FrakturSpacingWarning). ValueError without x or pen.
        An opening ” before a capital is fitted to 1 px of ink, and every mark (i-dot, accent,
        composed ä/ö/å) keeps 2 px from the letters on both sides where 1 px of fit allows it,
        see MARKS. allow_ring: the composed å is unreviewed (THE COMPOSED LETTERS); text with
        an å raises ValueError unless allow_ring=True (line_before/line_after pass it on).
  lay = line_after(occurrence_id, text, dx, dy)   # continue after a shipped glyph ('Annaud'+'s')
  lay = line_before(occurrence_id, text, dx, dy)  # end before a shipped glyph ('av ' + 'Umberto');
                                        # its LAST glyph is within 0.25 px of the font's advance
                                        # before the kept glyph, word_gap= included (searched);
                                        # where no start lands it (marks, a fixed phase), the
                                        # nearest start + to_kept_off=True + a FrakturSpacingWarning
  dx  = align_before(occurrence_id, text, x)      # the dx that starts line_before's text at x
  lay = letters(lang, image, line_text, idx=None, box=None)   # shipped letters, letter-exact:
                                        # idx = int / slice / list / substring ('Umberto Eco')
  lay = block(lang, image, box)         # shipped coverage as a pixel block ('Umberto Eco',
                                        # 'Paco Menéndez', 'Jean-Jacques Annaud'): the connected
                                        # components mostly inside the box (box whole words;
                                        # ValueError if it splits one, unless partial_ok=True),
                                        # glow excluded (it is regenerated); letters=True: the
                                        # letters mostly inside the box; whole_components=False:
                                        # a hard crop
  lay = Layer.from_rgba(img, x, y)      # cream-on-alpha ink (e.g. script_och.och_layer()) as coverage
  lay.moved(dx, dy), lay.bbox(), lay.ink_bbox(), Layer.union([...])   # moved: whole px (int) only
  occurrences(lang, image, line_text, char) -> [Occurrence] (.id, .char, .p, .xint, .phase, ...;
                                        lang 'de' = 'en')
  ink_left(occ), ink_right(occ)         # ink columns (coverage >= 128) of a shipped glyph
  cv = Canvas.shipped(lang, image)      # a shipped intro image with its SCRIPT_BOXES (de = en)
  cv = Canvas(base, script_boxes)       # base: path / PIL image (any mode, converted to RGBA).
                                        # script_boxes is required: a path to a shipped image
                                        # finds its own; anything else raises TypeError unless
                                        # the boxes (or an explicit () = no script ink) are given
  cv.erase(box, whole_letters=True, partial_ok=False)  # see ERASE vs CUT vs LETTERS; returns the
                                        # removed components' bboxes
  cv.erase_text(box)                    # = erase(box)
  cv.erase_letters(lang, image, line_text, idx=None, box=None)   # letter-exact (see letters())
  cv.cut(box)                           # see ERASE vs CUT vs LETTERS
  cv.erase_layer(lay)                   # remove exactly the pixels a Layer covers (a block();
                                        # for letters() prefer erase_letters: joins stay whole)
  cv.draw(lay, clip_ok=False)           # add Fraktur coverage (sum, clamped); it gets the glow.
                                        # ValueError (nothing drawn) if any coverage falls off the
                                        # canvas, unless clip_ok=True
  cv.draw_script(lay, clip_ok=False)    # add script ink (the conjunctions): coverage, NO glow
  cv.coverage_layer(box=None, script=False)   # current coverage in the box (clamped to the image)
  img = cv.render()                     # RGBA PIL image; cv.changed_box() = bbox of rewritten px
  composite(base, lays, erase=boxes, cut=boxes, script_boxes=None, partial_ok=False,
            clip_ok=False) -> RGBA
  erase(base, boxes, whole_letters=True, script_boxes=None, partial_ok=False) -> RGBA   # one shot
  save_rgba_png(img, path) # deterministic RGBA PNG: IHDR, one IDAT, IEND (no gAMA/iCCP/pHYs)
  moon_pixels(img)         # [(x,y)] in the moon window x >= 250, y < 100 with alpha > 0: the
                           # acceptance rule is moon_pixels(img) == []. moon_pixels(img, base=b)
                           # (alpha above b's) is a diagnostic only, NOT the rule: es pacoyjuan
                           # and en pelicula ship with glow there that a build must not keep
  diff_pixels(a, b)        # [(x,y)] where two RGBA images differ
  SCRIPT_BOXES[(lang, image)]  # script conjunction boxes of the shipped images, de = en

THE COMPOSED LETTERS (optional; the GLOSSARY §8 wordings need none)
  ä, ö = a, o + two copies of the font's own i-dot tick. Each tick sits over a stem of the
         letter the way the i's tick sits over the i's stem (0.9 px right of the stem's coverage
         centroid, measured on both i phases), rounded to the half pixel, plus DOT_SHIFT (o: the
         o's top narrows at the right, and the rule's right tick hung past that corner, so both
         of its ticks sit 0.5 px further left); the offsets are the same for both phases (a and o:
         -2.5/+2.5 px from the pen), so the ticks are 3 px apart in clear ink on both phases.
  å    = a + a ring on the pixel grid (RING_PATTERN: an elliptical ring 6 px wide (faint
         edges) and 4 rows tall, sheared 0.25 px per row like the i-dot tick, so its top row sits
         0.66 px right of its bottom row; cores 221/255, a dark 2x2 hole <= 51) in rows -21..-18
         (the accents' rows), centred on the whole pixel nearest 0.5 px right of the umlaut
         ticks' midpoint (the font's accents sit right of centre); the same pixels on both
         phases. NOT FOR USE WITHOUT REVIEW: the font has no ring to copy, and no GLOSSARY §8
         wording has an å. Enforced: line() raises ValueError on text with an å unless the
         caller passes allow_ring=True (after looking at the result at 4x and 6x).
  ”    before a capital (the Swedish opening quote, ”Rosens) never occurs in the shipped lines,
       so its right side is unobserved. The capital is moved left in half-pixel steps until its
       ink comes within 1 px of the quote's (per row, coverage >= 128): the gap measured between
       the shipped opening “ and its capital in all three images (en “T, es “E, fr “L: 1 px).
       An explicit kern on that pair or index switches the fit off.

MARKS (the mark fit; MARKED = i í é á à ê ä ö å, the letters whose ink above the x-height is a
  separate mark, not part of an ascender or capital; the selftest derives the set from the glyphs)
  Every shipped mark keeps >= 2 clear px (Chebyshev, ink = coverage >= 128) from the next
  letter's ink (film: il 2; Delcán, Menéndez, même: 2) and >= 3 from the letter before (film:
  fi 3). The fitted spacing alone does not always: é/á/í before an ascender or a capital overlap
  it (-1 px), i before h or k keeps 1 px at some pen phases. So line() moves a glyph right
  (half-pixel steps, at most MARK_MAX_SHIFT = 2 half px (1 px), the rest of the line with it) until
  MARK_MIN_GAP = 2 clear px separate both its own mark from the previous glyph's ink and the
  previous glyph's mark from its ink (same word only). Glyph dict: mark_fit = the half px moved,
  mark_gap = the clear px left, mark_crowded = still under 2 px (then a FrakturSpacingWarning).
  Measured over every letter at pen phases 0, .25, .5, .75, in both orders (selftest):
    composed ä/ö/å: every Swedish letter before or after keeps >= 2 px, except a capital I
      directly after ö (1 px, flagged). The fit moves fä, äh, äI, äN, and after ö: b d h k l and
      the capitals A D I M N R U (each at some pen phases).
    the font's own i: the fit moves ih, ik, iI, iN, iU at some pen phases (no shipped line has
      them; 'film', 'il' keep their 2 px unmoved); iI stays at 1 px (flagged).
    é á í ê à (Spanish/French): before an ascender or a capital 1 px is not enough (éd -1 -> 0
      px): flagged. No Swedish wording has one.
  An explicit kern on that glyph (index or pair) switches the fit and the warning off. The three
  Swedish credit wordings (GLOSSARY §8) and the re-typeset shipped lines come out unchanged.

CLI
  uv run tools/images/fraktur.py selftest [--out DIR]  acceptance test -> work/phaseD/fraktur-kit/selftest/
  uv run tools/images/fraktur.py demo [--out DIR]      the Swedish wordings on es/en bases (API demo,
                                                       not the shipped assets) -> .../fraktur-kit/demo/
  uv run tools/images/fraktur.py info                  metrics, variants, spacing table, alternates
  uv run tools/images/fraktur.py sheet [--out PNG]     every glyph variant at 6x
  uv run tools/images/fraktur.py typeset TEXT --x X --baseline Y [--base PNG] [--erase BOX]...
                                 [--partial-ok] [--cut BOX]... [--script BOX]... [--word-gap N]
                                 [--phase P] [--allow-ring] [--clip-ok] [--out PNG]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
import warnings
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "work" / "jar" / "res"
GLYPHS = ROOT / "work" / "phaseA" / "images" / "glyphs"
KIT_OUT = ROOT / "work" / "phaseD" / "fraktur-kit"

F = (253, 246, 231)                  # cream core
G = (29, 8, 27)                      # glow colour
GLOW_GAIN = 2                        # g = min(1, GLOW_GAIN * T(c))
GLOW_BOX_R = 3                       # box of 2*3+1 = 7 px ...
GLOW_PASSES = 2                      # ... applied twice per axis
GLOW_R = GLOW_BOX_R * GLOW_PASSES    # support radius of T: 6 px
GLOW_NORM = (2 * GLOW_BOX_R + 1) ** (2 * GLOW_PASSES)   # 7^4 = 2401
X_HEIGHT = 17                        # rows baseline-16 .. baseline
CAP_TOP = 21                         # cap/ascender top = baseline - 21
LINE_PITCH = 30
KERN_SHRINK = 1.0                    # pair kerning = sum(residuals) / (n + KERN_SHRINK)
SUBTRACT_NOISE = 8                   # a union minus a neighbour's median shape at or below this is 0
                                     # (coverage comes in steps of 17; clean copies agree within 1-2)
MOON = (250, 0, 319, 99)             # inclusive: the moon window clip (250,0,70,100)

# Script conjunctions in the shipped images (ink box from images.md §2 padded by 1 px for AA).
SCRIPT_BOXES = {
    ("es", "manuydani"): [(73, 149, 83, 165)], ("en", "manuydani"): [(49, 142, 82, 158)],
    ("it", "manuydani"): [(75, 143, 84, 155)], ("fr", "manuydani"): [(57, 150, 75, 165)],
    ("es", "pacoyjuan"): [(65, 165, 75, 181)], ("en", "pacoyjuan"): [(46, 157, 79, 173)],
    ("it", "pacoyjuan"): [(58, 162, 67, 173)], ("fr", "pacoyjuan"): [(52, 168, 70, 181)],
    ("es", "pelicula"): [(27, 105, 37, 121)], ("en", "pelicula"): [(26, 77, 59, 93)],
    ("it", "pelicula"): [(38, 82, 47, 93)], ("fr", "pelicula"): [],
    ("es", "novela"): [], ("en", "novela"): [], ("it", "novela"): [], ("fr", "novela"): [],
}
LANGS = ("es", "en", "it", "fr")
IMAGES = ("manuydani", "pacoyjuan", "novela", "pelicula")
SCRIPT_BOXES.update({("de", i): SCRIPT_BOXES[("en", i)] for i in IMAGES})   # de == en byte for byte

# Composed letters and the opening quote (see THE COMPOSED LETTERS in the header).
STEM_ROWS = range(-11, -4)           # rows (rel. baseline) where a, o, i have plain vertical stems
TICK_ROWS_TOP = -X_HEIGHT            # the i-dot tick = the i's rows at or above baseline - 17
# Half px added to both umlaut ticks after the i-rule (Font.dot_offsets). o: -1. The o narrows at
# its top right (its top-right ink is 2 px left of its right stem), so the i-rule's right tick
# (0.9 px right of the stem: pen +3 px) hung past that corner and crowded a following ascender:
# 0-1 clear px before h, k, d, l, b and every capital, and still 0-1 for h, k, N, U after 1 px of
# mark fit. At pen -2.5/+2.5 px (the ä's offsets) both ticks still sit over the stems, centred on
# the letter, 3 clear px apart on both phases, and the fit clears every following letter but I.
DOT_SHIFT = {"o": -1}
# å ring (the font has no ring to copy): an elliptical ring, outer radii 2.1 x 2.05 px, inner
# 1.15 x 1.05 px, sheared 0.25 px per row (the slant of the font's own i-dot tick: its top row
# sits ~0.8 px right of its bottom row), 24x24 supersampled and quantised to the font's coverage
# steps of 17. The top row's ink sits 0.66 px right of the bottom row's, so the ring leans like
# the ticks and accents; the 2x2 hole stays dark (<= 51) and the sides keep 221/255 cores, so it
# reads as a ring at the game's 4x. The same pixels on both phases (no half-pixel blur). NOT FOR
# USE WITHOUT REVIEW: no GLOSSARY §8 wording has an å; look at it at 4x and 6x before shipping one.
RING_PATTERN = ((0, 51, 204, 255, 187, 0),
                (0, 221, 51, 17, 221, 34),
                (34, 221, 17, 51, 221, 0),
                (0, 187, 255, 204, 51, 0))
UNREVIEWED = "å"                     # composed letters line() takes only with allow_ring=True
RING_CY = -19.0                      # continuous y of the ring centre: rows -21..-18
RING_DX = 0.5                        # ring centre right of the umlaut ticks' midpoint (px)
QUOTE_CAP_GAP = 1                    # ink gap (px, per row) between an opening quote and its capital
# Letters whose ink at rows <= TICK_ROWS_TOP is a separate MARK (an i-dot tick, an accent, the
# composed umlaut ticks or ring) and not part of the body (ascenders and capitals reach those rows
# too, joined to their body): the font's own i, í, é, á, à, ê and the composed ä, ö, å. The
# selftest checks the set against the glyphs (a mark = ink above row TICK_ROWS_TOP, none on it).
MARKED = "iíéáàêäöå"
MARK_MIN_GAP = 2                     # clear px between a mark and the neighbouring glyphs' ink: every
                                     # shipped mark keeps >= 2 after it (film, Delcán, Menéndez, même)
                                     # and >= 3 before it (film, Celemín, película)
MARK_MAX_SHIFT = 2                   # ... kept by moving the later glyph right: at most 2 half px (1 px)
OPENING_QUOTES = "”"                 # a ” directly followed by a capital opens a quote



class FrakturSpacingWarning(UserWarning):
    """line() placed a glyph with an advance that uses a letter side no shipped pair shows
    (glyph dict 'spacing_guessed'); silence or escalate with the warnings module."""


_DR, _DG, _DB = F[0] - G[0], F[1] - G[1], F[2] - G[2]
_DD = _DR * _DR + _DG * _DG + _DB * _DB


# ----------------------------------------------------------------------------- pixels and PNG

def load_rgba(src) -> Image.Image:
    if isinstance(src, Image.Image):
        return src.convert("RGBA") if src.mode != "RGBA" else src.copy()
    return Image.open(src).convert("RGBA")


def shipped(lang: str, image: str) -> Path:
    if lang == "de":
        lang = "en"                  # de == en byte for byte (FORMAT §6.1)
    return RES / lang / "intro" / f"{image}.png"


def decompose_px(r: int, g: int, b: int, a: int) -> tuple[int, float]:
    """(coverage 0..255, glow alpha 0..1) of one pixel under the F-over-G model."""
    if a == 0:
        return 0, 0.0
    t = ((r - G[0]) * _DR + (g - G[1]) * _DG + (b - G[2]) * _DB) / _DD
    t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
    alpha = a / 255.0
    c = int(t * alpha * 255.0 + 0.5)
    if c >= 255:
        return 255, 1.0
    cq = c / 255.0
    gl = (alpha - cq) / (1.0 - cq)
    return c, (0.0 if gl < 0.0 else 1.0 if gl > 1.0 else gl)


def compose_px(c: int, gl: float) -> tuple[int, int, int, int] | None:
    """RGBA of coverage c (0..255) over glow gl (0..1); None if it rounds to transparent."""
    cf = c / 255.0
    alpha = cf + gl * (1.0 - cf)
    a8 = int(alpha * 255.0 + 0.5)
    if a8 <= 0:
        return None
    gw = gl * (1.0 - cf)
    return (int((F[0] * cf + G[0] * gw) / alpha + 0.5), int((F[1] * cf + G[1] * gw) / alpha + 0.5),
            int((F[2] * cf + G[2] * gw) / alpha + 0.5), min(255, a8))


def _box_pass_rows(src: list[int], w: int, h: int, r: int) -> list[int]:
    out = [0] * (w * h)
    for y in range(h):
        base = y * w
        pre = [0] * (w + 1)
        s = 0
        for x in range(w):
            s += src[base + x]
            pre[x + 1] = s
        for x in range(w):
            lo = x - r if x > r else 0
            hi = x + r + 1 if x + r + 1 < w else w
            out[base + x] = pre[hi] - pre[lo]
    return out


def _box_pass_cols(src: list[int], w: int, h: int, r: int) -> list[int]:
    out = [0] * (w * h)
    for x in range(w):
        pre = [0] * (h + 1)
        s = 0
        for y in range(h):
            s += src[y * w + x]
            pre[y + 1] = s
        for y in range(h):
            lo = y - r if y > r else 0
            hi = y + r + 1 if y + r + 1 < h else h
            out[y * w + x] = pre[hi] - pre[lo]
    return out


def tent_sums(cov: list[int], w: int, h: int) -> list[int]:
    """Unnormalised T(c): integer sums, divide by GLOW_NORM * 255 for a 0..1 value."""
    s = cov
    for _ in range(GLOW_PASSES):
        s = _box_pass_rows(s, w, h, GLOW_BOX_R)
    for _ in range(GLOW_PASSES):
        s = _box_pass_cols(s, w, h, GLOW_BOX_R)
    return s


def glow_of_sum(s: int) -> float:
    v = GLOW_GAIN * s
    lim = GLOW_NORM * 255
    return 1.0 if v >= lim else v / lim


def save_rgba_png(img: Image.Image, path) -> bytes:
    """Deterministic 8-bit RGBA PNG (IHDR, one IDAT with filter 0 rows at zlib level 9, IEND)."""
    img = load_rgba(img)
    w, h = img.size
    raw = img.tobytes()
    stride = 4 * w
    data = b"".join(b"\x00" + raw[y * stride:(y + 1) * stride] for y in range(h))

    def chunk(t: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + t + body + struct.pack(">I", zlib.crc32(t + body) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(data, 9)) + chunk(b"IEND", b""))
    if path is not None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(png)
    return png


def moon_pixels(img, base=None) -> list[tuple[int, int]]:
    """Pixels of the moon window (x >= 250, y < 100) with alpha > 0. THIS (no base) IS THE
    ACCEPTANCE RULE: credit ink and its glow stay out of the window, so a built image must give
    moon_pixels(img) == [].
    base= is a diagnostic only: the pixels whose alpha exceeds the base's (what an edit ADDED).
    It is NOT the rule: es pacoyjuan (17 px at x 250..252, y 93..99) and en pelicula (11 px at
    x 267..276, y 99, alpha 2-4) ship with glow in the window, and a build that kept that text (or
    part of its glow) would pass the base= check and still break the rule."""
    im = load_rgba(img)
    px = im.load()
    pb = load_rgba(base).load() if base is not None else None
    x0, y0, x1, y1 = MOON
    return [(x, y) for y in range(y0, min(y1 + 1, im.height)) for x in range(x0, min(x1 + 1, im.width))
            if px[x, y][3] > (pb[x, y][3] if pb is not None else 0)]


def diff_pixels(a, b) -> list[tuple[int, int]]:
    ia, ib = load_rgba(a), load_rgba(b)
    if ia.size != ib.size:
        raise ValueError(f"diff_pixels(): sizes differ {ia.size} vs {ib.size}")
    w = ia.width
    return [(i % w, i // w) for i, (p, q) in enumerate(zip(ia.getdata(), ib.getdata())) if p != q]


def bbox_of(points) -> tuple[int, int, int, int] | None:
    pts = list(points)
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


# ----------------------------------------------------------------------------- coverage layers

@dataclass
class Layer:
    """A coverage patch in image coordinates: data[(y-y0)*w + (x-x0)] in 0..255."""
    x0: int
    y0: int
    w: int
    h: int
    data: list[int]
    glyphs: list[dict] = field(default_factory=list)   # filled by line()
    text: str = ""

    def get(self, x: int, y: int) -> int:
        if self.x0 <= x < self.x0 + self.w and self.y0 <= y < self.y0 + self.h:
            return self.data[(y - self.y0) * self.w + (x - self.x0)]
        return 0

    def pixels(self):
        """Yield (x, y, c) for c > 0."""
        for j in range(self.h):
            row = j * self.w
            for i in range(self.w):
                c = self.data[row + i]
                if c:
                    yield self.x0 + i, self.y0 + j, c

    def ink_bbox(self, threshold: int = 128) -> tuple[int, int, int, int] | None:
        """Inclusive bbox of pixels with coverage >= threshold (128 ~ the Phase A ink rule)."""
        return bbox_of((x, y) for x, y, c in self.pixels() if c >= threshold)

    def bbox(self) -> tuple[int, int, int, int] | None:
        return bbox_of((x, y) for x, y, _ in self.pixels())

    def moved(self, dx: int, dy: int) -> "Layer":
        """A copy moved by whole pixels (its glyph dicts too)."""
        for v in (dx, dy):
            if isinstance(v, bool) or not isinstance(v, int):
                raise ValueError(f"Layer.moved({dx!r}, {dy!r}): blocks move whole pixels (int); "
                                 f"use line(..., pen=) or a kern for half pixels")
        gl = [dict(g, **{k: g[k] + dx for k in ("x", "pen", "model_pen", "ink_left", "ink_right") if k in g},
                   baseline=g["baseline"] + dy) for g in self.glyphs]
        return Layer(self.x0 + dx, self.y0 + dy, self.w, self.h, list(self.data), gl, self.text)

    @staticmethod
    def empty() -> "Layer":
        return Layer(0, 0, 0, 0, [])

    @staticmethod
    def from_rgba(img, x0: int = 0, y0: int = 0) -> "Layer":
        """Coverage of cream-on-alpha ink (an RGBA image, e.g. script_och.och_layer()) placed with
        its top-left at (x0, y0): each pixel decomposed under the F-over-G model (for pure cream
        pixels the coverage is the alpha). Draw script ink with Canvas.draw_script()."""
        im = load_rgba(img)
        data = [decompose_px(*q)[0] for q in im.getdata()]
        return Layer(x0, y0, im.width, im.height, data)

    @staticmethod
    def union(layers: list["Layer"]) -> "Layer":
        """Sum of coverages, clamped to 255 (exact for shapes that do not overlap)."""
        layers = [l for l in layers if l.w and l.h]
        if not layers:
            return Layer.empty()
        x0 = min(l.x0 for l in layers)
        y0 = min(l.y0 for l in layers)
        x1 = max(l.x0 + l.w for l in layers)
        y1 = max(l.y0 + l.h for l in layers)
        w, h = x1 - x0, y1 - y0
        data = [0] * (w * h)
        for l in layers:
            for j in range(l.h):
                src = j * l.w
                dst = (l.y0 - y0 + j) * w + (l.x0 - x0)
                for i in range(l.w):
                    v = l.data[src + i]
                    if v:
                        s = data[dst + i] + v
                        data[dst + i] = 255 if s > 255 else s
        out = Layer(x0, y0, w, h, data)
        for l in layers:
            out.glyphs.extend(l.glyphs)
        out.text = " ".join(l.text for l in layers if l.text)
        return out


# ----------------------------------------------------------------------------- canvas

def _check_box(box, what: str) -> tuple[int, int, int, int]:
    """box as a tuple of 4 ints (x0, y0, x1, y1), inclusive. ValueError for anything else and
    for an inverted box (x1 < x0 or y1 < y0): those would select nothing and leave old text in
    place without a word, e.g. a box with swapped coordinates."""
    try:
        t = tuple(box)
    except TypeError:
        raise ValueError(f"{what}: box {box!r}: give 4 ints (x0, y0, x1, y1), inclusive") from None
    if len(t) != 4 or not all(_is_int(v) for v in t):
        raise ValueError(f"{what}: box {box!r}: give 4 ints (x0, y0, x1, y1), inclusive")
    if t[2] < t[0] or t[3] < t[1]:
        raise ValueError(f"{what}: box {t} is inverted (x1 < x0 or y1 < y0; swapped coordinates?): "
                         f"boxes are inclusive (x0, y0, x1, y1) with x1 >= x0 and y1 >= y0")
    return t


def _shipped_key(base) -> tuple[str, str] | None:
    """(lang, image) if base is a path to one of the shipped credit images (work/jar/res)."""
    if not isinstance(base, (str, Path)):
        return None
    try:
        rp = Path(base).resolve()
    except OSError:
        return None
    for lang in LANGS + ("de",):
        for image in IMAGES:
            if rp == (RES / lang / "intro" / f"{image}.png").resolve():
                return (lang, image)
    return None


class Canvas:
    """An RGBA image in coverage space. Edit with erase/cut/draw/draw_script, then render().

    script_boxes (required): the boxes holding script ink (the conjunctions y/and/e/et), whose
    coverage gets no glow and adds none. Canvas.shipped(lang, image) supplies the shipped ones;
    a path to a shipped image finds its own; for any other base pass them, or () explicitly for
    an image without script ink. Leaving them out on an image that has a conjunction would treat
    it as glowing Fraktur, and erasing or replacing it would then take a glow it never had from
    the kept neighbours (en pacoyjuan: the 'J' of 'Juan' loses its glow)."""

    def __init__(self, base, script_boxes=None):
        key = _shipped_key(base)
        self.key = None if key is None else ("en" if key[0] == "de" else key[0], key[1])
        if script_boxes is None:
            if key is None:
                raise TypeError("Canvas(base, script_boxes): pass the base's script-ink boxes "
                                "(SCRIPT_BOXES[(lang, image)] for a shipped image, () if it has none), "
                                "or use Canvas.shipped(lang, image)")
            script_boxes = SCRIPT_BOXES[key]
        self.script_boxes = [_check_box(b, "Canvas script_boxes") for b in script_boxes]
        self.base_img = load_rgba(base)
        self.w, self.h = self.base_img.size
        self.base = list(self.base_img.getdata())
        n = self.w * self.h
        self.c0 = [0] * n            # glowing (Fraktur) coverage of the base
        self.s0 = [0] * n            # script coverage of the base (no glow)
        self.g0 = [0.0] * n          # decomposed glow alpha of the base
        script = [False] * n
        for (x0, y0, x1, y1) in self.script_boxes:
            for y in range(max(0, y0), min(self.h - 1, y1) + 1):
                for x in range(max(0, x0), min(self.w - 1, x1) + 1):
                    script[y * self.w + x] = True
        for i, (r, g, b, a) in enumerate(self.base):
            if a:
                c, gl = decompose_px(r, g, b, a)
                if script[i]:
                    self.s0[i] = c
                else:
                    self.c0[i] = c
                self.g0[i] = gl
        self.c = list(self.c0)
        self.s = list(self.s0)
        self._changed: set[int] = set()

    @classmethod
    def shipped(cls, lang: str, image: str) -> "Canvas":
        """The shipped intro image (lang 'de' = 'en') with its SCRIPT_BOXES."""
        return cls(shipped(lang, image), SCRIPT_BOXES[("en" if lang == "de" else lang, image)])

    # -- edits
    def _box_indices(self, box, what: str = "cut"):
        x0, y0, x1, y1 = _check_box(box, what)
        for y in range(max(0, y0), min(self.h - 1, y1) + 1):
            for x in range(max(0, x0), min(self.w - 1, x1) + 1):
                yield y * self.w + x

    def cut(self, box, script: bool = True) -> None:
        """Hard cut: zero all coverage (glowing and, unless script=False, script) inside the box
        and nothing outside it. It can slice a kept letter's anti-aliased fringe; erase() cannot."""
        for i in self._box_indices(box):
            self.c[i] = 0
            if script:
                self.s[i] = 0

    def erase(self, box, whole_letters: bool = True, min_inside: float = 0.5,
              partial_ok: bool = False) -> list[tuple[int, int, int, int]]:
        """Remove whole connected components (see erase_text); whole_letters=False = cut(box).
        Returns the bboxes of the removed components, [] for a cut."""
        _check_box(box, "erase")
        if not whole_letters:
            self.cut(box)
            return []
        return self.erase_text(box, min_inside, partial_ok)

    def erase_text(self, box, min_inside: float = 0.5, partial_ok: bool = False) -> list[tuple[int, int, int, int]]:
        """Zero each 8-connected coverage component (c > 0) with at least min_inside of its
        coverage mass inside the box, including its pixels outside the box. A component is a
        whole word part, often 2-4 joined letters, not a letter: box whole words or lines. If
        the box splits a component (one left in place has ink, coverage >= 128, inside the box,
        or one taken has ink outside it) nothing is changed and ValueError is raised, unless
        partial_ok=True. For single letters use erase_letters(). Returns the removed
        components' bboxes. Use it where text of a kept line may reach near the box."""
        box = _check_box(box, "erase_text")
        tot = [a + b for a, b in zip(self.c, self.s)]
        taken, kept, inset = _split_components(tot, self.w, self.h, box, min_inside)
        if not partial_ok:
            _check_split("erase", box, taken, kept, inset, tot, self.w)
        for comp in taken:
            for i in comp:
                self.c[i] = 0
                self.s[i] = 0
        return [bbox_of((i % self.w, i // self.w) for i in comp) for comp in taken]

    def erase_letters(self, lang: str, image: str, line_text: str | None = None, idx=None, box=None,
                      min_inside: float = 0.5) -> Layer:
        """Letter-exact erase of shipped letters (selected as in letters(); lang 'de' = 'en'): their
        Phase A pixels are zeroed, except pixels a kept letter of the same image also owns (where
        two letters join, the kept one stays whole). Their glow goes with them and the kept
        neighbours' glow is regenerated, as with erase(). The canvas must be that image (or an
        unkeyed base); returns the letters() Layer of what was erased."""
        key = ("en" if lang == "de" else lang, image)
        if self.key is not None and self.key != key:
            raise ValueError(f"erase_letters({lang}, {image}): this canvas is {self.key[0]}/{self.key[1]}")
        lay = letters(lang, image, line_text, idx, box, min_inside)
        chosen = {g["source"] for g in lay.glyphs}
        keep_px = set()
        for o in _line_letters(lang, image, None):
            if o.id not in chosen:
                keep_px.update((o.x0 + i, o.y0 + j) for j in range(o.h) for i in range(o.w) if o.data[j * o.w + i])
        for x, y, _ in lay.pixels():
            if (x, y) not in keep_px and 0 <= x < self.w and 0 <= y < self.h:
                i = y * self.w + x
                self.c[i] = 0
                self.s[i] = 0
        return lay

    def erase_layer(self, lay: Layer) -> None:
        """Zero the coverage at every pixel the layer covers (e.g. a block() of the old text)."""
        for x, y, _ in lay.pixels():
            if 0 <= x < self.w and 0 <= y < self.h:
                i = y * self.w + x
                self.c[i] = 0
                self.s[i] = 0

    def draw(self, lay: Layer, glow: bool = True, clip_ok: bool = False) -> None:
        """Add a layer's Fraktur coverage (sum, clamped); the glow is regenerated from it.
        Script ink (no glow) goes through draw_script() (= draw(lay, glow=False)).
        If any coverage pixel (> 0) of the layer falls outside the canvas, ValueError naming the
        layer's bbox is raised and nothing is drawn (a line running off the right edge, a
        negative x), unless clip_ok=True, which drops those pixels."""
        if not clip_ok:
            off = [(x, y) for x, y, _ in lay.pixels() if not (0 <= x < self.w and 0 <= y < self.h)]
            if off:
                raise ValueError(
                    f"draw(): {len(off)} coverage px of the layer {lay.text!r} fall off the "
                    f"{self.w}x{self.h} canvas (layer bbox {lay.bbox()}, ink bbox {lay.ink_bbox()}, "
                    f"first off-canvas px {off[0]}): move or shorten it, or pass clip_ok=True to cut it")
        tgt = self.c if glow else self.s
        for x, y, v in lay.pixels():
            if 0 <= x < self.w and 0 <= y < self.h:
                i = y * self.w + x
                s = tgt[i] + v
                tgt[i] = 255 if s > 255 else s

    def draw_script(self, lay: Layer, clip_ok: bool = False) -> None:
        """Add script ink (the conjunctions' font, cream without glow): its coverage neither
        gets a glow nor adds to the glow of the Fraktur around it. clip_ok as for draw()."""
        self.draw(lay, glow=False, clip_ok=clip_ok)

    def coverage_layer(self, box=None, script: bool = False) -> Layer:
        """The current (glowing or script) coverage inside box (default: whole image), the box
        clamped to the image as in cut(); an empty Layer if it lies outside the image (an
        inverted box raises ValueError)."""
        x0, y0, x1, y1 = (0, 0, self.w - 1, self.h - 1) if box is None else _check_box(box, "coverage_layer")
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(self.w - 1, x1), min(self.h - 1, y1)
        if x1 < x0 or y1 < y0:
            return Layer.empty()
        src = self.s if script else self.c
        w, h = x1 - x0 + 1, y1 - y0 + 1
        return Layer(x0, y0, w, h, [src[(y0 + j) * self.w + x0 + i] for j in range(h) for i in range(w)])

    # -- output
    def render(self) -> Image.Image:
        w, h = self.w, self.h
        n = w * h
        ch = [i for i in range(n) if self.c[i] != self.c0[i] or self.s[i] != self.s0[i]]
        out = list(self.base)
        self._changed = set()
        if ch:
            # influence region: changed coverage dilated by the glow support (Chebyshev 6)
            region = set()
            for i in ch:
                x, y = i % w, i // w
                for yy in range(max(0, y - GLOW_R), min(h - 1, y + GLOW_R) + 1):
                    row = yy * w
                    for xx in range(max(0, x - GLOW_R), min(w - 1, x + GLOW_R) + 1):
                        region.add(row + xx)
            t0 = tent_sums(self.c0, w, h)
            t1 = tent_sums(self.c, w, h)
            for i in sorted(region):
                c_old = self.c0[i] + self.s0[i]
                c_new = self.c[i] + self.s[i]
                c_old = 255 if c_old > 255 else c_old
                c_new = 255 if c_new > 255 else c_new
                gm0, gm1 = glow_of_sum(t0[i]), glow_of_sum(t1[i])
                if c_new == c_old and self.c[i] == self.c0[i]:
                    if gm1 == gm0:
                        continue                      # nothing changed here: keep base bytes
                    gl = self.g0[i] + (gm1 - gm0)     # base glow plus the model's delta
                    gl = 0.0 if gl < 0.0 else 1.0 if gl > 1.0 else gl
                else:
                    gl = gm1
                px = compose_px(c_new, gl)
                if px is None:
                    px = self.base[i] if self.base[i][3] == 0 else (G[0], G[1], G[2], 0)
                if px != out[i]:
                    out[i] = px
                    self._changed.add(i)
        img = Image.new("RGBA", (w, h))
        img.putdata(out)
        return img

    def changed_box(self):
        return bbox_of((i % self.w, i // self.w) for i in self._changed)

    def model_render(self) -> Image.Image:
        """Every pixel re-rendered from the decomposed coverage (a check of the colour model)."""
        t = tent_sums(self.c, self.w, self.h)
        out = []
        for i in range(self.w * self.h):
            cc = min(255, self.c[i] + self.s[i])
            px = compose_px(cc, glow_of_sum(t[i]))
            out.append(px if px is not None else (0, 0, 0, 0))
        img = Image.new("RGBA", (self.w, self.h))
        img.putdata(out)
        return img


def _boxes(boxes) -> list:
    if not boxes:
        return []
    return [tuple(boxes)] if isinstance(boxes[0], int) else [tuple(b) for b in boxes]


def composite(base, lay: Layer | list[Layer] | None = None, *, erase=None, cut=None, erase_text=None,
              script_boxes=None, partial_ok: bool = False, clip_ok: bool = False) -> Image.Image:
    """One shot on an intro image: cut (every coverage pixel inside each box), then erase (the
    connected components mostly inside each box, see Canvas.erase_text; erase_text is the
    same), then draw the layer(s) with one glow regenerated from the union of all cores, and
    render. Pixels farther than 6 px from every changed coverage pixel keep the base's bytes.
    script_boxes as for Canvas (required unless base is a path to a shipped image); clip_ok as
    for Canvas.draw (a layer running off the image raises ValueError without it)."""
    cv = Canvas(base, script_boxes)
    for box in _boxes(cut):
        cv.cut(box)
    for box in _boxes(erase) + _boxes(erase_text):
        cv.erase(box, partial_ok=partial_ok)
    for l in ([] if lay is None else lay if isinstance(lay, list) else [lay]):
        cv.draw(l, clip_ok=clip_ok)
    return cv.render()


def erase(base, boxes, *, whole_letters: bool = True, script_boxes=None, partial_ok: bool = False) -> Image.Image:
    """Remove old text with its glow: the connected components mostly inside each box (the
    default, see Canvas.erase_text: box whole words; it also takes their faint anti-aliased
    fringes just outside the box), or with whole_letters=False a cut of every coverage pixel
    inside each box. The glow of kept text nearby is regenerated, not eaten."""
    return composite(base, None, erase=boxes if whole_letters else None,
                     cut=None if whole_letters else boxes, script_boxes=script_boxes,
                     partial_ok=partial_ok)


# ----------------------------------------------------------------------------- the font

_DECOMP_CACHE: dict[str, tuple[int, int, list[int]]] = {}


def source_coverage(src_rel: str) -> tuple[int, int, list[int]]:
    """Glowing coverage of a shipped image (script boxes removed), cached. src_rel like
    'res/es/intro/novela.png'."""
    if src_rel not in _DECOMP_CACHE:
        parts = src_rel.split("/")
        lang, image = parts[1], parts[3][:-4]
        cv = Canvas(ROOT / "work" / "jar" / src_rel, SCRIPT_BOXES.get((lang, image), []))
        _DECOMP_CACHE[src_rel] = (cv.w, cv.h, cv.c0)
    return _DECOMP_CACHE[src_rel]


@dataclass
class Occurrence:
    id: str              # Phase A file stem, e.g. 'a__es_novela_133_98'
    char: str
    lang: str
    image: str
    src: str
    line: str            # line key 'lang:image:line_text'
    word_i: int
    char_i: int          # index in the line (non-space glyphs)
    word: str            # the word it belongs to
    word_ci: int         # index in that word
    cx: float            # coverage centroid x (image coordinates)
    x0: int              # patch origin (image coordinates)
    y0: int
    w: int
    h: int
    data: list[int]
    baseline: int
    p: int = 0           # pen position in half pixels (centroid based, see Font)
    copy_of: str = ""    # id of an earlier occurrence with the same pixels (another language)

    def __post_init__(self):
        self.data = tuple(self.data)     # shared by every Font and by occurrences(): read-only

    @property
    def phase(self) -> int:
        return self.p & 1

    @property
    def canon(self) -> str:
        return self.copy_of or self.id

    @property
    def xint(self) -> int:
        return self.p >> 1


@dataclass(frozen=True)
class Glyph:
    """A typesettable glyph. Immutable (data and members are tuples): the font hands out the
    same cached object to every line(), so a builder cannot change later lines by editing one."""
    char: str
    phase: int
    ox: int              # patch left relative to the integer pen x
    oy: int              # patch top relative to the baseline
    w: int
    h: int
    data: tuple[int, ...]
    members: tuple[str, ...]   # occurrence ids used
    spread: float        # mean L1 (coverage units 0..1) of the members vs the median
    source: str          # 'median of N' / an occurrence id / 'composed ...'

    def __post_init__(self):
        object.__setattr__(self, "data", tuple(self.data))
        object.__setattr__(self, "members", tuple(self.members))

    def ink_left(self) -> int:
        """Leftmost column (relative to the integer pen x) holding coverage >= 128."""
        cols = [i for i in range(self.w) if any(self.data[j * self.w + i] >= 128 for j in range(self.h))]
        return self.ox + (cols[0] if cols else 0)

    def ink_right(self) -> int:
        cols = [i for i in range(self.w) if any(self.data[j * self.w + i] >= 128 for j in range(self.h))]
        return self.ox + (cols[-1] if cols else self.w - 1)

    def layer(self, xint: int, baseline: int) -> Layer:
        return Layer(xint + self.ox, baseline + self.oy, self.w, self.h, list(self.data))


def _line_tokens(text: str) -> list[list[str]]:
    """Phase A line_text -> words of chars ('[oe]' = œ, '_' = a narrow word gap)."""
    t = text.replace("[oe]", "œ").replace("_", " ")
    return [list(w) for w in t.split(" ") if w]


def _median_low(vals: list[int]) -> int:
    s = sorted(vals)
    return s[(len(s) - 1) // 2]


class Font:
    """The credit-screen Fraktur, built from the Phase A glyph inventory.

    exclude: optional predicate(Occurrence) -> bool; excluded occurrences are used neither for
    glyph variants nor for the spacing fit (the selftest re-typesets a line without its own
    pixels or spacing)."""

    def __init__(self, exclude=None):
        self.exclude = exclude
        self.occ: list[Occurrence] = [o for o in _all_occurrences() if not (exclude and exclude(o))]
        self.by_id = {o.id: o for o in self.occ}
        self._pen_off: dict[str, float] = {}
        self._variants: dict[tuple[str, int], Glyph] = {}
        groups: dict[tuple[str, int], list[Occurrence]] = {}
        canon_seen = set()
        for o in self.occ:
            if o.canon in ALTERNATES or o.canon in canon_seen:
                continue          # a special shape, or the same pixels as one already counted
            canon_seen.add(o.canon)
            groups.setdefault((o.char, o.phase), []).append(o)
        self.groups = groups
        # pass 1: medians over the members that own each pixel alone; pass 2: the pixels every
        # member shares with a neighbour, with that neighbour's own (pass-1) shape subtracted
        p1 = {key: self._variant_pass1(key, groups[key]) for key in sorted(groups)}
        self._pass1 = p1
        self.fragment_info: dict[tuple[str, int], dict] = {}
        for key in sorted(groups):
            self._variants[key] = self._variant_pass2(key, p1)
        self._fit_spacing()

    # -- variants
    @staticmethod
    def _variant_pass1(key: tuple[str, int], members: list[Occurrence]) -> dict:
        """Members on a common (pen x, baseline) frame. A member's pixel is CONTESTED where the
        Phase A ownership gives that image pixel to another letter too (a join or an overlap with
        an old neighbour: the shipped value there is the two letters' union, and a fragment only
        ever adds coverage). Each pixel = the lower median over the members that own it alone;
        members whose uncontested pixels differ from that by more than 3 levels anywhere are
        dropped and the median retaken. Pixels contested in every member keep the lower median of
        all of them for now (resolved in pass 2)."""
        owners = _pixel_owners()
        ox0 = min(o.x0 - o.xint for o in members)
        oy0 = min(o.y0 - o.baseline for o in members)
        ox1 = max(o.x0 - o.xint + o.w for o in members)
        oy1 = max(o.y0 - o.baseline + o.h for o in members)
        w, h = ox1 - ox0, oy1 - oy0
        stacks, contested = [], []
        for o in members:
            arr = [0] * (w * h)
            dx, dy = o.x0 - o.xint - ox0, o.y0 - o.baseline - oy0
            for j in range(o.h):
                for i in range(o.w):
                    arr[(dy + j) * w + dx + i] = o.data[j * o.w + i]
            stacks.append(arr)
            con = [False] * (w * h)
            for j in range(h):
                for i in range(w):
                    own = owners.get((o.src, o.xint + ox0 + i, o.baseline + oy0 + j), ())
                    con[j * w + i] = any(q != o.id for q in own)
            contested.append(con)

        def median(use: list[int]) -> tuple[list[int], list[bool]]:
            data, cert = [0] * (w * h), [False] * (w * h)
            for k in range(w * h):
                clean = [stacks[m][k] for m in use if not contested[m][k]]
                cert[k] = bool(clean)
                data[k] = _median_low(clean if clean else [stacks[m][k] for m in use])
            return data, cert

        use = list(range(len(members)))
        data, cert = median(use)
        agree = [m for m in use if all(abs(stacks[m][k] - data[k]) <= 3
                                       for k in range(w * h) if not contested[m][k])]
        if agree and len(agree) < len(use):
            use = agree
            data, cert = median(use)
        return {"members": members, "use": use, "frame": (ox0, oy0, w, h), "stacks": stacks,
                "contested": contested, "data": data, "cert": cert}

    def _variant_pass2(self, key: tuple[str, int], p1: dict) -> Glyph:
        """Pass 2: a pixel contested in every member used (P of 'Pazos' and 'a', U of 'd’Umberto'
        and ’, the round s before e in 'based' / 'Rosa' / 'basato'): per member, the image
        coverage minus the pass-1 shape of each other owner there (its char at its phase, placed
        at its pen), where that shape is known from members owning the pixel alone; the lower
        median of those. Where an owner's own shape is not known there (two letters that are
        joined in every occurrence), the member's value stays (the join is kept in both)."""
        r = p1[key]
        ox0, oy0, w, h = r["frame"]
        members, use, stacks, contested = r["members"], r["use"], r["stacks"], r["contested"]
        data = list(r["data"])
        owners = _pixel_owners()
        ix = _occurrence_index()
        resolved = kept = 0
        for k in range(w * h):
            if r["cert"][k]:
                continue
            i, j = k % w, k // w
            ests = []
            any_kept = False
            for m in use:
                o = members[m]
                x, y = o.xint + ox0 + i, o.baseline + oy0 + j
                others = [q for q in owners.get((o.src, x, y), ()) if q != o.id]
                sub, known = 0, True
                for q in others:
                    qo = ix[q]
                    v = None
                    if qo.canon not in ALTERNATES and (qo.char, qo.phase) in p1:
                        rq = p1[(qo.char, qo.phase)]
                        qx0, qy0, qw, qh = rq["frame"]
                        ii, jj = x - qo.xint - qx0, y - qo.baseline - qy0
                        if 0 <= ii < qw and 0 <= jj < qh:
                            kq = jj * qw + ii
                            v = rq["data"][kq] if rq["cert"][kq] else None
                        else:
                            v = 0            # outside every member of that letter: none of its ink
                    if v is None:
                        known = False
                        break
                    sub += v
                if known:
                    cw, _, cov = source_coverage(o.src)
                    est = cov[y * cw + x] - sub
                    ests.append(est if est > SUBTRACT_NOISE else 0)
                else:
                    ests.append(stacks[m][k])
                    any_kept = True
            new = _median_low(ests)
            if any_kept:
                kept += 1 if new else 0
            elif new != data[k]:
                resolved += 1
            data[k] = new
        used = [members[m] for m in use]
        spread = sum(sum(abs(stacks[m][k] - data[k]) for k in range(w * h) if not contested[m][k])
                     for m in range(len(members))) / (255.0 * len(members))
        self.fragment_info[key] = {"resolved_px": resolved, "joined_px_kept": kept}
        n_all = len(members)
        g = Glyph(key[0], key[1], ox0, oy0, w, h, data, [o.id for o in used], spread,
                  f"median of {len(used)}" + (f" (of {n_all})" if len(used) < n_all else ""))
        return _trim(g)

    def _occurrence_glyph(self, o: Occurrence) -> Glyph:
        return _occurrence_glyph(o)

    def pen_offset(self, g: Glyph) -> float:
        """px to add to the pen of glyph g to get the pen a plain glyph of the same char would
        have in its place. 0 for plain variants and ordinary occurrences (their pens are on the
        same frame). For an ALTERNATES shape (the swash y of 'by', whose tail pulls its centroid
        pen 2 px left) the plain variants are slid over it and the best L1 match is taken."""
        if g.source not in ALTERNATES:
            return 0.0
        if g.source in self._pen_off:
            return self._pen_off[g.source]
        best = None
        ga = {(g.ox + i, g.oy + j): g.data[j * g.w + i] for j in range(g.h) for i in range(g.w)
              if g.data[j * g.w + i]}
        for ph in (0, 1):
            if (g.char, ph) not in self._variants:
                continue
            gn = self._variants[(g.char, ph)]
            for s in range(-8, 9):           # plain glyph at integer pen s (relative to g's)
                gb = {(gn.ox + s + i, gn.oy + j): gn.data[j * gn.w + i] for j in range(gn.h)
                      for i in range(gn.w) if gn.data[j * gn.w + i]}
                cost = sum(abs(ga.get(k, 0) - gb.get(k, 0)) for k in set(ga) | set(gb))
                off = s + (ph - g.phase) / 2.0
                if best is None or (cost, abs(off)) < (best[0], abs(best[1])):
                    best = (cost, off)
        self._pen_off[g.source] = best[1] if best else 0.0
        return self._pen_off[g.source]

    def phases(self, ch: str) -> list[int]:
        if ch in COMPOSED:
            return self.phases(COMPOSED[ch][0])
        return [p for p in (0, 1) if (ch, p) in self._variants]

    def chars(self) -> str:
        cs = sorted({k[0] for k in self._variants} | set(COMPOSED))
        return "".join(cs)

    def image_candidates(self, ch: str, lang: str, image: str, phase: int | None = None) -> list[Occurrence]:
        """The plain occurrences of ch in lang/image (de = en) a 'lang:image' source can pick,
        at phase (None = any): never an ALTERNATES shape and never an excluded one; the members
        of the median variant first (in inventory order), then the occurrences the median
        rejected (fragments of an old neighbour)."""
        lang = "en" if lang == "de" else lang       # de == en byte for byte
        cand = [o for o in self.occ if o.char == ch and o.lang == lang and o.image == image
                and o.canon not in ALTERNATES and (phase is None or o.phase == phase)]

        def rank(o: Occurrence) -> int:
            v = self._variants.get((ch, o.phase))
            return 0 if v is not None and (o.canon in v.members or o.id in v.members) else 1
        return sorted(cand, key=rank)                # stable: inventory order within a rank

    def glyph(self, ch: str, phase: int = 0, source: str | None = None) -> Glyph:
        """Variant of ch at phase (0/1). source: None = median of the occurrences; an
        occurrence id ('a__es_novela_133_98', any occurrence, also an excluded or ALTERNATES
        one, at its own phase); or 'lang:image' (de = en) = the first plain occurrence of ch at
        that phase in that image, see image_candidates() (KeyError if it has none at that
        phase; line() only asks for the phases the image has)."""
        if ch in COMPOSED:
            return self._composed(ch, phase, source)
        if source:
            occ = _occurrence_index()
            if source in occ:
                o = occ[source]
                if o.char != ch:
                    raise ValueError(f"source {source} is a {o.char!r}, not {ch!r}")
                return self._occurrence_glyph(o)
            lang, sep, image = source.partition(":")
            if not sep:
                raise KeyError(f"source {source!r}: neither an occurrence id nor 'lang:image'")
            cand = self.image_candidates(ch, lang, image, phase)
            if cand:
                return self._occurrence_glyph(cand[0])
            raise KeyError(f"no plain occurrence {source!r} of {ch!r} at phase {phase} "
                           f"(ALTERNATES and excluded occurrences are only reachable by id)")
        key = (ch, phase)
        if key not in self._variants:
            raise KeyError(f"no {ch!r} at phase {phase} (phases available: {self.phases(ch)})")
        return self._variants[key]

    # -- composed Swedish letters (optional, the GLOSSARY §8 wordings need none)
    def _tick(self, phase: int) -> Glyph:
        """The i-dot tick (rows at or above baseline - 17) of the i variant, on the i's pen frame."""
        i = self.glyph("i", phase)
        rows = [j for j in range(i.h) if i.oy + j <= TICK_ROWS_TOP]
        data = [i.data[j * i.w + k] if j in rows else 0 for j in range(i.h) for k in range(i.w)]
        return _trim(Glyph("˙", phase, i.ox, i.oy, i.w, i.h, data, i.members, 0.0, "tick of i"))

    def dot_offsets(self, base_ch: str) -> tuple[int, int]:
        """(left, right) pen offsets in HALF px of the two i-dot ticks of base_ch + umlaut,
        relative to the base glyph's pen. Each tick goes over a stem of the letter as the i's tick
        sits over the i's stem: (tick centroid - stem centroid) of the i, both phases averaged
        (0.9 px), added to the coverage centroid of the letter's left / right stem (STEM_ROWS,
        both phases averaged), minus the tick's own centroid, rounded to the half pixel, plus
        DOT_SHIFT[base_ch] half px (o: -1, see there). The same offsets serve both phases of the
        letter (the ticks move with its half pixel)."""
        key = ("dots", base_ch)
        if key in self._pen_off:
            return self._pen_off[key]

        def centroid(g: Glyph, rows, cols=None) -> float:
            sm = sx = 0
            for j in range(g.h):
                if g.oy + j not in rows:
                    continue
                for i in range(g.w):
                    x = g.ox + i
                    if cols is None or cols[0] <= x <= cols[1]:
                        v = g.data[j * g.w + i]
                        sm += v
                        sx += v * (2 * x + 1)
            return sx / (2.0 * sm) - g.phase / 2.0          # continuous x, relative to the pen

        def stems(g: Glyph) -> tuple[float, float]:
            runs_l, runs_r = [], []
            for j in range(g.h):
                if g.oy + j not in STEM_ROWS:
                    continue
                runs = []
                for i in range(g.w):
                    if g.data[j * g.w + i] >= 128:
                        x = g.ox + i
                        if runs and runs[-1][1] == x - 1:
                            runs[-1][1] = x
                        else:
                            runs.append([x, x])
                runs_l.append(runs[0])
                runs_r.append(runs[-1])
            span_l = (min(r[0] for r in runs_l) - 1, max(r[1] for r in runs_l) + 1)
            span_r = (min(r[0] for r in runs_r) - 1, max(r[1] for r in runs_r) + 1)
            return centroid(g, STEM_ROWS, span_l), centroid(g, STEM_ROWS, span_r)

        ph_i = self.phases("i")
        tick_rows = range(-CAP_TOP - 4, TICK_ROWS_TOP + 1)
        i_off = sum(centroid(self.glyph("i", p), tick_rows) - stems(self.glyph("i", p))[0] for p in ph_i) / len(ph_i)
        t_c = sum(centroid(self._tick(p), tick_rows) for p in ph_i) / len(ph_i)
        ph_b = self.phases(base_ch)
        sl = sum(stems(self.glyph(base_ch, p))[0] for p in ph_b) / len(ph_b)
        sr = sum(stems(self.glyph(base_ch, p))[1] for p in ph_b) / len(ph_b)
        sh = DOT_SHIFT.get(base_ch, 0)
        off = (int(math.floor(2 * (sl + i_off - t_c) + 0.5)) + sh, int(math.floor(2 * (sr + i_off - t_c) + 0.5)) + sh)
        self._pen_off[key] = off
        self._pen_off[("tick_c",)] = t_c
        return off

    def _composed(self, ch: str, phase: int, source: str | None) -> Glyph:
        base_ch, mark = COMPOSED[ch]
        base = self.glyph(base_ch, phase, source)
        parts = [base.layer(0, 0)]
        dl, dr = self.dot_offsets(base_ch)
        if mark == "dots":
            for d in (dl, dr):
                q = phase + d                   # the tick's pen in half px from the base's xint
                parts.append(self._tick(q & 1).layer(q >> 1, 0))
        elif mark == "ring":
            mid = (dl + dr) / 4.0 + self._pen_off[("tick_c",)]
            parts.append(_ring_layer(phase / 2.0 + mid + RING_DX, RING_CY))
        u = Layer.union(parts)
        return _trim(Glyph(ch, phase, u.x0, u.y0, u.w, u.h, u.data, base.members, base.spread,
                           f"composed {base_ch}+{mark}"))

    # -- spacing model
    def _fit_spacing(self) -> None:
        """Fit pen advances: pos(next) - pos(cur) = R[cur] + L[next] (+ S between words), pos in
        px, observed as p/2 (half-px pen positions). Least squares with a weak L = R prior (gauge),
        then per-pair mean residuals = the font's own kerning."""
        lines: dict[str, list[Occurrence]] = {}
        for o in self.occ:
            lines.setdefault(o.line, []).append(o)
        seen_seq = set()
        seen_pair = set()
        obs = []                         # (a, b, nspace, d)
        for key in sorted(lines):
            occ = sorted(lines[key], key=lambda o: o.char_i)
            img = key.split(":")[1]
            sig = (img, tuple((o.char, o.p - occ[0].p) for o in occ))
            if sig in seen_seq:
                continue                 # a copy of a line from another language
            seen_seq.add(sig)
            narrow = "_" in key
            for a, b in zip(occ, occ[1:]):
                if b.char_i != a.char_i + 1:
                    continue             # an excluded glyph sits between them
                if a.canon in ALTERNATES or b.canon in ALTERNATES:
                    continue             # special shapes: their centroids are not letter centroids
                sp = b.word_i - a.word_i
                if narrow and sp:
                    continue             # the it 'lavoro_di' 3-px gap
                if (a.canon, b.canon) in seen_pair:
                    continue             # both letters copied from a pair already counted
                seen_pair.add((a.canon, b.canon))
                obs.append((a.char, b.char, sp, (b.p - a.p) / 2.0))
        chars = sorted({a for a, _, _, _ in obs} | {b for _, b, _, _ in obs})
        idx = {}
        for c in chars:
            idx[("R", c)] = len(idx)
            idx[("L", c)] = len(idx)
        idx[("S",)] = len(idx)
        n = len(idx)
        ata = [[0.0] * n for _ in range(n)]
        atb = [0.0] * n

        def add(row: dict, val: float, wgt: float = 1.0):
            items = sorted(row.items())
            for i, vi in items:
                atb[i] += wgt * vi * val
                for j, vj in items:
                    ata[i][j] += wgt * vi * vj

        for a, b, sp, d in obs:
            row = {idx[("R", a)]: 1.0}
            row[idx[("L", b)]] = row.get(idx[("L", b)], 0.0) + 1.0
            if sp:
                row[idx[("S",)]] = float(sp)
            add(row, d)
        for c in chars:                  # gauge + chars seen on one side only
            add({idx[("R", c)]: 1.0, idx[("L", c)]: -1.0}, 0.0, 1e-3)
        sol = _solve(ata, atb)
        self.R = {c: sol[idx[("R", c)]] for c in chars}
        self.L = {c: sol[idx[("L", c)]] for c in chars}
        self.space = sol[idx[("S",)]]
        res: dict[tuple[str, str], list[float]] = {}
        self.residuals = []
        for a, b, sp, d in obs:
            pred = self.R[a] + self.L[b] + sp * self.space
            if not sp:
                res.setdefault((a, b), []).append(d - pred)
            self.residuals.append((a, b, sp, d, pred))
        # mean residual shrunk towards 0 by n/(n+1): one observation is half rounding noise.
        # Leave-line-out over the es/en/fr lines (word start at its best sub-pixel offset): 85% of
        # the in-word pen positions exact to the half pixel and none off by a whole pixel
        # (unshrunk 82%; a fit of absolute positions per line: 88% but 6 off by a whole pixel).
        self.pair_kern = {k: sum(v) / (len(v) + KERN_SHRINK) for k, v in sorted(res.items())}
        self.n_obs = len(obs)
        # sides never observed (a char seen only word-final, say): ink extent + median sidebearing
        self.n_side = {("R", c): 0 for c in chars} | {("L", c): 0 for c in chars}
        for a, b, sp, d in obs:
            self.n_side[("R", a)] += 1
            self.n_side[("L", b)] += 1
        sbl, sbr = [], []
        for c in chars:
            ext = self._extents(c)
            if ext is None:
                continue
            if self.n_side[("L", c)] >= 2:
                sbl.append(self.L[c] - ext[0])
            if self.n_side[("R", c)] >= 2:
                sbr.append(self.R[c] - ext[1])
        sbl.sort()
        sbr.sort()
        self.sidebearing = (sbl[(len(sbl) - 1) // 2], sbr[(len(sbr) - 1) // 2])
        for c in chars:
            ext = self._extents(c)
            for side_, tab, k in (("L", self.L, 0), ("R", self.R, 1)):
                if self.n_side[(side_, c)] == 0:
                    if ext is None:
                        del tab[c]           # side() estimates it from the glyph actually used
                    else:
                        tab[c] = ext[k] + self.sidebearing[k]

    def _extents(self, ch: str, g: Glyph | None = None):
        """(pen to ink left, ink right to pen) in px, averaged over the phases."""
        gs = [g] if g is not None else [self._variants[(ch, p)] for p in (0, 1) if (ch, p) in self._variants]
        if not gs:
            return None
        le = sum(x.phase / 2.0 - x.ink_left() for x in gs) / len(gs)
        re = sum(x.ink_right() + 1 - x.phase / 2.0 for x in gs) / len(gs)
        return le, re

    def side(self, ch: str, which: str, g: Glyph | None = None) -> float:
        """R or L of ch; for a char outside the fit (only an excluded/alternate occurrence) the
        estimate from the glyph actually used."""
        ch = COMPOSED[ch][0] if ch in COMPOSED else ch
        tab = self.R if which == "R" else self.L
        if ch in tab:
            return tab[ch]
        ext = self._extents(ch, g)
        if ext is None:
            raise KeyError(f"no spacing data for {ch!r}")
        return ext[0] + self.sidebearing[0] if which == "L" else ext[1] + self.sidebearing[1]

    def side_n(self, ch: str, which: str) -> int:
        """How many shipped letter pairs (word spaces included) observed side `which` ('L' or
        'R') of ch; 0 = guessed from the ink extent plus the median side bearing."""
        ch = COMPOSED[ch][0] if ch in COMPOSED else ch
        return self.n_side.get((which, ch), 0)

    def advance_guessed(self, a: str, b: str) -> list[str]:
        """The sides of the advance a -> b that were never observed, e.g. ["R of 'k'"]; [] if
        the advance rests on shipped pairs."""
        return [f"{w} of {c!r}" for c, w in ((a, "R"), (b, "L")) if self.side_n(c, w) == 0]

    def advance(self, a: str, b: str, spaces: int = 0, ga: Glyph | None = None, gb: Glyph | None = None) -> float:
        """Pen advance in px from a to b (the pair's own kerning included when observed)."""
        a0 = COMPOSED[a][0] if a in COMPOSED else a
        b0 = COMPOSED[b][0] if b in COMPOSED else b
        d = self.side(a0, "R", ga) + self.side(b0, "L", gb)
        if spaces:
            d += spaces * self.space
        else:
            d += self.pair_kern.get((a0, b0), 0.0)
        return d


COMPOSED = {"ä": ("a", "dots"), "ö": ("o", "dots"), "å": ("a", "ring")}

# Occurrences that are not a plain letter: kept out of the medians and the spacing fit, still
# usable through prefer={char: id}. (The second stroke of “ was cut into the following capital.)
ALTERNATES = {
    "y__en_novela_40_159": "swash y of the ligature 'by' (en novela line 3, tail under the b)",
    "b__en_novela_40_153": "b of the swash ligature 'by' (carries part of the y tail)",
    "U_E__es_novela_45_123": "E carrying the second stroke of the opening quote “",
    "U_T__en_novela_45_123": "T carrying the second stroke of the opening quote “ (the only T)",
    "U_L__fr_novela_46_131": "L carrying the second stroke of the opening quote “ (the only L)",
    "LEFT_DOUBLE_QUOTATION_MARK__en_novela_40_124": "first stroke of “ only",
    "LEFT_DOUBLE_QUOTATION_MARK__es_novela_40_124": "first stroke of “ only",
    "LEFT_DOUBLE_QUOTATION_MARK__fr_novela_41_131": "first stroke of “ only",
}


def _ring_layer(cx: float, cy: float) -> Layer:
    """The slanted å ring (RING_PATTERN, the same pixels on both phases: no half-pixel blur) with
    its centre on the whole pixel nearest the continuous point (cx, cy) (pixel x covers [x, x+1));
    an exact tie goes right, as the font's accents sit right of centre."""
    h, w = len(RING_PATTERN), len(RING_PATTERN[0])
    x0 = int(math.floor(cx - w / 2.0 + 0.5))
    y0 = int(math.floor(cy - h / 2.0 + 0.5))
    return Layer(x0, y0, w, h, [v for row in RING_PATTERN for v in row])


def _occurrence_glyph(o: Occurrence) -> Glyph:
    """A shipped occurrence as a Glyph on its own (pen x, baseline) frame."""
    return _trim(Glyph(o.char, o.phase, o.x0 - o.xint, o.y0 - o.baseline, o.w, o.h, list(o.data),
                       [o.id], 0.0, o.id))


def _trim(g: Glyph) -> Glyph:
    rows = [j for j in range(g.h) if any(g.data[j * g.w:(j + 1) * g.w])]
    cols = [i for i in range(g.w) if any(g.data[j * g.w + i] for j in range(g.h))]
    if not rows:
        return g
    j0, j1, i0, i1 = rows[0], rows[-1], cols[0], cols[-1]
    w, h = i1 - i0 + 1, j1 - j0 + 1
    data = [g.data[(j0 + j) * g.w + i0 + i] for j in range(h) for i in range(w)]
    return Glyph(g.char, g.phase, g.ox + i0, g.oy + j0, w, h, data, g.members, g.spread, g.source)


def _solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting (deterministic)."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: (abs(m[r][col]), -r))
        m[col], m[piv] = m[piv], m[col]
        p = m[col][col]
        if abs(p) < 1e-12:
            continue
        for r in range(n):
            if r != col and m[r][col]:
                f = m[r][col] / p
                mr, mc = m[r], m[col]
                for k in range(col, n + 1):
                    mr[k] -= f * mc[k]
    return [m[i][n] / m[i][i] if abs(m[i][i]) > 1e-12 else 0.0 for i in range(n)]


_OCC_CACHE: list[Occurrence] | None = None
_OCC_INDEX: dict[str, Occurrence] | None = None
_OWNERS_CACHE: dict[tuple[str, int, int], tuple[str, ...]] | None = None


def _pixel_owners() -> dict[tuple[str, int, int], tuple[str, ...]]:
    """(src, x, y) -> ids of the occurrences whose Phase A pixels include that image pixel (two
    where letters join or overlap; cached)."""
    global _OWNERS_CACHE
    if _OWNERS_CACHE is None:
        own: dict[tuple[str, int, int], list[str]] = {}
        for o in _all_occurrences():
            for j in range(o.h):
                row = j * o.w
                for i in range(o.w):
                    if o.data[row + i]:
                        own.setdefault((o.src, o.x0 + i, o.y0 + j), []).append(o.id)
        _OWNERS_CACHE = {k: tuple(v) for k, v in own.items()}
    return _OWNERS_CACHE


def _occurrence_index() -> dict[str, Occurrence]:
    global _OCC_INDEX
    if _OCC_INDEX is None:
        _OCC_INDEX = {o.id: o for o in _all_occurrences()}
    return _OCC_INDEX


def _all_occurrences() -> list[Occurrence]:
    """Every fraktur glyph of the Phase A inventory as a coverage patch (cached)."""
    global _OCC_CACHE
    if _OCC_CACHE is not None:
        return _OCC_CACHE
    index = json.loads((GLYPHS / "index.json").read_text(encoding="utf-8"))
    metrics = json.loads((GLYPHS / "font_metrics.json").read_text(encoding="utf-8"))
    baselines = {(l["image"], l["text"]): l["baseline_y(last ink row of x-letters)"]
                 for l in metrics["fraktur"]["lines"]}
    entries = [g for g in index["glyphs"] if g["font"] == "fraktur" and g["lang"] in LANGS]
    by_line: dict[tuple[str, str], list[dict]] = {}
    for g in entries:
        by_line.setdefault((g["source"], g["line_text"]), []).append(g)
    occs: list[Occurrence] = []
    for (src, text), gs in sorted(by_line.items()):
        w, h, cov = source_coverage(src)
        gs.sort(key=lambda g: (g["ink_bbox"][0], g["ink_bbox"][1]))
        words = _line_tokens(text)
        flat = [(wi, ch) for wi, word in enumerate(words) for ch in word]
        if [ch for _, ch in flat] != [g["char"] for g in gs]:
            raise RuntimeError(f"Phase A inventory: the glyphs of {src} {text!r} do not spell the line")
        # ownership: mask pixels with coverage; faint orphans within 2 px join the nearest glyph
        owner: dict[int, list[int]] = {}
        masks = []
        for k, g in enumerate(gs):
            m = Image.open(GLYPHS / g["mask_file"]).getchannel("A")
            x0, y0, x1, y1 = g["crop_bbox"]
            mp = m.load()
            pts = [(y0 + j) * w + (x0 + i) for j in range(y1 - y0 + 1) for i in range(x1 - x0 + 1)
                   if mp[i, j] > 0 and cov[(y0 + j) * w + (x0 + i)] > 0]
            masks.append(set(pts))
            for p in pts:
                owner.setdefault(p, []).append(k)
        lx0 = min(g["crop_bbox"][0] for g in gs) - 2
        lx1 = max(g["crop_bbox"][2] for g in gs) + 2
        ly0 = min(g["crop_bbox"][1] for g in gs) - 2
        ly1 = max(g["crop_bbox"][3] for g in gs) + 2
        for y in range(max(0, ly0), min(h - 1, ly1) + 1):
            for x in range(max(0, lx0), min(w - 1, lx1) + 1):
                p = y * w + x
                if not cov[p] or p in owner:
                    continue
                best = None
                for d in (1, 2):
                    for dy in range(-d, d + 1):
                        for dx in range(-d, d + 1):
                            if max(abs(dx), abs(dy)) != d:
                                continue
                            q = (y + dy) * w + (x + dx)
                            if 0 <= x + dx < w and 0 <= y + dy < h and q in owner and best is None:
                                best = owner[q][0]
                    if best is not None:
                        break
                if best is not None:
                    masks[best].add(p)
        base = baselines[(src, text)]
        lang, image = src.split("/")[1], src.split("/")[3][:-4]
        for k, (g, (wi, ch)) in enumerate(zip(gs, flat)):
            pts = masks[k]
            xs = [p % w for p in pts]
            ys = [p // w for p in pts]
            x0, y0 = min(xs), min(ys)
            pw, ph = max(xs) - x0 + 1, max(ys) - y0 + 1
            data = [0] * (pw * ph)
            sm = sx = 0
            for p in pts:
                v = cov[p]
                data[(p // w - y0) * pw + (p % w - x0)] = v
                sm += v
                sx += v * (p % w)
            wci = k - sum(len(words[j]) for j in range(wi))
            occs.append(Occurrence(Path(g["file"]).stem, ch, lang, image, src, f"{lang}:{image}:{text}",
                                   wi, k, "".join(words[wi]), wci, (sx / sm) + 0.5, x0, y0, pw, ph, data, base))
    # phase: per char, the circular mean of frac(2*cx) defines where the two half-px phases sit
    by_char: dict[str, list[Occurrence]] = {}
    for o in occs:
        by_char.setdefault(o.char, []).append(o)
    for ch, os_ in by_char.items():
        sn = sum(math.sin(2 * math.pi * (2 * o.cx)) for o in os_)
        cs = sum(math.cos(2 * math.pi * (2 * o.cx)) for o in os_)
        phi = (math.atan2(sn, cs) / (2 * math.pi)) % 1.0
        for o in os_:
            o.p = int(math.floor(2 * o.cx - phi + 0.5))
    # copies: the same word drawn at (nearly) the same place in another language's version of the
    # image (en/es/it/fr share names and 'Umberto Eco'), or the same letter with exactly the same
    # pixels there even where the word labels differ (en 'Celemin' / es 'Celemín', en 'based' /
    # it 'basato', the en/es/fr opening “, en 'inspired' / fr 'inspiré'): one occurrence, not
    # independent evidence
    for i, o in enumerate(occs):
        for q in occs[:i]:
            if (q.image == o.image and q.lang != o.lang and q.char == o.char and not q.copy_of
                    and abs(q.x0 - o.x0) <= 3 and abs(q.y0 - o.y0) <= 8
                    and ((q.word == o.word and q.word_ci == o.word_ci)
                         or ((q.w, q.h) == (o.w, o.h) and q.data == o.data))):
                o.copy_of = q.id
                break
    _OCC_CACHE = occs
    return occs


_DEFAULT_FONT: Font | None = None


def default_font() -> Font:
    global _DEFAULT_FONT
    if _DEFAULT_FONT is None:
        _DEFAULT_FONT = Font()
    return _DEFAULT_FONT


def fragment_audit(font: Font | None = None, tol: int = 2) -> dict:
    """Checks that the variants carry no fragment of an old neighbour (selftest, info):
      boundary  every word-initial or word-final occurrence a variant uses, compared with the
                variant on the pixels that occurrence owns alone (its clean side included):
                [(char, phase, id, max |difference|)] for those differing by more than tol;
                'rejected' lists the boundary occurrences the median dropped (other shapes)
      stubs     variant ink (coverage >= 128) at a pixel that every member shares with another
                letter whose own shape (from occurrences owning that pixel alone) has ink there:
                [(char, phase, (x, y) rel. pen/baseline)]; 'stubs_pass1' = the same audit of the
                pass-1 medians, i.e. without the neighbour subtraction (what it removes)."""
    font = font or default_font()
    owners = _pixel_owners()
    ix = _occurrence_index()
    p1 = font._pass1
    out = {"checked": 0, "boundary": [], "rejected": [], "stubs": [], "stubs_pass1": []}

    def at(r: dict, rx: int, ry: int, data=None) -> tuple[int, bool]:
        ox0, oy0, w, h = r["frame"]
        i, j = rx - ox0, ry - oy0
        if 0 <= i < w and 0 <= j < h:
            k = j * w + i
            return (data or r["data"])[k], r["cert"][k]
        return 0, True

    for key in sorted(font._variants):
        g = font._variants[key]
        gv = {(g.ox + i, g.oy + j): g.data[j * g.w + i] for j in range(g.h) for i in range(g.w)}
        r = p1[key]
        used = [r["members"][m] for m in r["use"]]
        for o in r["members"]:
            if o.word_ci not in (0, len(o.word) - 1):
                continue
            if o not in used:
                out["rejected"].append((key[0], key[1], o.id))
                continue
            out["checked"] += 1
            ov = {(o.x0 - o.xint + i, o.y0 - o.baseline + j): o.data[j * o.w + i]
                  for j in range(o.h) for i in range(o.w)}
            worst = max((abs(gv.get(q, 0) - ov.get(q, 0)) for q in set(gv) | set(ov)
                         if not any(p != o.id for p in owners.get((o.src, o.xint + q[0], o.baseline + q[1]), ()))),
                        default=0)
            if worst > tol:
                out["boundary"].append((key[0], key[1], o.id, worst))
        ox0, oy0, w, h = r["frame"]
        for tag, vals in (("stubs", gv), ("stubs_pass1", {(ox0 + k % w, oy0 + k // w): v
                                                          for k, v in enumerate(r["data"])})):
            for (rx, ry), v in sorted(vals.items()):
                if v < 128:
                    continue
                stub = True
                for o in used:
                    x, y = o.xint + rx, o.baseline + ry
                    others = [p for p in owners.get((o.src, x, y), ()) if p != o.id]
                    ink = False
                    for p in others:
                        q = ix[p]
                        if q.canon not in ALTERNATES and (q.char, q.phase) in p1:
                            vq, cq = at(p1[(q.char, q.phase)], x - q.xint, y - q.baseline)
                            ink |= cq and vq >= 128
                    if not ink:
                        stub = False
                        break
                if stub:
                    out[tag].append((key[0], key[1], (rx, ry)))
    return out


# ----------------------------------------------------------------------------- typesetting

def _half_px(actual: float, phases: list[int], tie: int = -1) -> int:
    """Round a pen position (px) to half pixels (returned in half px), snapped to an available
    phase if the letter exists in one phase only: towards the unrounded position, or, when that
    is exactly on the missing half pixel, in the direction of tie (+1 right, -1 left)."""
    p = int(math.floor(2 * actual + 0.5))
    if (p & 1) not in phases:
        if 2 * actual > p:
            p += 1
        elif 2 * actual < p:
            p -= 1
        else:
            p += 1 if tie > 0 else -1
    return p


def _row_ink(g: Glyph, xint: int) -> dict[int, tuple[int, int]]:
    """{row rel. baseline: (leftmost, rightmost) ink column (coverage >= 128)} of g at xint."""
    out = {}
    for j in range(g.h):
        xs = [xint + g.ox + i for i in range(g.w) if g.data[j * g.w + i] >= 128]
        if xs:
            out[g.oy + j] = (xs[0], xs[-1])
    return out


def _row_gap(ga: Glyph, xa: int, gb: Glyph, xb: int) -> int | None:
    """Smallest per-row ink gap (px) from glyph a (left) to glyph b (right); None if no shared row."""
    ra, rb = _row_ink(ga, xa), _row_ink(gb, xb)
    gaps = [rb[y][0] - ra[y][1] - 1 for y in ra if y in rb]
    return min(gaps) if gaps else None


def _word_starts(text: str, after: bool = False) -> list[int]:
    """Indices of the glyphs that start a new word after an earlier glyph (each takes one
    word_gap entry); after=True: a glyph before the text (line_after) counts as earlier."""
    out, seen = [], after
    for ci, ch in enumerate(text):
        if ch == " ":
            continue
        if seen and ci > 0 and text[ci - 1] == " ":
            out.append(ci)
        seen = True
    return out


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v) -> bool:
    return (isinstance(v, (int, float)) and not isinstance(v, bool)) and math.isfinite(v)


def _check_line_numbers(x, baseline, pen, first_phase, after: bool) -> None:
    """ValueError naming the argument for a position that would fail deep inside or be ignored."""
    if x is not None and not _is_int(x):
        raise ValueError(f"line(): x={x!r} ({type(x).__name__}): the left ink edge is a whole pixel "
                         f"column, an int (centre with // or round(); a fractional start is pen=)")
    if not _is_int(baseline):
        raise ValueError(f"line(): baseline={baseline!r} ({type(baseline).__name__}): a pixel row, an int")
    if pen is not None and not _is_num(pen):
        raise ValueError(f"line(): pen={pen!r} ({type(pen).__name__}): a finite int or float (px)")
    if pen is not None and x is not None and not after:
        raise ValueError("line(): give x (the left ink edge) or pen= (the first pen), not both")
    if first_phase is not None and (not _is_int(first_phase) or first_phase not in (0, 1)):
        raise ValueError(f"line(): first_phase={first_phase!r}: None (0 where the first letter has it), 0 or 1")
    if first_phase is not None and (pen is not None or after):
        raise ValueError("line(): first_phase goes with x; pen= (and line_after / line_before) "
                         "fix the first glyph's half pixel themselves")


def _check_line_args(text: str, kern: dict, prefer: dict, word_gap=None, after_char: str | None = None) -> None:
    """ValueError for any kern / prefer / word_gap entry that would be ignored or misread."""
    pairs = {text[i:i + 2] for i in range(len(text) - 1) if " " not in text[i:i + 2]}
    if after_char and text[:1] not in ("", " "):
        pairs.add(after_char + text[0])
    for k in kern:
        if isinstance(k, bool) or not isinstance(k, (int, str)):
            raise ValueError(f"kern key {k!r}: use a char index (int) or a 2-char pair (str)")
        if isinstance(k, int) and not (0 <= k < len(text) and text[k] != " "):
            raise ValueError(f"kern key {k}: not the index of a glyph in {text!r}")
        if isinstance(k, str) and (len(k) != 2 or " " in k):
            raise ValueError(f"kern key {k!r}: a str key is a pair of two glyphs, e.g. 'av' "
                             f"(a word gap is set with word_gap or an index kern)")
        if isinstance(k, str) and k not in pairs:
            raise ValueError(f"kern key {k!r}: {text!r} has no {k[0]!r} directly followed by {k[1]!r}")
        if not _is_num(kern[k]):
            raise ValueError(f"kern[{k!r}] = {kern[k]!r} ({type(kern[k]).__name__}): a finite int or float "
                             f"(px; 0.5 steps select the other half-pixel phase), not a bool or str")
    for k in prefer:
        if isinstance(k, bool) or not isinstance(k, (int, str)):
            raise ValueError(f"prefer key {k!r}: use a char (str) or a char index (int)")
        if isinstance(k, int) and not (0 <= k < len(text) and text[k] != " "):
            raise ValueError(f"prefer key {k}: not the index of a glyph in {text!r}")
        if isinstance(k, str) and len(k) != 1:
            raise ValueError(f"prefer key {k!r}: a str key is one char")
        if isinstance(k, str) and (k == " " or k not in text):
            raise ValueError(f"prefer key {k!r}: no such glyph in {text!r}")
    if word_gap is None:
        return
    if _is_int(word_gap):
        if word_gap < 0:
            raise ValueError(f"word_gap={word_gap}: an ink gap in px, >= 0 (a negative gap overlaps the words)")
        return
    if not isinstance(word_gap, (list, tuple)):
        raise ValueError(f"word_gap {word_gap!r}: None, an int, or a list of ints / (gap, phase) tuples")
    n = len(_word_starts(text, bool(after_char)))
    if len(word_gap) != n:
        raise ValueError(f"word_gap has {len(word_gap)} entries, {text!r} has {n} word gap(s): give "
                         f"one per gap (a single (gap, phase) goes in a list: [(11, 1)]) or one int for all")
    for e in word_gap:
        ok = _is_int(e) and e >= 0
        if isinstance(e, (tuple, list)) and len(e) == 2:
            ok = _is_int(e[0]) and e[0] >= 0 and _is_int(e[1]) and e[1] in (0, 1)
        if not ok:
            raise ValueError(f"word_gap entry {e!r}: an int (ink px, >= 0) or a tuple (ink px >= 0, phase 0/1)")


def _source_phases(font: "Font", ch: str, src: str) -> list[int]:
    """Phases a preferred source can supply for ch: the occurrence's own, or every phase at which
    'lang:image' has the letter (KeyError if it has none)."""
    occ_ix = _occurrence_index()
    if src in occ_ix:
        return [occ_ix[src].phase]
    lang, sep, image = src.partition(":")
    if not sep:
        raise KeyError(f"prefer source {src!r}: neither an occurrence id nor 'lang:image'")
    base_ch = COMPOSED[ch][0] if ch in COMPOSED else ch
    phases = sorted({o.phase for o in font.image_candidates(base_ch, lang, image)})
    if not phases:
        raise KeyError(f"prefer source {src!r}: {lang}/{image} has no plain {base_ch!r} "
                       f"(ALTERNATES and excluded occurrences are only reachable by id)")
    return phases


def _ink_points(g: Glyph, x: int, mark_only: bool = False) -> list[tuple[int, int]]:
    """Ink pixels (coverage >= 128) of g drawn at xint x, (x, row rel. baseline); mark_only: only
    the rows at or above baseline - 17 (the mark of a MARKED letter)."""
    return [(x + g.ox + i, g.oy + j) for j in range(g.h) for i in range(g.w)
            if g.data[j * g.w + i] >= 128 and (not mark_only or g.oy + j <= TICK_ROWS_TOP)]


def _clear_px(a: list[tuple[int, int]], b: list[tuple[int, int]]) -> int | None:
    """Clear px between two pixel sets (Chebyshev distance - 1; -1 = they overlap); None if one is empty."""
    if not a or not b:
        return None
    return min(max(abs(p[0] - q[0]), abs(p[1] - q[1])) for p in a for q in b) - 1


def _mark_gap(ca: str, ga: Glyph, xa: int, cb: str, gb: Glyph, xb: int) -> int | None:
    """Clear px between a mark and its neighbour, for glyph a (char ca, at xint xa) directly left of
    glyph b: the smaller of (a's mark -> all of b's ink) if a is MARKED and (all of a's ink -> b's
    mark) if b is MARKED. None if neither carries a mark."""
    gaps = []
    if cb in MARKED:
        gaps.append(_clear_px(_ink_points(ga, xa), _ink_points(gb, xb, True)))
    if ca in MARKED:
        gaps.append(_clear_px(_ink_points(ga, xa, True), _ink_points(gb, xb)))
    gaps = [g for g in gaps if g is not None]
    return min(gaps) if gaps else None


def _fit_mark(font: "Font", prev: dict, ch: str, src, phases: list[int], p: int) -> tuple[int, int | None]:
    """(pen in half px, clear px) for ch after the placed glyph prev when either carries a mark:
    p, or the first half-pixel step right of it (at most MARK_MAX_SHIFT half px) at which every
    mark keeps MARK_MIN_GAP clear px (the farthest step if none does)."""
    cand, cand_gap = p, None
    for step in range(MARK_MAX_SHIFT + 1):
        q = p + step
        if (q & 1) not in phases:
            continue
        gap = _mark_gap(prev["char"], prev["glyph"], prev["x"], ch, font.glyph(ch, q & 1, src), q >> 1)
        cand, cand_gap = q, gap
        if gap is None or gap >= MARK_MIN_GAP:
            break
    return cand, cand_gap


def line(text: str, x: int | None, baseline: int, kern: dict | None = None, prefer: dict | None = None,
         word_gap=None, first_phase: int | None = None, font: Font | None = None, pen: float | None = None,
         allow_ring: bool = False, _after=None) -> Layer:
    """Typeset one line of Fraktur.

    x           left ink edge (column of the first coverage >= 128) of the first glyph: an int
                (ValueError for a float: centre with // or round())
    pen         instead of x (not both; and without first_phase): the first glyph's pen position
                in px, fractional (rounded to the half pixel for drawing; the remainder is kept
                for the advances)
    baseline    last ink row of the x-height letters (shipped lines: 114/144/174, pitch 30), an int
    kern        {char index in text: px} and/or {"ab": px}: extra advance before that glyph
                (or between every a and b), moving it and everything after it; 0.5-px steps
                select the other half-pixel phase, on the first glyph and after a word_gap too
                (x / word_gap then fix the unkerned place). Keys must be the index of a glyph
                (not a space) or a pair that occurs in text as two adjacent glyphs; values an int
                or float (not a bool or str); anything else raises ValueError. A kern onto a phase
                the letter lacks snaps in the kern's direction. An explicit kern on a glyph (its
                index or its pair) switches off the fits that would move it: the 1-px quote fit of
                a capital after an opening ” and the mark fit (module header, MARKS).
    prefer      {char or char index: occurrence id or "lang:image"}: use that occurrence's
                pixels instead of the median variant (e.g. a swash, or a letter cut from the
                same image as the rest of the line). With "lang:image" (de = en) the letter is
                put on a half pixel at which that image has it (the pen snaps to the nearest
                one); KeyError up front if the image has no such letter. A char key must occur
                in text (ValueError). Two neighbours given as adjacent letters of one shipped
                line keep their shipped relative position (a kern moves the second from there).
    word_gap    None (default): the font's own word space, as in the shipped lines; an int >= 0:
                every word gap is that many px of ink gap; a list: exactly one entry per word
                gap, in order, each an int >= 0 or a tuple (gap, phase) that also fixes the
                half-pixel phase of the word's first glyph (ValueError if the letter lacks that
                phase, or if a half-pixel kern on that glyph contradicts it).
    first_phase half-pixel phase of the first glyph with x: None (default) = 0 where the first
                letter (from its prefer source, if any) has it, else its only phase; 0 or 1 =
                that phase, ValueError if the letter lacks it or a half-pixel kern on the first
                glyph contradicts it (as for a word_gap phase). Any other value: ValueError.
    allow_ring  False (default): text containing the composed å (UNREVIEWED: its ring has no model
                in the font, see THE COMPOSED LETTERS) raises ValueError; True: typeset it, after
                you have looked at the result at 4x and 6x next to the shipped letters.
    Each glyph's pen position accumulates the font's fractional advances and is rounded to a
    half pixel, which selects the phase variant (snapped to the other phase if a letter exists
    in one only). Returns a Layer; .glyphs lists each placed glyph: char, index (into text,
    spaces counted: the index kern= and prefer= take), letter_index (spaces not counted), x,
    phase, pen, model_pen, baseline, ink_left, ink_right, source, glyph (immutable), mark_fit
    (half px the glyph was moved right so that its own mark or the previous glyph's keeps
    MARK_MIN_GAP clear px), mark_gap (clear px between a mark and the previous glyph of the same
    word, None if neither carries one), mark_crowded (mark_gap < MARK_MIN_GAP even after the fit,
    without an explicit kern: a FrakturSpacingWarning is issued) and spacing_guessed: True
    when the advance onto it uses a side no shipped pair shows (see Font.advance_guessed; a
    FrakturSpacingWarning is issued too) - check that pair by eye or give it an explicit kern,
    which clears both flags.
    """
    _check_line_numbers(x, baseline, pen, first_phase, _after is not None)
    if not isinstance(allow_ring, bool):
        raise ValueError(f"line(): allow_ring={allow_ring!r}: True or False")
    ring = sorted({ch for ch in text if ch in UNREVIEWED})
    if ring and not allow_ring:
        raise ValueError(f"line({text!r}): {' '.join(ring)} is composed with a ring the font has no model "
                         f"for and is NOT REVIEWED (module header, THE COMPOSED LETTERS); no GLOSSARY §8 "
                         f"wording needs it. Pass allow_ring=True to typeset it anyway, and look at the "
                         f"result at 4x and 6x before shipping it")
    if x is None and pen is None and _after is None:
        raise ValueError("line(): give x (the left ink edge of the first glyph) or pen=")
    font = font or default_font()
    kern = kern or {}
    prefer = prefer or {}
    _check_line_args(text, kern, prefer, word_gap, _after[0].char if _after is not None else None)
    gap_all = word_gap is not None and not isinstance(word_gap, (list, tuple))
    gap_i = 0
    parts: list[Layer] = []
    placed: list[dict] = []
    # pos = pen of the previous glyph in px (fractional, unrounded) on the PLAIN-glyph frame: for
    # an ALTERNATES shape it is its actual pen + font.pen_offset() (see Font.pen_offset)
    pos = None
    prev = prev_g = prev_src = None
    spaces = 0
    placed_prev = None
    letter_i = 0
    occ_ix = _occurrence_index()
    if _after is not None:  # continue after a shipped occurrence: (Occurrence, dx, dy)
        o_prev, adx, ady = _after
        prev, prev_g = o_prev.char, font._occurrence_glyph(o_prev)
        pos = o_prev.p / 2.0 + adx + font.pen_offset(prev_g)
        baseline = o_prev.baseline + ady
        placed_prev = {"char": o_prev.char, "glyph": prev_g, "x": o_prev.xint + adx,
                       "ink_right": o_prev.xint + adx + prev_g.ink_right(), "pen": o_prev.p / 2.0 + adx}
    for ci, ch in enumerate(text):
        if ch == " ":
            spaces += 1
            continue
        src = prefer.get(ci, prefer.get(ch))
        phases = _source_phases(font, ch, src) if src else font.phases(ch)
        if not phases:
            raise KeyError(f"the Fraktur font has no {ch!r} (available: {font.chars()}); "
                           f"broken or special shapes: {sorted(ALTERNATES)}")
        explicit = ci in kern or (prev is not None and spaces == 0 and prev + ch in kern)
        extra = float(kern.get(ci, 0.0))
        if prev is not None and spaces == 0:
            extra += float(kern.get(prev + ch, 0.0))
        tie = 1 if extra > 0 else -1             # a kern onto a missing half pixel goes its way
        guessed: list[str] = []
        mark_fit = 0
        last = placed[-1] if placed else placed_prev    # the glyph before this one, if any
        if pos is None and pen is not None:
            g_probe = font.glyph(ch, phases[0], src)
            pos = pen + extra
            p = _half_px(pos - font.pen_offset(g_probe), phases, tie)
            ph = p & 1
            gl = font.glyph(ch, ph, src)
            xint = p >> 1
        elif pos is None:
            # x fixes the unkerned start; a kern then moves the pen from there like any other
            # glyph's (a 0.5-px kern selects the other half-pixel phase)
            if first_phase is not None and first_phase not in phases:
                raise ValueError(f"first_phase={first_phase}: {ch!r} (index {ci}) has only phase(s) {phases}"
                                 + (f" from source {src!r}" if src else "") + "; first_phase=None takes it")
            if first_phase is not None and extra != math.floor(extra):
                raise ValueError(f"first_phase={first_phase} fixes the phase of {ch!r} (index {ci}); a "
                                 f"half-pixel kern there contradicts it: give one or the other")
            ph0 = first_phase if first_phase is not None else (0 if 0 in phases else phases[0])
            g0 = font.glyph(ch, ph0, src)
            p0 = 2 * (x - g0.ink_left()) + ph0
            p = _half_px(p0 / 2.0 + extra, phases, tie) if extra else p0
            ph = p & 1
            gl = font.glyph(ch, ph, src)
            xint = p >> 1
            pos = p0 / 2.0 + extra + font.pen_offset(gl)
        elif spaces and word_gap is not None:
            # the next word starts word_gap px of ink after the previous glyph; the phase is the
            # one given, else the one whose pen lies nearest the font's own advance; a kern then
            # moves it from there (0.5 px = the other phase)
            gap = word_gap if gap_all else word_gap[gap_i]
            gap_i += 1
            want_ph = None
            if isinstance(gap, (tuple, list)):
                gap, want_ph = gap
                if want_ph not in phases:
                    raise ValueError(f"word_gap entry {gap_i - 1} asks for phase {want_ph} of {ch!r} "
                                     f"(index {ci}), which has only phase(s) {phases}")
                if extra != math.floor(extra):
                    raise ValueError(f"word_gap entry {gap_i - 1} fixes the phase of {ch!r} (index {ci}); "
                                     f"a half-pixel kern there contradicts it: give one or the other")
            last_right = placed[-1]["ink_right"] if placed else placed_prev["ink_right"]
            best = None
            for ph_c in phases:
                g_c = font.glyph(ch, ph_c, src)
                x_c = last_right + 1 + int(gap) - g_c.ink_left()
                model = pos + font.advance(prev, ch, spaces, prev_g, g_c) - font.pen_offset(g_c)
                d = abs(x_c + ph_c / 2.0 - model) if want_ph is None else abs(ph_c - want_ph)
                if best is None or d < best[0]:
                    best = (d, ph_c, g_c, x_c)
            _, ph, gl, xint = best
            if extra:
                p = _half_px(xint + ph / 2.0 + extra, phases, tie)
                ph = p & 1
                gl = font.glyph(ch, ph, src)
                xint = p >> 1
            pos = xint + ph / 2.0 + font.pen_offset(gl)
        elif (not spaces and src in occ_ix and prev_src in occ_ix
              and occ_ix[src].line == occ_ix[prev_src].line
              and occ_ix[src].char_i == occ_ix[prev_src].char_i + 1):
            # two neighbours cut from one source line keep their original relative position; a
            # kern moves the second from there, snapped to its own phase like any other source
            o_a, o_b = occ_ix[prev_src], occ_ix[src]
            p_raw = int(round(2 * placed[-1]["pen"])) + (o_b.p - o_a.p)
            p = _half_px(p_raw / 2.0 + extra, phases, tie) if extra else p_raw
            ph = p & 1
            gl = font.glyph(ch, ph, src)
            xint = p >> 1
            pos = p / 2.0 + font.pen_offset(gl)
        else:
            g_probe = font.glyph(ch, phases[0], src)
            pos += font.advance(prev, ch, spaces, prev_g, g_probe) + extra
            p = _half_px(pos - font.pen_offset(g_probe), phases, tie)   # an alternate sits off the plain pen
            ph = p & 1
            gl = font.glyph(ch, ph, src)
            xint = p >> 1
            if not explicit:
                guessed = font.advance_guessed(prev, ch)
            p_fit = p
            if prev in OPENING_QUOTES and not spaces and ch.isupper() and not explicit and placed:
                # opening quote + capital: never observed, fit to the shipped 1-px ink gap
                guessed = []
                p_fit = _fit_after_quote(font, placed[-1], ch, src, phases, p)
            elif (ch in MARKED or prev in MARKED) and not spaces and not explicit and last is not None:
                # a mark (an i-dot tick, an accent, the composed ticks or ring) must keep
                # MARK_MIN_GAP clear px from the other glyph of the pair, on either side
                p_fit = _fit_mark(font, last, ch, src, phases, p)[0]
                mark_fit = p_fit - p
            if p_fit != p:
                pos += (p_fit - p) / 2.0
                p = p_fit
                ph = p & 1
                gl = font.glyph(ch, ph, src)
                xint = p >> 1
        if gl.source in occ_ix and gl.phase != ph:
            raise AssertionError(f"line({text!r}): {ch!r} (index {ci}) recorded at phase {ph}, "
                                 f"but its source {gl.source} is drawn at phase {gl.phase}")
        if guessed:
            warnings.warn(f"line({text!r}): the advance {prev!r} -> {ch!r} (index {ci}) uses "
                          f"{' and '.join(guessed)}, which no shipped pair shows: check that pair by "
                          f"eye or give it an explicit kern", FrakturSpacingWarning, stacklevel=2)
        mark_gap = None
        if not spaces and last is not None and (ch in MARKED or prev in MARKED):
            mark_gap = _mark_gap(prev, last["glyph"], last["x"], ch, gl, xint)
        crowded = mark_gap is not None and mark_gap < MARK_MIN_GAP and not explicit
        if crowded:
            warnings.warn(f"line({text!r}): the mark of {prev + ch!r} (index {ci}) keeps only {mark_gap} "
                          f"clear px (shipped: >= {MARK_MIN_GAP}) after moving {mark_fit / 2:g} px, the most "
                          f"the mark fit moves: check it by eye or give it an explicit kern",
                          FrakturSpacingWarning, stacklevel=2)
        parts.append(gl.layer(xint, baseline))
        placed.append({"char": ch, "index": ci, "letter_index": letter_i, "x": xint, "phase": ph,
                       "pen": xint + ph / 2.0, "model_pen": pos, "baseline": baseline,
                       "ink_left": xint + gl.ink_left(), "ink_right": xint + gl.ink_right(),
                       "source": gl.source, "glyph": gl, "mark_fit": mark_fit, "mark_gap": mark_gap,
                       "mark_crowded": crowded, "spacing_guessed": bool(guessed)})
        letter_i += 1
        prev, prev_g, prev_src = ch, gl, src
        spaces = 0
    out = Layer.union(parts)
    out.glyphs = placed
    out.text = text
    return out


def _fit_after_quote(font: "Font", q: dict, ch: str, src, phases: list[int], p: int) -> int:
    """Pen (half px) for capital ch after the opening quote q (a placed-glyph dict): stepping
    left from p in half pixels (at most 4 px), the first pen whose per-row ink gap to the quote
    is QUOTE_CAP_GAP or less (never a negative gap: then the step before it); p itself if the
    model already puts it that close or the two share no ink row."""
    gq, xq = q["glyph"], q["x"]
    best = p
    for cand in range(p, p - 9, -1):
        if (cand & 1) not in phases:
            continue
        gap = _row_gap(gq, xq, font.glyph(ch, cand & 1, src), cand >> 1)
        if gap is None:
            return p
        if gap < 0:
            break
        best = cand
        if gap <= QUOTE_CAP_GAP:
            break
    return best


def line_after(occurrence_id: str, text: str, dx: int = 0, dy: int = 0, **kw) -> Layer:
    """Typeset text continuing after a shipped glyph (moved by dx, dy together with the block it
    belongs to), with the font's advance from that glyph, e.g. the 's' of 'Annauds' after the
    'd' of a reused 'Jean-Jacques Annaud' block. A leading space starts a new word. Takes line()'s
    kern / prefer / word_gap / font (not x, pen or first_phase: the shipped glyph fixes the start);
    the mark fit and its warning apply to the first glyph after the shipped one too."""
    if not (_is_int(dx) and _is_int(dy)):
        raise ValueError(f"line_after(): dx={dx!r}, dy={dy!r}: whole pixels (ints), as the block moves")
    _no_position_kw("line_after", kw)
    o = _occurrence_index()[occurrence_id]
    return line(text, None, 0, _after=(o, dx, dy), **kw)


def _no_position_kw(fn: str, kw: dict) -> None:
    bad = sorted(k for k in ("x", "pen", "first_phase", "baseline", "_after") if k in kw)
    if bad:
        raise ValueError(f"{fn}(): {', '.join(bad)} not accepted: the shipped glyph fixes the position "
                         f"(move it with dx, dy)")


LINE_BEFORE_SEARCH = 8               # line_before tries the start at +-0.25 px steps, up to 2 px away


def line_before(occurrence_id: str, text: str, dx: int = 0, dy: int = 0, **kw) -> Layer:
    """Typeset text ending just before a shipped glyph (moved by dx, dy together with its block),
    with the font's advances, e.g. 'av ' before the 'U' of a kept 'Umberto Eco'. A trailing
    space puts the font's word space between them; without one the text joins the glyph's word.
    Takes line()'s kern / prefer / word_gap / font (not x, pen or first_phase).
    GUARANTEE: the LAST glyph lands on the half pixel nearest to where the font's advance before
    the kept glyph puts it: within 0.25 px (0.5 px if that letter exists at one phase only). With
    word_gap=None and no fit the whole text is then where the font puts it. word_gap (or a mark or
    quote fit) makes the line a non-linear function of its start (words after a gap snap to whole
    ink columns), so the start is searched in quarter-pixel steps, nearest first, up to 2 px from
    the linear estimate, until the last glyph lands within that tolerance; with word_gap the last
    word's half-pixel phase is part of the search unless a (gap, phase) entry fixes it (its ink
    gap is word_gap either way). If no start lands (a mark fit can make the last glyph skip the
    target half pixel; a fixed last-word phase can make it unreachable; never seen for the Swedish
    wordings, see the selftest), the start whose last glyph comes nearest is used, the glyph dict
    says so (to_kept_off=True) and a FrakturSpacingWarning is issued: check that pair by eye, or
    nudge it with a kern. The glyph dict of the last glyph gets 'to_kept_err' (px, signed),
    'to_kept_off', 'spacing_guessed_to_kept' and, without a trailing space, 'mark_gap_to_kept' /
    'mark_crowded_to_kept' (a FrakturSpacingWarning as in line())."""
    if not (_is_int(dx) and _is_int(dy)):
        raise ValueError(f"line_before(): dx={dx!r}, dy={dy!r}: whole pixels (ints), as the block moves")
    _no_position_kw("line_before", kw)
    font = kw.get("font") or default_font()
    o = _occurrence_index()[occurrence_id]
    body = text.rstrip(" ")
    spaces = len(text) - len(body)
    if not body:
        return Layer.empty()
    g_o = font._occurrence_glyph(o)
    base_y = o.baseline + dy

    def run(pen: float) -> Layer:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FrakturSpacingWarning)   # the final line() call warns
            return line(body, None, base_y, pen=pen, **kw)

    def want_of(g: dict) -> float:
        return (o.p / 2.0 + dx + font.pen_offset(g_o)
                - font.advance(g["char"], o.char, spaces, g["glyph"], g_o))

    def err_of(lay: Layer) -> float:
        g = lay.glyphs[-1]
        return g["pen"] + font.pen_offset(g["glyph"]) - want_of(g)

    trial = run(0.0)
    pen0 = want_of(trial.glyphs[-1]) - trial.glyphs[-1]["model_pen"]
    li = len(body) - 1
    prefer = kw.get("prefer") or {}
    src = prefer.get(li, prefer.get(body[li]))
    tol = 0.25 if len(_source_phases(font, body[li], src) if src else font.phases(body[li])) == 2 else 0.5
    # With word_gap, line() picks each word start's half pixel nearest the font's advance from the
    # word BEFORE it, and the words snap to whole ink columns, so the last word may only ever land
    # on one half pixel (e.g. 'efter av ' with word_gap=12: 'av' always on .5). Here the side that
    # matters for the last word is the kept glyph after it, so, unless the caller fixed it, the
    # search may also give the last word start either phase (the ink gap stays exactly word_gap).
    variants = [kw]
    starts = _word_starts(body)
    wg = kw.get("word_gap")
    if wg is not None and starts:
        entries = [wg] * len(starts) if _is_int(wg) else list(wg)
        if _is_int(entries[-1]):
            variants += [{**kw, "word_gap": entries[:-1] + [(entries[-1], ph)]} for ph in (0, 1)]
    best = None
    for k in sorted(range(-LINE_BEFORE_SEARCH, LINE_BEFORE_SEARCH + 1), key=lambda k: (abs(k), k)):
        pen_k = pen0 + k / 4.0
        for kw_v in variants:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", FrakturSpacingWarning)
                    e = err_of(line(body, None, base_y, pen=pen_k, **kw_v))
            except ValueError:
                if kw_v is kw:
                    raise
                continue                         # that phase is not available / contradicts a kern
            if best is None or abs(e) < abs(best[1]) - 1e-9:
                best = (pen_k, e, kw_v)
            if abs(e) <= tol + 1e-9:
                break
        if abs(best[1]) <= tol + 1e-9:
            break
    off = abs(best[1]) > tol + 1e-9
    lay = line(body, None, base_y, pen=best[0], **best[2])
    last = lay.glyphs[-1]
    last["to_kept_err"] = round(err_of(lay), 4)
    last["to_kept_off"] = off
    if off:
        warnings.warn(f"line_before({occurrence_id!r}, {text!r}, {dx}, {dy}): no start within "
                      f"{LINE_BEFORE_SEARCH / 4:g} px puts the last glyph {last['char']!r} within {tol} px of the "
                      f"font's advance before the kept {o.char!r} (a mark fit, or a word_gap phase fixed for "
                      f"the last word, can cause this); using the nearest start: {last['to_kept_err']:+.3f} px "
                      f"(glyph dict to_kept_err / to_kept_off). Check that pair by eye or nudge it with a kern",
                      FrakturSpacingWarning, stacklevel=2)
    guessed = font.advance_guessed(last["char"], o.char)
    last["spacing_guessed_to_kept"] = bool(guessed)
    if guessed:
        warnings.warn(f"line_before({occurrence_id!r}, {text!r}): the advance {last['char']!r} -> "
                      f"{o.char!r} uses {' and '.join(guessed)}, which no shipped pair shows: check it "
                      f"by eye", FrakturSpacingWarning, stacklevel=2)
    mg = None if spaces else _mark_gap(last["char"], last["glyph"], last["x"], o.char, g_o, o.xint + dx)
    last["mark_gap_to_kept"] = mg
    last["mark_crowded_to_kept"] = mg is not None and mg < MARK_MIN_GAP
    if last["mark_crowded_to_kept"]:
        warnings.warn(f"line_before({occurrence_id!r}, {text!r}): the mark of {last['char'] + o.char!r} "
                      f"keeps only {mg} clear px (shipped: >= {MARK_MIN_GAP}) and the kept glyph cannot "
                      f"move: check it by eye", FrakturSpacingWarning, stacklevel=2)
    return lay


def align_before(occurrence_id: str, text: str, x: int, dy: int = 0, **kw) -> int:
    """The whole-pixel dx that puts the left ink edge of line_before(occurrence_id, text, dx, dy)
    at column x: move the kept block (block().moved(dx, dy) / letters().moved(dx, dy)) and the
    line by it, e.g. to give 'av Umberto Eco' the left edge of the line above (es novela:
    line_before(U, 'av ') starts at x 37, the lines above at 40, so dx = 3). The kept block moves
    whole pixels, so its half-pixel phases, and the font's space before it, stay exact."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FrakturSpacingWarning)
        lay = line_before(occurrence_id, text, 0, dy, **kw)
    if not lay.glyphs:
        raise ValueError(f"align_before(): {text!r} has no glyph to align")
    return x - lay.glyphs[0]["ink_left"]


def ink_left(o: Occurrence) -> int:
    """Left ink column (coverage >= 128) of a shipped occurrence."""
    return min(x for x in range(o.x0, o.x0 + o.w)
               if any(o.data[j * o.w + (x - o.x0)] >= 128 for j in range(o.h)))


def ink_right(o: Occurrence) -> int:
    return max(x for x in range(o.x0, o.x0 + o.w)
               if any(o.data[j * o.w + (x - o.x0)] >= 128 for j in range(o.h)))


def occurrences(lang: str | None = None, image: str | None = None, line_text: str | None = None,
                char: str | None = None) -> list[Occurrence]:
    """The shipped Fraktur glyphs (Phase A inventory), filtered (lang 'de' = 'en'); each has .id,
    .char, .p (pen in half px), .xint, .phase, .baseline, .word, .line, ink via ink_left(o)."""
    if lang == "de":
        lang = "en"                  # de == en byte for byte
    out = []
    for o in _all_occurrences():
        if lang and o.lang != lang or image and o.image != image or char and o.char != char:
            continue
        if line_text and o.line.split(":", 2)[2] != line_text:
            continue
        out.append(o)
    return out


def _split_components(tot: list[int], w: int, h: int, box, min_inside: float):
    """The 8-connected coverage components (tot > 0) with a pixel inside box: (taken, kept,
    inset), taken = those with at least min_inside of their coverage mass inside the box (each
    a list of pixel indices y*w+x), inset = the box's pixel indices."""
    x0, y0, x1, y1 = box
    inbox = [y * w + x for y in range(max(0, y0), min(h - 1, y1) + 1) for x in range(max(0, x0), min(w - 1, x1) + 1)]
    inset = set(inbox)
    seen = set()
    taken, kept = [], []
    for start in inbox:
        if not tot[start] or start in seen:
            continue
        comp, stack = [], [start]
        seen.add(start)
        while stack:
            i = stack.pop()
            comp.append(i)
            x, y = i % w, i // w
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < w and 0 <= yy < h:
                        j = yy * w + xx
                        if tot[j] and j not in seen:
                            seen.add(j)
                            stack.append(j)
        mass = sum(tot[i] for i in comp)
        inside = sum(tot[i] for i in comp if i in inset)
        (taken if inside >= min_inside * mass else kept).append(comp)
    return taken, kept, inset


def _check_split(what: str, box, taken, kept, inset, tot: list[int], w: int) -> None:
    """ValueError if the box splits a component: a kept one has ink (coverage >= 128) inside the
    box, or a taken one has ink outside it (anti-aliased fringe below 128 may lie outside)."""
    def bb(comp):
        return bbox_of((i % w, i // w) for i in comp)
    kept_in = [bb(c) for c in kept if any(tot[i] >= 128 and i in inset for i in c)]
    taken_out = [bb(c) for c in taken if any(tot[i] >= 128 and i not in inset for i in c)]
    if kept_in or taken_out:
        raise ValueError(
            f"{what} box {tuple(box)} splits connected coverage components (inside a word one is "
            f"often 2-4 joined letters)"
            + (f"; left in place, with ink inside the box: {kept_in}" if kept_in else "")
            + (f"; taken whole, with ink outside the box: {taken_out}" if taken_out else "")
            + ". Box whole words or lines, use letters() / Canvas.erase_letters() for single "
              "letters, or pass partial_ok=True to accept it")


def _line_letters(lang: str, image: str, line_text: str | None) -> list[Occurrence]:
    lang = "en" if lang == "de" else lang
    occ = [o for o in _all_occurrences() if o.lang == lang and o.image == image]
    if not occ:
        raise KeyError(f"no Fraktur letters in {lang}/{image}")
    if line_text is None:
        return occ
    sel = sorted((o for o in occ if o.line.split(":", 2)[2] == line_text), key=lambda o: o.char_i)
    if not sel:
        texts = sorted({o.line.split(":", 2)[2] for o in occ})
        raise KeyError(f"{lang}/{image} has no Fraktur line {line_text!r}; its lines: {texts}")
    return sel


def letters(lang: str, image: str, line_text: str | None = None, idx=None, box=None,
            min_inside: float = 0.5) -> Layer:
    """Letter-exact shipped pixels (Phase A ownership: each letter's own mask pixels with their
    anti-aliased fringe; where two joined letters share a pixel, both own it). Selects the
    letters of line_text (the Phase A line text, see occurrences(); lang 'de' = 'en') or, with
    line_text=None, of the whole image, narrowed by
      idx  None (all) / an int / a slice / a list of ints into the line's letters (spaces not
           counted, negative from the end) / a str = a substring of the line, e.g. 'Umberto Eco'
      box  only the letters with at least min_inside of their coverage mass inside the box.
    Returns a Layer (pixels as in the shipped image, glow excluded: it is regenerated) whose
    .glyphs list the letters (char, index = position in the line text with spaces counted, as in
    line(); letter_index = spaces not counted, the numbering idx= uses; x, phase, pen, baseline,
    ink_left/right, source = the occurrence id), usable as a reusable block (.moved(dx, dy)) or
    with Canvas.erase_letters()."""
    occ = _line_letters(lang, image, line_text)
    if idx is not None:
        if line_text is None:
            raise ValueError("letters(): idx needs line_text")
        n = len(occ)
        if isinstance(idx, str):
            disp = line_text.replace("[oe]", "œ").replace("_", " ")
            k = disp.find(idx)
            if k < 0 or not idx.strip():
                raise KeyError(f"letters(): {idx!r} is not part of the line {disp!r}")
            first = sum(1 for ch in disp[:k] if ch != " ")
            sel_i = list(range(first, first + sum(1 for ch in idx if ch != " ")))
        elif isinstance(idx, slice):
            sel_i = list(range(n))[idx]
        elif isinstance(idx, int) and not isinstance(idx, bool):
            if not -n <= idx < n:
                raise IndexError(f"letters(): index {idx} out of range for {n} letters")
            sel_i = [idx % n]
        else:
            sel_i = []
            for k in idx:
                if not isinstance(k, int) or isinstance(k, bool) or not -n <= k < n:
                    raise IndexError(f"letters(): index {k!r} out of range for {n} letters")
                sel_i.append(k % n)
        occ = [occ[k] for k in sorted(set(sel_i))]
    if box is not None:
        x0, y0, x1, y1 = _check_box(box, "letters()")
        sel = []
        for o in occ:
            mass = sum(o.data)
            inside = sum(o.data[j * o.w + i] for j in range(o.h) for i in range(o.w)
                         if x0 <= o.x0 + i <= x1 and y0 <= o.y0 + j <= y1)
            if mass and inside >= min_inside * mass:
                sel.append(o)
        occ = sel
    if not occ:
        return Layer.empty()
    px: dict[tuple[int, int], int] = {}
    for o in occ:
        for j in range(o.h):
            for i in range(o.w):
                v = o.data[j * o.w + i]
                if v:
                    px[(o.x0 + i, o.y0 + j)] = v      # a shared pixel has the same value in both
    bb = bbox_of(px)
    bw, bh = bb[2] - bb[0] + 1, bb[3] - bb[1] + 1
    data = [0] * (bw * bh)
    for (x, y), v in px.items():
        data[(y - bb[1]) * bw + (x - bb[0])] = v
    glyphs = []
    for o in sorted(occ, key=lambda o: (o.line, o.char_i)):
        g = _occurrence_glyph(o)
        disp = o.line.split(":", 2)[2].replace("[oe]", "œ").replace("_", " ")
        text_i = [i for i, ch in enumerate(disp) if ch != " "][o.char_i]
        glyphs.append({"char": o.char, "index": text_i, "letter_index": o.char_i, "x": o.xint,
                       "phase": o.phase, "pen": o.p / 2.0, "model_pen": o.p / 2.0, "baseline": o.baseline,
                       "ink_left": ink_left(o), "ink_right": ink_right(o), "source": o.id, "glyph": g,
                       "mark_fit": 0, "mark_gap": None, "mark_crowded": False, "spacing_guessed": False})
    return Layer(bb[0], bb[1], bw, bh, data, glyphs,
                 text=f"{'en' if lang == 'de' else lang}:{image}:" + "".join(o.char for o in occ))


def block(lang: str, image: str, box, whole_components: bool = True, min_inside: float = 0.5,
          letters: bool = False, partial_ok: bool = False) -> Layer:
    """Glowing coverage cut from a shipped image (lang 'de' = 'en') as a reusable pixel block (a
    name, a word); the glow is left out (it is regenerated wherever the block is drawn).
      default         every 8-connected coverage component with >= min_inside of its mass inside
                      the box, including its parts outside (a long descender). Inside a word a
                      component is often 2-4 joined letters, so box whole words: ValueError if
                      the box splits one (a left-out component with ink inside the box, or a
                      taken one with ink outside it) unless partial_ok=True.
      letters=True    letter-exact: the Phase A letters with >= min_inside of their mass inside
                      the box (= letters(lang, image, box=box)), for cutting inside a word.
      whole_components=False   a hard crop of the box (clamped to the image)."""
    box = _check_box(box, "block()")
    if letters:
        return _letters_fn(lang, image, box=box, min_inside=min_inside)
    src = f"res/{'en' if lang == 'de' else lang}/intro/{image}.png"
    w, h, cov = source_coverage(src)
    if not whole_components:
        x0, y0 = max(0, box[0]), max(0, box[1])
        x1, y1 = min(w - 1, box[2]), min(h - 1, box[3])
        if x1 < x0 or y1 < y0:
            return Layer.empty()
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        return Layer(x0, y0, bw, bh, [cov[(y0 + j) * w + x0 + i] for j in range(bh) for i in range(bw)],
                     text=f"{lang}:{image}:{tuple(box)}")
    taken, kept, inset = _split_components(cov, w, h, box, min_inside)
    if not partial_ok:
        _check_split("block()", box, taken, kept, inset, cov, w)
    keep = [i for comp in taken for i in comp]
    if not keep:
        return Layer.empty()
    bb = bbox_of((i % w, i // w) for i in keep)
    bw, bh = bb[2] - bb[0] + 1, bb[3] - bb[1] + 1
    data = [0] * (bw * bh)
    for i in keep:
        data[(i // w - bb[1]) * bw + (i % w - bb[0])] = cov[i]
    return Layer(bb[0], bb[1], bw, bh, data, text=f"{lang}:{image}:{tuple(box)}")


_letters_fn = letters                # block()'s letters= parameter shadows the function


# ----------------------------------------------------------------------------- CLI: selftest

# Re-typeset tests: (lang, image, line_text, baseline). Each is typeset by line() with a Font that
# excludes the line's own glyphs (and their copies in other languages), so every letter comes from
# OTHER occurrences where one exists, and the spacing model is fitted without the line.
SELFTEST_LINES = [
    ("en", "novela", "by Umberto Eco"),
    ("en", "pelicula", "film of the same name"),
    ("es", "novela", "en la novela"),
    ("es", "pacoyjuan", "inspirado en la obra de"),
    ("es", "pelicula", "del mismo nombre"),
    ("en", "novela", "inspired by the novel"),
    ("en", "pacoyjuan", "based on the work of"),
    ("es", "pacoyjuan", "Paco Menéndez"),
]
# Reported, not gated: letters whose spacing has (almost) no evidence outside the line itself.
SELFTEST_STRESS = {
    ("en", "pacoyjuan", "based on the work of"): "w and k occur nowhere else: their advances are "
                                                 "guessed from ink extents, and the error carries on",
    ("es", "pacoyjuan", "Paco Menéndez"): "P, z and é have one other occurrence each (Pazos, "
                                          "inspiré), at the other half-pixel phase",
}
# Gates for the other lines. A (the whole line re-typeset): its alpha MAE must stay within
# SELFTEST_A_BAND of the value measured when the kit was last accepted (round 6), in EITHER direction:
# worse is a regression; better is a change too (re-baseline after looking at the comparisons).
# B (glyph fidelity at the shipped pens): alpha MAE <= B_mae (measured: at most 0.49). A_pen_err:
# the largest pen error of A in half pixels.
SELFTEST_A_MAE = {
    ("en", "novela", "by Umberto Eco"): 5.008,
    ("en", "pelicula", "film of the same name"): 1.127,
    ("es", "novela", "en la novela"): 3.295,
    ("es", "pacoyjuan", "inspirado en la obra de"): 2.720,
    ("es", "pelicula", "del mismo nombre"): 1.349,
    ("en", "novela", "inspired by the novel"): 4.286,
}
SELFTEST_A_BAND = 1.0
SELFTEST_GATE = {"B_mae": 1.0, "A_pen_err": 2}
# Marks painted by hand after the glow was made (weaker glow than the model): model-check only.
HAND_PAINTED = {("es", "manuydani"): (220, 126, 242, 146)}


def _line_occurrences(lang: str, image: str, text: str) -> list[Occurrence]:
    occ = [o for o in _all_occurrences() if o.line == f"{lang}:{image}:{text}"]
    return sorted(occ, key=lambda o: o.char_i)


def _excluder(target: list[Occurrence]):
    """Exclude the target line's glyphs and every copy of them (the same word drawn at the same
    place in another language's version of the image)."""
    canon = {o.canon for o in target}
    return lambda o: o.canon in canon




def _compare(orig: Image.Image, new: Image.Image, box) -> dict:
    """Alpha and displayed-luminance (over black, the game's ground) differences in the box,
    over pixels where either image has alpha > 0; plus pixels changed outside the box."""
    po, pn = orig.load(), new.load()

    def lum(p):
        return (p[3] / 255.0) * (0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2])
    da, dl = [], []
    for y in range(box[1], box[3] + 1):
        for x in range(box[0], box[2] + 1):
            if po[x, y][3] or pn[x, y][3]:
                da.append(abs(po[x, y][3] - pn[x, y][3]))
                dl.append(abs(lum(po[x, y]) - lum(pn[x, y])))
    outside = [p for p in diff_pixels(orig, new)
               if not (box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3])]
    return {"pixels": len(da), "alpha_mae": round(sum(da) / len(da), 3), "alpha_max": max(da),
            "alpha_ge32": sum(1 for v in da if v >= 32), "lum_mae": round(sum(dl) / len(dl), 3),
            "lum_max": round(max(dl), 1), "changed_outside_box": len(outside)}


def _scaled(img: Image.Image, box, s: int, bg=(0, 0, 0)) -> Image.Image:
    x0, y0, x1, y1 = box
    c = img.crop((x0, y0, x1 + 1, y1 + 1))
    g = Image.new("RGBA", c.size, bg + (255,))
    g.alpha_composite(c)
    return g.convert("RGB").resize((c.width * s, c.height * s), Image.NEAREST)


def _diff_vis(a: Image.Image, b: Image.Image, box, s: int) -> Image.Image:
    x0, y0, x1, y1 = box
    pa, pb = a.load(), b.load()
    out = Image.new("RGB", (x1 - x0 + 1, y1 - y0 + 1))
    po = out.load()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = abs(pa[x, y][3] - pb[x, y][3])
            v = min(255, d * 4)
            po[x - x0, y - y0] = (v, v // 3, 0) if d else (0, 0, 0)
    return out.resize((out.width * s, out.height * s), Image.NEAREST)


def _sheet(rows: list[tuple[str, Image.Image]]) -> Image.Image:
    from PIL import ImageDraw
    wmax = max(im.width for _, im in rows)
    hh = sum(im.height + 14 for _, im in rows)
    sheet = Image.new("RGB", (wmax, hh), (60, 60, 60))
    d = ImageDraw.Draw(sheet)
    y = 0
    for label, im in rows:
        d.text((2, y + 1), label, fill=(255, 255, 0))
        sheet.paste(im, (0, y + 14))
        y += im.height + 14
    return sheet


def _sheet_h(cols: list[tuple[str, Image.Image]], gap: int = 12) -> Image.Image:
    from PIL import ImageDraw
    w = sum(im.width for _, im in cols) + gap * (len(cols) - 1)
    h = max(im.height for _, im in cols) + 14
    sheet = Image.new("RGB", (w, h), (60, 60, 60))
    d = ImageDraw.Draw(sheet)
    x = 0
    for label, im in cols:
        d.text((x + 2, 1), label, fill=(255, 255, 0))
        sheet.paste(im, (x, 14))
        x += im.width + gap
    return sheet


def cmd_selftest(args) -> int:
    out = Path(args.out) if args.out else KIT_OUT / "selftest"
    out.mkdir(parents=True, exist_ok=True)
    ok = True
    report = {"model_check": {}, "lines": [], "determinism": {}}

    # 1. the colour model reproduces every shipped credit image
    print("1. colour model: every pixel re-rendered from its own decomposed coverage")
    print("   gates outside the hand-painted box: alpha max <= 4, RGB max <= 2")
    worst = worst_rgb = 0
    for lang in LANGS:
        for image in IMAGES:
            cv = Canvas(shipped(lang, image), SCRIPT_BOXES[(lang, image)])
            m = cv.model_render()
            ex = HAND_PAINTED.get((lang, image))
            # alpha over every pixel, RGB over the pixels both images show (alpha > 0); both gated
            # outside the HAND_PAINTED box, whose figures are reported only
            ea, ea_ex, erg, erg_ex = [], [], [], []
            for i, (pm, q) in enumerate(zip(m.getdata(), cv.base)):
                x, y = i % cv.w, i // cv.w
                inside = ex and ex[0] <= x <= ex[2] and ex[1] <= y <= ex[3]
                (ea_ex if inside else ea).append(abs(pm[3] - q[3]))
                if q[3] > 0 and pm[3] > 0:
                    (erg_ex if inside else erg).append(max(abs(pm[k] - q[k]) for k in range(3)))
            mx, mean, rmx = max(ea), sum(ea) / len(ea), max(erg)
            worst = max(worst, mx)
            worst_rgb = max(worst_rgb, rmx)
            report["model_check"][f"{lang}/{image}"] = {"alpha_max": mx, "alpha_mean": round(mean, 4),
                                                        "rgb_max": rmx}
            note = ""
            if ex:
                report["model_check"][f"{lang}/{image}"]["hand_painted"] = {
                    "box": ex, "alpha_max": max(ea_ex), "rgb_max": max(erg_ex or [0])}
                note = f"   (hand-painted mark {ex}, not gated: alpha max {max(ea_ex)}, rgb max {max(erg_ex or [0])})"
            print(f"   {lang}/{image:9s} alpha max {mx}  mean {mean:.3f}  rgb max {rmx}{note}")
    if worst > 4:
        ok = False
        print("   FAIL: model alpha error > 4 levels")
    if worst_rgb > 2:
        ok = False
        print("   FAIL: model RGB error > 2 levels")

    # 2. re-typeset shipped lines from other occurrences
    print("2. re-typeset shipped lines from OTHER occurrences of the same letters")
    print("   A = the whole line in ONE line() call: only the start (left ink x, half-px phase and")
    print("       baseline of the first glyph) is taken from the original; every letter is the median")
    print("       of the other occurrences, and every advance and word space comes from a spacing fit")
    print("       made without this line (and without its copies in the other languages)")
    print("   B = the same glyphs placed at the shipped pen positions (glyph + glow fidelity only)")
    print("   MAE/max = mean/max |alpha difference| (0..255) over the pixels where either image has")
    print("   alpha > 0 in the line's box (ink + glow); lum = displayed luminance over black")
    for lang, image, text in SELFTEST_LINES:
        target = _line_occurrences(lang, image, text)
        assert target, (lang, image, text)
        font = Font(exclude=_excluder(target))
        base_line = target[0].baseline
        idx_of = [i for i, ch in enumerate(text) if ch != " "]
        # letters without another occurrence (or a special shape): the line's own pixels
        own_ids = {}
        for o, ci in zip(target, idx_of):
            if o.canon in ALTERNATES or not font.phases(o.char):
                own_ids[ci] = o.id
        own = [f"{text[ci]}@{ci}" for ci in sorted(own_ids)]
        # A: one line() call for the whole line, default word spaces
        o0 = target[0]
        src0 = own_ids.get(idx_of[0])
        ph_avail = _source_phases(font, o0.char, src0) if src0 else font.phases(o0.char)
        fp = o0.phase if o0.phase in ph_avail else None    # the other occurrences may lack it
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FrakturSpacingWarning)   # reported via spacing_guessed
            lay_a = line(text, ink_left(o0), base_line, first_phase=fp, font=font, prefer=own_ids)
        guessed_a = [f"{g['char']}@{g['index']}" for g in lay_a.glyphs if g["spacing_guessed"]]
        # B: every glyph at its shipped pen position. A letter the font has only at the other
        # phase goes on the neighbouring half pixel (pen -0.5 or +0.5) whose coverage centroid
        # lies nearer the shipped glyph's; those are counted in B_other_phase.
        parts_b = []
        other_phase = []
        for o, ci in zip(target, idx_of):
            if ci in own_ids or o.phase in font.phases(o.char):
                g = font.glyph(o.char, o.phase, own_ids.get(ci))
                parts_b.append(g.layer(o.xint, base_line))
                continue
            g = font.glyph(o.char, 1 - o.phase)
            cands = []
            for p_c in (o.p - 1, o.p + 1):
                lay_c = g.layer(p_c >> 1, base_line)
                sm = sum(v for _, _, v in lay_c.pixels())
                cx_c = sum((x + 0.5) * v for x, _, v in lay_c.pixels()) / sm
                cands.append((abs(cx_c - o.cx), p_c, lay_c))
            _, p_c, lay_c = min(cands, key=lambda t: (t[0], t[1]))
            parts_b.append(lay_c)
            other_phase.append(f"{o.char}@{ci}{(p_c - o.p) / 2:+.1f}px")
        lay_b = Layer.union(parts_b)
        src_img = shipped(lang, image)
        orig = load_rgba(src_img)
        old = Layer.union([Layer(o.x0, o.y0, o.w, o.h, o.data) for o in target])
        results = {}
        for tag, lay in (("A", lay_a), ("B", lay_b)):
            cv = Canvas(src_img, SCRIPT_BOXES[(lang, image)])
            cv.erase_layer(old)          # remove exactly the old line's coverage, keep the rest
            cv.draw(lay)
            results[tag] = (lay, cv.render())
        bb_old = old.bbox()
        bbs = [bb_old] + [r[0].bbox() for r in results.values()]
        box = (max(0, min(b_[0] for b_ in bbs) - 7), max(0, min(b_[1] for b_ in bbs) - 7),
               min(orig.width - 1, max(b_[2] for b_ in bbs) + 7), min(orig.height - 1, max(b_[3] for b_ in bbs) + 7))
        rec = {"line": f"{lang}/{image}: {text}", "box": box, "glyphs": len(target),
               "own_pixels_no_other_occurrence": own, "B_other_phase": other_phase,
               "A_spacing_guessed": guessed_a}
        for tag, (lay, new) in results.items():
            m = _compare(orig, new, box)
            if tag == "A":
                errs = [2 * g["x"] + g["phase"] - o.p for g, o in zip(lay.glyphs, target)]
                m["pen_err_half_px"] = errs
                m["pen_err_max"] = max(abs(e) for e in errs)
                m["glyphs_at_other_half_px_than_shipped"] = sum(1 for e in errs if e)
                m["glyph_sources"] = [f"{g['char']}<{g['source']}" for g in lay.glyphs]
            rec[tag] = m
            if m["changed_outside_box"]:
                ok = False
        report["lines"].append(rec)
        name = f"{lang}_{image}_{text.replace(' ', '_')}"
        new_a, new_b = results["A"][1], results["B"][1]
        for s_, bg, tag in ((6, (0, 0, 0), "x6"), (4, (0, 0, 0), "x4"), (6, (110, 140, 110), "x6_glow")):
            rows = [(f"shipped {lang}/{image}.png  (x{s_})", _scaled(orig, box, s_, bg)),
                    (f"A: re-typeset by fraktur.line(), letters from other occurrences  (x{s_})",
                     _scaled(new_a, box, s_, bg))]
            if tag != "x4":
                rows.append((f"B: same glyphs at the shipped pen positions  (x{s_})", _scaled(new_b, box, s_, bg)))
            if tag == "x6":
                rows.append(("|alpha diff| shipped vs A, x4 gain (6x)", _diff_vis(orig, new_a, box, s_)))
                rows.append(("|alpha diff| shipped vs B, x4 gain (6x)", _diff_vis(orig, new_b, box, s_)))
            _sheet(rows).save(out / f"{name}_{tag}.png")
        # side by side (shipped | A) at 6x and 4x; the stacked sheets above line the same x up
        for s_ in (6, 4):
            _sheet_h([(f"shipped {lang}/{image}.png (x{s_})", _scaled(orig, box, s_)),
                      (f"A: re-typeset, letters from other occurrences (x{s_})", _scaled(new_a, box, s_))]
                     ).save(out / f"{name}_x{s_}_sbs.png")
        ma, mb = rec["A"], rec["B"]
        stress = SELFTEST_STRESS.get((lang, image, text))
        rec["gated"] = stress is None
        print(f"   {rec['line']}" + (f"   (own pixels, no other occurrence: {' '.join(own)})" if own else "")
              + (f"\n      [stress line, reported only: {stress}]" if stress else "")
              + (f"\n      (B: only the other phase exists, placed at the nearer half pixel: "
                 f"{' '.join(other_phase)})" if other_phase else "")
              + (f"\n      (A: advance onto {' '.join(guessed_a)} uses a side no other line shows: "
                 f"spacing_guessed)" if guessed_a else ""))
        for tag, m in (("A", ma), ("B", mb)):
            print(f"      {tag}: alpha MAE {m['alpha_mae']:6.3f} max {m['alpha_max']:3d} "
                  f"(>=32: {m['alpha_ge32']:4d} of {m['pixels']} px)  displayed-lum MAE {m['lum_mae']:5.2f} max {m['lum_max']:5.1f}")
        print("      A pen error per glyph (half px): " + " ".join(
            f"{o.char}{e:+d}" for o, e in zip(target, ma["pen_err_half_px"])))
        if not stress:
            bad = []
            a_ref = SELFTEST_A_MAE[(lang, image, text)]
            rec["A"]["baseline_mae"] = a_ref
            print(f"      gate: A MAE {a_ref:.3f} +- {SELFTEST_A_BAND:g} (measured {ma['alpha_mae'] - a_ref:+.3f}), "
                  f"B MAE <= {SELFTEST_GATE['B_mae']:g}, A pen error <= {SELFTEST_GATE['A_pen_err']} half px")
            if ma["alpha_mae"] > a_ref + SELFTEST_A_BAND:
                bad.append(f"A MAE {ma['alpha_mae']} > baseline {a_ref} + {SELFTEST_A_BAND:g} (a regression)")
            elif ma["alpha_mae"] < a_ref - SELFTEST_A_BAND:
                bad.append(f"A MAE {ma['alpha_mae']} < baseline {a_ref} - {SELFTEST_A_BAND:g} (the spacing or "
                           f"glyphs changed: look at the comparisons, then re-baseline SELFTEST_A_MAE)")
            if mb["alpha_mae"] > SELFTEST_GATE["B_mae"]:
                bad.append(f"B MAE > {SELFTEST_GATE['B_mae']}")
            if ma["pen_err_max"] > SELFTEST_GATE["A_pen_err"]:
                bad.append(f"a pen off by more than {SELFTEST_GATE['A_pen_err']} half px")
            if bad:
                ok = False
                print("      FAIL: " + "; ".join(bad))

    # 3. API checks
    print("3. API checks")
    checks = []
    base = shipped("es", "novela")
    cv = Canvas(base)
    checks.append(("render() without edits returns the base bytes",
                   list(cv.render().getdata()) == list(load_rgba(base).getdata())))
    # erase one word and redraw it 1 px to the right: render() may rewrite only pixels within the
    # glow radius of a changed coverage pixel, and every rewritten pixel must agree with an
    # independent full model render of the new coverage (within the model's own error)
    de = occurrences("es", "novela", "de Umberto Eco")[:2]
    word = Layer.union([Layer(o.x0, o.y0, o.w, o.h, o.data) for o in de])
    cv = Canvas(base)
    cv.erase_layer(word)
    cv.draw(word.moved(1, 0))
    img = cv.render()
    ref = cv.model_render()
    chg = [(i % cv.w, i // cv.w) for i in range(len(cv.c)) if cv.c[i] != cv.c0[i]]
    near = {(x + ddx, y + ddy) for x, y in chg for ddy in range(-GLOW_R, GLOW_R + 1)
            for ddx in range(-GLOW_R, GLOW_R + 1)}
    ch = diff_pixels(base, img)
    far = [q for q in ch if q not in near]
    pi, pr = img.load(), ref.load()
    d_a = max([abs(pi[q][3] - pr[q][3]) for q in ch] or [99])
    d_rgb = max([max(abs(pi[q][k] - pr[q][k]) for k in range(3)) for q in ch if pi[q][3] >= 32 and pr[q][3] >= 32]
                or [99])
    checks.append((f"erase 'de' + redraw it 1 px right: {len(chg)} coverage px changed, {len(ch)} px rewritten, "
                   f"{len(far)} of them farther than {GLOW_R} px from a changed coverage px; rewritten px vs an "
                   f"independent full model render: alpha within {d_a}, RGB within {d_rgb} (alpha >= 32)",
                   len(ch) > len(chg) and not far and d_a <= 4 and d_rgb <= 4))
    # erase removes the glow with the text and leaves the neighbours' glow: after erasing 'de',
    # every pixel around the old 'de' (its glow zone, which also holds the glow of 'Umberto' and
    # of the line above) must equal an independent full model render of the remaining coverage
    cv = Canvas(base)
    x0e, x1e = ink_left(de[0]) - 1, ink_right(de[1]) + 1
    cv.cut((x0e, 150, x1e, 178))
    img = cv.render()
    ref = cv.model_render()
    u = occurrences("es", "novela", "de Umberto Eco")[2]
    zone = [(x, y) for y in range(140, 185) for x in range(x0e - 8, x1e + 9)]
    dz = max(abs(img.getpixel(q)[3] - ref.getpixel(q)[3]) for q in zone)
    gone = max(img.getpixel((x, y))[3] for x in range(x0e, x1e + 1) for y in range(158, 175))
    kept_u = min(img.getpixel((x, y))[3] for x in range(ink_left(u), ink_left(u) + 3) for y in range(170, 175)
                 if load_rgba(base).getpixel((x, y))[3] == 255)
    checks.append((f"cut('de' box): alpha left at the old 'de' {gone}; around it (glow of 'Umberto' and of "
                   f"line 2 included) render() = full model render within {dz} levels; 'U' stem alpha {kept_u}",
                   gone == 0 and dz <= 4 and kept_u == 255))
    # component erase: a box over the ink columns of 'de' only still removes the letters entirely,
    # including their faint anti-aliased fringe columns outside the box, and nothing of 'Umberto'
    cv = Canvas(base)
    removed = cv.erase_text((ink_left(de[0]), 152, ink_right(de[1]), 175))
    left = sum(1 for o in de for j in range(o.h) for i in range(o.w)
               if o.data[j * o.w + i] and cv.c[(o.y0 + j) * cv.w + o.x0 + i])
    fringe = sum(1 for o in de for j in range(o.h) for i in range(o.w)
                 if o.data[j * o.w + i] and not ink_left(de[0]) <= o.x0 + i <= ink_right(de[1]))
    u_ok = all(cv.c[(u.y0 + j) * cv.w + u.x0 + i] == u.data[j * u.w + i]
               for j in range(u.h) for i in range(u.w) if u.data[j * u.w + i])
    checks.append((f"erase_text() on the ink columns of 'de': {len(removed)} component(s) removed, {left} px "
                   f"of 'de' left (of which {fringe} px lay outside the box), 'U' untouched: {u_ok}",
                   bool(removed) and left == 0 and u_ok))
    # kerning overrides and word gaps
    l0 = line("av", 40, 174)
    l1 = line("av", 40, 174, kern={1: 0.5})
    l2 = line("av", 40, 174, kern={"av": 1})
    d1 = l1.glyphs[1]["pen"] - l0.glyphs[1]["pen"]
    d2 = l2.glyphs[1]["pen"] - l0.glyphs[1]["pen"]
    checks.append((f"kern {{1: 0.5}} moves v by {d1} px, {{'av': 1}} by {d2} px", (d1, d2) == (0.5, 1.0)))
    lg = line("av av", 40, 174, word_gap=11)
    gap = lg.glyphs[2]["ink_left"] - lg.glyphs[1]["ink_right"] - 1
    checks.append((f"word_gap=11 gives an ink gap of {gap}", gap == 11))
    la = line_after(occurrences("it", "pelicula", "Jean-Jacques Annaud", "d")[-1].id, "s")
    checks.append((f"line_after(it 'Annaud' d, 's') -> s at x {la.glyphs[0]['ink_left']}"
                   f"..{la.glyphs[0]['ink_right']}", la.glyphs[0]["ink_left"] > 249))
    lb = line_before(u.id, "de ")
    checks.append((f"line_before('U' of es 'Umberto', 'de ') puts d, e at "
                   f"{[(g['x'], g['phase']) for g in lb.glyphs]}, shipped {[(o.xint, o.phase) for o in de]}",
                   [(g["x"], g["phase"]) for g in lb.glyphs] == [(o.xint, o.phase) for o in de]))
    # blocks: the three names come out whole, without the neighbouring lines' fragments
    for lang_b, image_b, box_b, text_b in (("es", "pacoyjuan", (50, 120, 210, 150), "Paco Menéndez"),
                                           ("it", "pelicula", (30, 131, 252, 165), "Jean-Jacques Annaud"),
                                           ("es", "novela", (60, 150, 200, 182), "de Umberto Eco")):
        b = block(lang_b, image_b, box_b)
        occ_b = [o for o in occurrences(lang_b, image_b, text_b) if ink_left(o) >= box_b[0]]
        whole = sum(1 for o in occ_b if all(b.get(o.x0 + i, o.y0 + j) == o.data[j * o.w + i]
                                            for j in range(o.h) for i in range(o.w) if o.data[j * o.w + i]))
        foreign = sum(1 for x_, y_, _ in b.pixels()
                      if not any(o.x0 <= x_ < o.x0 + o.w and o.y0 <= y_ < o.y0 + o.h for o in occ_b))
        checks.append((f"block({lang_b}, {image_b}, {box_b}): {whole}/{len(occ_b)} letters of "
                       f"'{text_b}' whole, {foreign} px from other lines", whole == len(occ_b) and foreign == 0))
    # the documented builder example: erase_text of en novela line 1 leaves line 2 intact
    cv = Canvas(shipped("en", "novela"), SCRIPT_BOXES[("en", "novela")])
    cv.erase_text((21, 88, 300, 122))
    l1 = occurrences("en", "novela", "inspired by the novel")
    l2 = occurrences("en", "novela", "“The Name of the Rose”")
    left1 = sum(1 for o in l1 for j in range(o.h) for i in range(o.w)
                if o.data[j * o.w + i] and cv.c[(o.y0 + j) * cv.w + o.x0 + i])
    ok2 = all(cv.c[(o.y0 + j) * cv.w + o.x0 + i] == o.data[j * o.w + i]
              for o in l2 for j in range(o.h) for i in range(o.w) if o.data[j * o.w + i])
    checks.append((f"erase_text(en novela line 1 box): {left1} px of line 1 left, line 2 intact: {ok2}",
                   left1 == 0 and ok2))
    cv2 = Canvas.shipped("en", "novela")
    cv2.erase((21, 88, 300, 122))
    checks.append(("Canvas.erase(box) (default whole_letters=True) == erase_text(box)", cv2.c == cv.c))

    # prefer={char: "lang:image"} at every start x and phase: the pen snaps to a half pixel the
    # image has the letter at, and the letter comes from that image
    occ_ix = _occurrence_index()
    fails, n_try, n_lack = [], 0, 0
    for t, ch_, src_ in (("la la", "a", "en:novela"), ("namn", "n", "es:novela"), ("namn", "m", "en:pelicula"),
                         ("ana", "a", "es:pacoyjuan"), ("anam", "m", "de:pelicula"), ("vän", "ä", "es:novela"),
                         ("aba", "b", "en:novela"), ("aya", "y", "en:novela")):
        lang_, image_ = src_.split(":")
        lang_ = "en" if lang_ == "de" else lang_
        fnt = default_font()
        ph_first = _source_phases(fnt, t[0], src_) if t[0] == ch_ else fnt.phases(t[0])
        for x_ in range(30, 34):
            for fp in (0, 1):
                n_try += 1
                if fp not in ph_first:
                    n_lack += 1                   # the first letter lacks that phase: ValueError
                    try:
                        line(t, x_, 114, prefer={ch_: src_}, first_phase=fp)
                        fails.append(f"{t}/{x_}/{fp}: first_phase the letter lacks accepted")
                    except ValueError:
                        pass
                    continue
                try:
                    lay = line(t, x_, 114, prefer={ch_: src_}, first_phase=fp)
                    base_ch_ = COMPOSED[ch_][0] if ch_ in COMPOSED else ch_
                    for g in lay.glyphs:
                        if g["char"] == ch_:
                            sid = g["glyph"].members[0] if g["glyph"].source.startswith("composed") else g["source"]
                            o_ = occ_ix[sid]
                            if (o_.char, o_.lang, o_.image) != (base_ch_, lang_, image_) or o_.canon in ALTERNATES:
                                fails.append(f"{t}/{x_}/{fp}: {sid}")
                except Exception as e:  # noqa: BLE001 - reported as a failed check
                    fails.append(f"{t}/{x_}/{fp}: {type(e).__name__} {e}")
    checks.append((f"prefer {{char: 'lang:image'}}: {n_try - n_lack - len(fails)}/{n_try - n_lack} lines typeset "
                   f"with a plain (not ALTERNATES) letter from that image, incl. b and y of en novela (swash 'by' "
                   f"there); {n_lack} first_phase values the first letter lacks there: ValueError"
                   + (f"; failures {fails[:3]}" if fails else ""), not fails))
    alt_msgs = []
    for ch_, src_ in (("T", "en:novela"), ("“", "en:novela"), ("L", "fr:novela")):
        try:
            line("a" + ch_ + "a", 30, 114, prefer={ch_: src_})
            alt_msgs.append(f"{ch_}: accepted")
        except KeyError:
            pass
    checks.append((f"prefer T/“/L from the only images that have them (ALTERNATES only) -> KeyError: "
                   f"{'all' if not alt_msgs else alt_msgs}", not alt_msgs))
    try:
        line("la", 30, 114, prefer={"a": "it:loading"})
        msg_e = "no error"
    except KeyError as e:
        msg_e = str(e)
    checks.append((f"prefer an image without the letter -> KeyError up front: {msg_e[:70]}", "has no" in msg_e))
    # kerning: a 0.5-px kern on the first glyph selects the other phase; bad keys raise
    k0, k1 = line("av", 30, 114), line("av", 30, 114, kern={0: 0.5})
    d0 = k1.glyphs[0]["pen"] - k0.glyphs[0]["pen"]
    bad_keys = []
    for kk in ({"a": 3}, {"avs": 1}, {"a ": 1}, {1: 1}, {5: 1}, {1.0: 1}):
        try:
            line("a v", 30, 114, kern=kk)
            bad_keys.append(f"{kk} accepted")
        except ValueError:
            pass
    checks.append((f"kern {{0: 0.5}} moves the first glyph's pen by {d0} px (phase {k0.glyphs[0]['phase']} -> "
                   f"{k1.glyphs[0]['phase']}); kern keys 'a', 'avs', 'a ', a space index, out of range, a float: "
                   f"{'all rejected' if not bad_keys else bad_keys}", d0 == 0.5 and not bad_keys))
    # script boxes: required, found for shipped paths, de = en; the en pacoyjuan 'and' cut leaves
    # every kept pixel outside its box alone (the 'J' of 'Juan' keeps its glow)
    try:
        Canvas(load_rgba(shipped("en", "pacoyjuan")))
        msg_t = "no error"
    except TypeError:
        msg_t = "TypeError"
    auto = Canvas(shipped("en", "pacoyjuan")).script_boxes == [tuple(b) for b in SCRIPT_BOXES[("en", "pacoyjuan")]]
    de_ok = (Canvas.shipped("de", "pacoyjuan").script_boxes == Canvas.shipped("en", "pacoyjuan").script_boxes
             and all(SCRIPT_BOXES[("de", i)] == SCRIPT_BOXES[("en", i)] for i in IMAGES))
    checks.append((f"Canvas(PIL image) without script_boxes: {msg_t}; a shipped path finds its boxes: {auto}; "
                   f"de = en (SCRIPT_BOXES, Canvas.shipped): {de_ok}", msg_t == "TypeError" and auto and de_ok))
    and_box = SCRIPT_BOXES[("en", "pacoyjuan")][0]
    b_pj = load_rgba(shipped("en", "pacoyjuan"))
    cv = Canvas.shipped("en", "pacoyjuan")
    cv.cut(and_box)
    img = cv.render()
    moved = [q for q in diff_pixels(b_pj, img)
             if not (and_box[0] <= q[0] <= and_box[2] and and_box[1] <= q[1] <= and_box[3])]
    checks.append((f"Canvas.shipped('en','pacoyjuan').cut('and' box): {len(moved)} px outside the box changed, "
                   f"'J' glow at (81,159) alpha {b_pj.getpixel((81, 159))[3]} -> {img.getpixel((81, 159))[3]}",
                   not moved and img.getpixel((81, 159)) == b_pj.getpixel((81, 159))))
    cv = Canvas.shipped("en", "pacoyjuan")
    and_lay = cv.coverage_layer(and_box, script=True)
    cv.cut(and_box)
    cv.draw_script(and_lay)
    n_s = len(diff_pixels(b_pj, cv.render()))
    cv = Canvas.shipped("en", "pacoyjuan")
    cv.cut(and_box)
    cv.draw(and_lay)
    n_g = len(diff_pixels(b_pj, cv.render()))
    checks.append((f"draw_script() puts the 'and' back with no glow: {n_s} px differ from the base "
                   f"(draw() would give it a glow: {n_g} px)", n_s == 0 and n_g > 0))
    # moon window: the rule is absolute; two shipped bases already break it (the base= form misses that)
    b_es, b_en = shipped("es", "pacoyjuan"), shipped("en", "pelicula")
    same = Canvas.shipped("es", "pacoyjuan").render()
    n_es, n_en = len(moon_pixels(b_es)), len(moon_pixels(b_en))
    checks.append((f"moon_pixels (the rule, absolute): shipped es pacoyjuan {n_es} px, en pelicula {n_en} px (glow "
                   f"a build must remove); an unchanged es pacoyjuan render {len(moon_pixels(same))} px, but "
                   f"{len(moon_pixels(same, base=b_es))} with the base= diagnostic (so base= is not the rule); the "
                   f"demo images are checked with the absolute form in 4.",
                   n_es == 17 and n_en == 11 and len(moon_pixels(same)) == 17 and not moon_pixels(same, base=b_es)))
    # composed letters: tick gap equal on both phases, ring inside the accent rows
    f_ = default_font()
    tick_gaps = {}
    for c_ in "äö":
        for ph_ in f_.phases(c_):
            g_ = f_.glyph(c_, ph_)
            cols = sorted({g_.ox + i for j in range(g_.h) for i in range(g_.w)
                           if g_.oy + j <= TICK_ROWS_TOP and g_.data[j * g_.w + i] >= 128})
            runs = []
            for xx in cols:
                if runs and runs[-1][1] == xx - 1:
                    runs[-1][1] = xx
                else:
                    runs.append([xx, xx])
            tick_gaps[(c_, ph_)] = runs[1][0] - runs[0][1] - 1 if len(runs) == 2 else None
    ring_rows = sorted({f_.glyph("å", ph_).oy + j for ph_ in f_.phases("å") for j in range(f_.glyph("å", ph_).h)
                        if f_.glyph("å", ph_).oy + j <= TICK_ROWS_TOP
                        and any(f_.glyph("å", ph_).data[j * f_.glyph("å", ph_).w:(j + 1) * f_.glyph("å", ph_).w])})
    tg = set(tick_gaps.values())
    checks.append((f"ä/ö tick clear gap (px) per phase {tick_gaps}; å ring rows {ring_rows[0]}..{ring_rows[-1]}",
                   len(tg) == 1 and None not in tg and min(tg) >= 2 and ring_rows[0] >= -CAP_TOP and ring_rows[-1] <= -18))
    # opening quote before every capital: 1 px of ink at the closest row, as shipped
    q_gaps = {}
    for c_ in [c for c in f_.chars() if c.isupper()]:
        lq = line("”" + c_, 40, 144)
        q_gaps[c_] = _row_gap(lq.glyphs[0]["glyph"], lq.glyphs[0]["x"], lq.glyphs[1]["glyph"], lq.glyphs[1]["x"])
    lq = line("”R", 40, 144, kern={"”R": 0})
    off = _row_gap(lq.glyphs[0]["glyph"], lq.glyphs[0]["x"], lq.glyphs[1]["glyph"], lq.glyphs[1]["x"])
    checks.append((f"”+capital closest ink gap {q_gaps} (shipped “T/“E/“L: 1); with an explicit kern the fit is "
                   f"off (”R {off})", set(q_gaps.values()) == {QUOTE_CAP_GAP} and off > QUOTE_CAP_GAP))
    # erase / block split a joined component -> ValueError, nothing changed (round-3 fix)
    for what, box_ in (("'R' of Rose", (224, 123, 241, 150)), ("'Ros'", (224, 123, 262, 150))):
        cv = Canvas.shipped("en", "novela")
        try:
            cv.erase(box_)
            msg_s = "no error"
        except ValueError:
            msg_s = "ValueError"
        unchanged = cv.c == cv.c0
        try:
            block("en", "novela", box_)
            msg_b = "no error"
        except ValueError:
            msg_b = "ValueError"
        removed = Canvas.shipped("en", "novela").erase(box_, partial_ok=True)
        checks.append((f"erase/block of a box over {what} {box_} (splits 'Rose'): erase {msg_s}, image unchanged "
                       f"{unchanged}; block {msg_b}; with partial_ok=True erase removes {len(removed)} component(s)",
                       msg_s == msg_b == "ValueError" and unchanged))
    # letter-exact: letters / erase_letters / block(letters=True)
    l2t = "“The Name of the Rose”"
    rose = occurrences("en", "novela", l2t)
    o_o = [o for o in rose if o.word.startswith("Rose") and o.char == "o"][0]
    lr = letters("en", "novela", l2t, "R")
    cv = Canvas.shipped("en", "novela")
    cv.erase_letters("en", "novela", l2t, "R")
    o_px = [(o_o.x0 + i, o_o.y0 + j) for j in range(o_o.h) for i in range(o_o.w) if o_o.data[j * o_o.w + i]]
    o_whole = all(cv.c[y * cv.w + x] == cv.c0[y * cv.w + x] for x, y in o_px)
    r_left = sum(1 for x, y, _ in lr.pixels() if cv.c[y * cv.w + x] and (x, y) not in set(o_px))
    lb_ = block("en", "novela", (224, 123, 262, 150), letters=True)
    checks.append((f"letters(en novela, '{l2t}', 'R') = {[g['char'] for g in lr.glyphs]}; erase_letters('R'): "
                   f"{r_left} px of the R left (besides pixels it shares with the o), 'o' whole: {o_whole}; "
                   f"block(box over 'Ros', letters=True) = {''.join(g['char'] for g in lb_.glyphs)}",
                   [g["char"] for g in lr.glyphs] == ["R"] and r_left == 0 and o_whole
                   and "".join(g["char"] for g in lb_.glyphs) == "Ros"))
    cv_a = Canvas.shipped("es", "novela")
    cv_a.erase_letters("es", "novela", "de Umberto Eco")
    cv_b = Canvas.shipped("es", "novela")
    cv_b.erase((30, 150, 300, 185))
    um_ = letters("es", "novela", "de Umberto Eco", "Umberto Eco")
    um_b = block("es", "novela", (60, 150, 200, 182))
    same_um = all(um_.get(x, y) == um_b.get(x, y) for x, y, _ in um_b.pixels()) and \
        all(um_.get(x, y) == um_b.get(x, y) for x, y, _ in um_.pixels())
    checks.append((f"erase_letters(whole es novela line 3) == erase(line box): {cv_a.c == cv_b.c}; letters('Umberto "
                   f"Eco') == block(its box) pixel for pixel: {same_um}", cv_a.c == cv_b.c and same_um))
    # small API fixes
    n_de, n_en = len(occurrences("de", "novela")), len(occurrences("en", "novela"))
    try:
        line("ab", None, 114)
        msg_n = "no error"
    except ValueError:
        msg_n = "ValueError"
    try:
        default_font().glyph("a", 0, "v__es_novela_108_95")
        msg_g = "no error"
    except ValueError:
        msg_g = "ValueError"
    try:
        crop = block("es", "novela", (-5, 200, 10, 215), whole_components=False)
        msg_c = f"{crop.x0},{crop.y0} {crop.w}x{crop.h}"
    except Exception as e:  # noqa: BLE001 - reported as a failed check
        msg_c = f"{type(e).__name__}"
    checks.append((f"occurrences('de','novela') {n_de} = en {n_en}; line(x=None, no pen) {msg_n}; glyph('a', "
                   f"source=a 'v') {msg_g}; hard-crop block off the image clamps to {msg_c}",
                   n_de == n_en > 0 and msg_n == msg_g == "ValueError" and msg_c == "0,200 11x8"))
    # spacing evidence: guessed sides are flagged and warned about; the planned wordings have none
    with warnings.catch_warnings(record=True) as wl:
        warnings.simplefilter("always", FrakturSpacingWarning)
        bw_ = _line_occurrences("en", "pacoyjuan", "based on the work of")
        f_st = Font(exclude=_excluder(bw_))
        lw = line("work of", 30, 114, font=f_st,
                  prefer={o.char: o.id for o in bw_ if o.char in "wk"})   # their only (own) pixels
        lq_ = line("”Rosens namn” är", 30, 144)
        n_warn = len([w_ for w_ in wl if issubclass(w_.category, FrakturSpacingWarning)])
        clean = [line(t_, 30, 114) for t_ in ("efter romanen", "”Rosens namn”", "efter spelet av",
                                              "film med samma namn", "av")]
        n_warn_clean = len([w_ for w_ in wl if issubclass(w_.category, FrakturSpacingWarning)]) - n_warn
    fl_w = [g["char"] for g in lw.glyphs if g["spacing_guessed"]]
    fl_q = [g["char"] for g in lq_.glyphs if g["spacing_guessed"]]
    fl_c = [g["char"] for l_ in clean for g in l_.glyphs if g["spacing_guessed"]]
    checks.append((f"spacing_guessed: 'work of' without the en pacoyjuan line flags {fl_w}; '”Rosens namn” är' "
                   f"flags {fl_q}; {n_warn} FrakturSpacingWarning(s); the Swedish wordings flag {fl_c} "
                   f"({n_warn_clean} warnings)",
                   fl_w == ["o", "k", "o"] and fl_q == ["ä"] and n_warn == 4 and not fl_c and n_warn_clean == 0))
    # copies: identical pixels at the same place in another language count once
    ix = _occurrence_index()
    want_cp = ["U_C__es_manuydani_169_137", "e__es_manuydani_186_142", "l__es_manuydani_194_137",
               "e__es_manuydani_201_142", "m__es_manuydani_209_142", "b__it_pacoyjuan_27_93",
               "a__it_pacoyjuan_38_98", "LEFT_DOUBLE_QUOTATION_MARK__es_novela_40_124"]
    n_cp = sum(1 for i_ in want_cp if ix[i_].copy_of)
    checks.append((f"copies with other word labels (en Celemin/es Celemín, en based/it basato, en/es “): "
                   f"{n_cp}/{len(want_cp)} counted once", n_cp == len(want_cp)))
    # the å ring: the same pixels on both phases, a dark 2x2 hole, strong cores on all four sides,
    # and the font's slant (top row's ink right of the bottom row's, like the i-dot tick's)
    def row_centroid(cell: dict, y: int) -> float:
        r_ = [(x, v) for (x, yy), v in cell.items() if yy == y]
        return sum(x * v for x, v in r_) / sum(v for _, v in r_)

    ring_ok = []
    for ph_ in f_.phases("å"):
        g_ = f_.glyph("å", ph_)
        cell = {(g_.ox + i, g_.oy + j): g_.data[j * g_.w + i] for j in range(g_.h) for i in range(g_.w)
                if g_.oy + j <= TICK_ROWS_TOP}
        hx = min(x for (x, y), v in cell.items() if y == -20 and v >= 128) + 1     # hole's left column
        hole = [cell.get((hx + i, -20 + j), 0) for j in (0, 1) for i in (0, 1)]
        side_cores = [max(v for (x, y), v in cell.items() if y == yy and (x < hx if s_ < 0 else x > hx + 1))
                      for yy in (-20, -19) for s_ in (-1, 1)]
        top_bot = [max(v for (x, y), v in cell.items() if y == yy) for yy in (-21, -18)]
        ring_ok.append((ph_, max(hole), min(side_cores + top_bot),
                        round(row_centroid(cell, -21) - row_centroid(cell, -18), 2)))
    tk = f_._tick(0)
    tcell = {(tk.ox + i, tk.oy + j): tk.data[j * tk.w + i] for j in range(tk.h) for i in range(tk.w)}
    slant_i = round(row_centroid(tcell, -21) - row_centroid(tcell, -18), 2)
    checks.append((f"å ring per phase (phase, hole max, min core, top-row minus bottom-row ink centroid px): "
                   f"{ring_ok}; the i-dot tick's (phase 0): {slant_i} px",
                   all(h_ <= 51 and c_ >= 221 and 0.4 <= s_ <= 1.0 for _, h_, c_, s_ in ring_ok)))

    # round 4: fragments of old neighbours (the median s0 carried the e of 'based'; P1 the a of
    # 'Pazos'; U0 the ’ of 'd’Umberto')
    au = fragment_audit(f_)
    known_odd = {"d__it_pacoyjuan_196_94", "i__it_pacoyjuan_207_96"}   # it 'lavoro_di': other shapes
    rej = {r_[2] for r_ in au["rejected"]}
    checks.append((f"fragments: {au['checked']} word-initial/final occurrences used by a variant equal it within 2 "
                   f"levels on the pixels they own alone (off: {au['boundary'] or 'none'}); boundary occurrences "
                   f"the median drops: {sorted(rej)} (it 'lavoro_di': a d with a looped ascender, an i with a "
                   f"long tick); neighbour ink left in a variant: {au['stubs'] or 'none'} (without the "
                   f"subtraction: {len(au['stubs_pass1'])} px, in {sorted({s_[:2] for s_ in au['stubs_pass1']})})",
                   not au["boundary"] and rej <= known_odd and not au["stubs"]))
    s0 = f_.glyph("s", 0)
    s_fin = _occurrence_glyph(occ_ix["s__en_pelicula_285_106"])        # line-final 'Annaud’s'
    d_s = max(abs(s0.layer(0, 0).get(xx, yy) - s_fin.layer(0, 0).get(xx, yy))
              for xx in range(-8, 9) for yy in range(-24, 4))
    checks.append((f"s phase 0 = median of {len(s0.members)} (round 3: of 1, the s of 'based'); vs the line-final s "
                   f"of en pelicula 'Annaud’s': max |difference| {d_s} levels", d_s <= 2 and len(s0.members) >= 2))
    # two neighbours from one shipped line keep their shipped spacing; a kern moves the second
    # from there and its recorded phase/pen is the drawn one (round-4 fix)
    d_o, e_o = de[0], de[1]
    pr = {0: d_o.id, 1: e_o.id}
    k_res = {}
    for k_ in (0, 0.5, -0.5, 1):
        g1 = line("de", 40, 174, prefer=pr, kern={1: k_} if k_ else None).glyphs[1]
        k_res[k_] = (g1["pen"], g1["phase"], g1["glyph"].phase)   # recorded pen/phase, drawn phase
    l_de = line("de", 40, 174, prefer=pr).glyphs
    ok_k = (all(v[1] == v[2] for v in k_res.values()) and k_res[0.5][0] > k_res[0][0]
            and k_res[-0.5][0] < k_res[0][0] and k_res[1][0] == k_res[0][0] + 1
            and l_de[1]["pen"] - l_de[0]["pen"] == (e_o.p - d_o.p) / 2)
    show_k = ", ".join(f"{k}: pen {v[0]} phase {v[1]} drawn {v[2]}" for k, v in k_res.items())
    checks.append((f"prefer two neighbours of es novela 'de' (shipped spacing kept) + kern on the e: {show_k} "
                   f"(the e exists at phase {e_o.phase} only there: a 0.5 kern snaps a whole px its way)", ok_k))
    # word_gap: a half-pixel kern at a word start is a phase change; list length and phases checked
    w0 = line("av av", 40, 114, word_gap=11)
    w1 = line("av av", 40, 114, word_gap=11, kern={3: 0.5})
    w2 = line("av av", 40, 114, word_gap=11, kern={3: 1})
    errs = []
    for t_, kw_ in (("av av av", {"word_gap": [11]}), ("av av av", {"word_gap": [11, 11, 11]}),
                    ("av av av", {"word_gap": [(11, 0), (11, 2)]}), ("av av", {"word_gap": (11, 1)}),
                    ("av av av", {"word_gap": [(11, 0), 11], "kern": {3: 0.5}}), ("av av", {"word_gap": 11.0}),
                    ("a Ca", {"word_gap": [(11, 0)]})):
        try:
            line(t_, 40, 114, **kw_)
            errs.append(f"{t_!r} {kw_} accepted")
        except ValueError:
            pass
    dw1 = w1.glyphs[2]["pen"] - w0.glyphs[2]["pen"]
    dw2 = w2.glyphs[2]["pen"] - w0.glyphs[2]["pen"]
    checks.append((f"word_gap=11 + kern 0.5 / 1 at the word start moves it {dw1} / {dw2} px; a word_gap list of the "
                   f"wrong length, a bad entry, a phase the letter lacks (C), or a phase plus a half-pixel kern: "
                   f"{'all ValueError' if not errs else errs}", dw1 == 0.5 and dw2 == 1.0 and not errs))
    # keys that match nothing in the text
    errs = []
    for kw_ in ({"prefer": {"z": "en:novela"}}, {"kern": {"zz": 3}}, {"kern": {"va": 1}}, {"prefer": {" ": "en:novela"}}):
        try:
            line("av", 40, 114, **kw_)
            errs.append(f"{kw_} accepted")
        except ValueError:
            pass
    d_it = occurrences("it", "pelicula", "Jean-Jacques Annaud", "d")[-1]
    la0 = line_after(d_it.id, "s")
    la1 = line_after(d_it.id, "s", kern={"ds": 1})
    checks.append((f"prefer / kern keys absent from the text: {'all ValueError' if not errs else errs}; "
                   f"line_after('d', 's', kern={{'ds': 1}}) accepted, moves s {la1.glyphs[0]['pen'] - la0.glyphs[0]['pen']} px",
                   not errs and la1.glyphs[0]["pen"] - la0.glyphs[0]["pen"] == 1.0))
    # coverage_layer clamps; moved() takes whole pixels; glyphs are immutable
    cv = Canvas.shipped("es", "novela")
    cl_a, cl_b = cv.coverage_layer((-5, -5, 10, 10)), cv.coverage_layer((0, 0, 10, 10))
    cl_c, cl_d = cv.coverage_layer((310, 200, 330, 215)), cv.coverage_layer((400, 0, 410, 5))
    try:
        Layer(0, 0, 1, 1, [255]).moved(1.5, 0)
        msg_m = "accepted"
    except ValueError:
        msg_m = "ValueError"
    ga_ = f_.glyph("a", 0)
    try:
        ga_.data[0] = 0
        msg_i = "mutable"
    except TypeError:
        msg_i = "TypeError"
    lg_ = line("aa", 40, 114).glyphs[0]["glyph"]
    occ0 = occurrences("es", "novela")[0]
    checks.append((f"coverage_layer box off the image clamps ({cl_a.x0},{cl_a.y0} {cl_a.w}x{cl_a.h} = (0,0,10,10): "
                   f"{cl_a.data == cl_b.data}; past the corner {cl_c.w}x{cl_c.h}; outside {cl_d.w}x{cl_d.h}); "
                   f"moved(1.5, 0) {msg_m}; glyph data write {msg_i}, line() glyph is the font's immutable "
                   f"glyph: {lg_ is f_.glyph('a', lg_.phase)}, occurrence data {type(occ0.data).__name__}",
                   (cl_a.x0, cl_a.y0, cl_a.w, cl_a.h) == (0, 0, 11, 11) and cl_a.data == cl_b.data
                   and (cl_c.w, cl_c.h) == (10, 8) and cl_d.w == 0 and msg_m == "ValueError" and msg_i == "TypeError"
                   and isinstance(ga_.data, tuple) and isinstance(occ0.data, tuple)))
    # 'index' = index into the text (spaces counted) in line() and letters(); letter_index without
    ul = letters("es", "novela", "de Umberto Eco", "Umberto Eco").glyphs[0]
    ut = line("de Umberto Eco", 40, 174).glyphs[2]
    checks.append((f"glyph dict keys: 'U' of es 'de Umberto Eco' from letters(): index {ul['index']} letter_index "
                   f"{ul['letter_index']}; from line(): index {ut['index']} letter_index {ut['letter_index']}",
                   (ul["index"], ul["letter_index"]) == (ut["index"], ut["letter_index"]) == (3, 2)))
    # MARKED: the letters whose ink above the x-height is a separate mark (none on row -17, ink
    # above and below it) are exactly MARKED
    derived = []
    for c_ in f_.chars():
        rows_ = set()
        for ph_ in f_.phases(c_):
            g_ = f_.glyph(c_, ph_)
            rows_ |= {g_.oy + j for j in range(g_.h) if any(v >= 128 for v in g_.data[j * g_.w:(j + 1) * g_.w])}
        if any(y < TICK_ROWS_TOP for y in rows_) and TICK_ROWS_TOP not in rows_ and any(y > TICK_ROWS_TOP for y in rows_):
            derived.append(c_)
    checks.append((f"letters with a separate mark (ink above row -17, none on it): {''.join(derived)} = MARKED "
                   f"{''.join(sorted(MARKED))}", sorted(derived) == sorted(MARKED)))
    # marks keep MARK_MIN_GAP clear px on both sides (the fit), or are flagged and warned about:
    # every pair (marked letter, any letter) at every pen phase, in both orders
    sw = [c for c in f_.chars() if c.isalpha() and (c.isascii() or c in "äöå")]   # the Swedish letters
    worst_s, crowded, silent, fitted, n_pairs, n_warn_m = {}, set(), [], set(), 0, 0
    for m_ in MARKED:
        for c_ in [c for c in f_.chars() if c.isalpha()]:
            for t_ in (c_ + m_, m_ + c_):
                for d_ in (0.0, 0.25, 0.5, 0.75):
                    with warnings.catch_warnings(record=True) as wl_:
                        warnings.simplefilter("always", FrakturSpacingWarning)
                        lm = line(t_, None, 114, pen=40 + d_, allow_ring=True)
                    n_pairs += 1
                    gb2 = lm.glyphs[1]
                    gp = gb2["mark_gap"]
                    n_w = sum(1 for w_ in wl_ if "mark of" in str(w_.message))
                    n_warn_m += n_w
                    if gb2["mark_fit"]:
                        fitted.add(t_)
                    if gp is not None and gp < MARK_MIN_GAP:
                        crowded.add(t_)
                        if not (gb2["mark_crowded"] and n_w == 1):
                            silent.append(t_)
                    elif gb2["mark_crowded"] or n_w:
                        silent.append(t_ + "(false flag)")
                    if gp is not None and all(c in sw for c in t_) and any(c in "äöå" for c in t_):
                        worst_s[t_] = min(worst_s.get(t_, 99), gp)
    swedish_crowded = sorted(t_ for t_, v in worst_s.items() if v < MARK_MIN_GAP)
    le = line("éd", 40, 114, kern={1: 0})
    min_sw = min(v for t_, v in worst_s.items() if t_ != "öI")
    checks.append((f"mark fit over {n_pairs} (marked letter, letter) pairs x pen phases, both orders: composed "
                   f"ä/ö/å next to any Swedish letter, before or after, keep >= {min_sw} clear px at every pen "
                   f"phase, except {swedish_crowded or 'none'} (a capital I inside a word: {worst_s.get('öI')} px); "
                   f"moved by the fit: {len(fitted)} pairs; still under "
                   f"{MARK_MIN_GAP} px after 1 px of fit, all flagged mark_crowded + warned ({n_warn_m} warnings): "
                   f"{' '.join(sorted(crowded))}; unflagged: {silent or 'none'}; 'éd' with an explicit kern: fit "
                   f"{le.glyphs[1]['mark_fit']}, flag {le.glyphs[1]['mark_crowded']}",
                   not silent and min_sw >= MARK_MIN_GAP and set(swedish_crowded) <= {"öI"}
                   and le.glyphs[1]["mark_fit"] == 0 and not le.glyphs[1]["mark_crowded"]))
    # line_before with word_gap: the last glyph stays within 0.25 px of the font's advance before
    # the kept glyph (round-4 bug: 0.48 px), the gaps are the asked ink px
    lb_bad, lb_n, lb_moved = [], 0, 0
    for lang_, lt_ in (("es", "de Umberto Eco"), ("en", "by Umberto Eco")):
        u_ = [o for o in occurrences(lang_, "novela", lt_) if o.char == "U"][0]
        for t_, wg_ in (("efter av ", 9), ("efter av ", 11), ("efter av ", 12), ("efter av ", 13),
                        ("efter romanen av ", 10), ("efter romanen av ", 11), ("ett två av ", None),
                        ("efter romanen av ", [(11, 1), 12]), ("efter romanen av ", [(12, 0), 11])):
            for dx_ in range(-2, 4):
                lb_n += 1
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", FrakturSpacingWarning)
                        lay_ = line_before(u_.id, t_, dx_, word_gap=wg_, allow_ring=True)   # 'två'
                except Exception as e:  # noqa: BLE001 - reported as a failed check
                    lb_bad.append(f"{t_!r}/{wg_}/{dx_}: {type(e).__name__}")
                    continue
                g_l = lay_.glyphs[-1]
                gaps_ = [b_["ink_left"] - a_["ink_right"] - 1 for a_, b_ in zip(lay_.glyphs, lay_.glyphs[1:])
                         if t_[b_["index"] - 1] == " "]
                want_g = ([wg_] * len(gaps_) if isinstance(wg_, int) else
                          [w_ if isinstance(w_, int) else w_[0] for w_ in wg_] if wg_ else gaps_)
                if abs(g_l["to_kept_err"]) > 0.25 or gaps_ != want_g:
                    lb_bad.append(f"{t_!r}/{wg_}/{dx_}: err {g_l['to_kept_err']} gaps {gaps_}")
                lb_moved += g_l["to_kept_err"] != 0
    with warnings.catch_warnings(record=True) as wl_:
        warnings.simplefilter("always", FrakturSpacingWarning)
        lf_ = line_before(u.id, "efter av ", 0, word_gap=[(12, 1)])
    n_wf = sum(1 for w_ in wl_ if "no start within" in str(w_.message))
    gf_ = lf_.glyphs[-1]
    ok_f = gf_["to_kept_off"] and abs(gf_["to_kept_err"]) > 0.25 and n_wf == 1
    checks.append((f"line_before(U of es/en 'Umberto', 'efter av ' / 'efter romanen av ' / 'ett två av ', word_gap "
                   f"9..13, None, lists) at dx -2..3: {lb_n - len(lb_bad)}/{lb_n} with the last glyph within 0.25 px "
                   f"of the font's advance before the kept U and the asked ink gaps"
                   + (f"; off: {lb_bad[:4]}" if lb_bad else "") + f"; a last-word phase fixed where it cannot "
                   f"land ('efter av ', [(12, 1)]): nearest start used, to_kept_off {gf_['to_kept_off']}, "
                   f"to_kept_err {gf_['to_kept_err']:+.3f} px, {n_wf} FrakturSpacingWarning",
                   not lb_bad and ok_f))
    # line_before robustness (round 6): seeded random texts (letters incl. marked ones, 1-3 words) before
    # the U of es/en 'Umberto' and the P of es 'Paco', dx -4..4, word_gap None/10/11/12: never an
    # exception; where no start lands, the nearest is used, flagged and warned about
    import random
    rng = random.Random(20261027)
    pool = [c for c in f_.chars() if c.isalpha() and c not in UNREVIEWED]
    anchors = [[o for o in occurrences(lg_, "novela", lt_) if o.char == "U"][0].id
               for lg_, lt_ in (("es", "de Umberto Eco"), ("en", "by Umberto Eco"))]
    anchors.append([o for o in occurrences("es", "pacoyjuan", "Paco Menéndez") if o.char == "P"][0].id)
    rb_n, rb_exc, rb_off, rb_unflagged, rb_worst = 0, [], 0, [], 0.0
    for _ in range(300):
        words = ["".join(rng.choice(pool) for _ in range(rng.randint(1, 5))) for _ in range(rng.randint(1, 3))]
        t_ = " ".join(words) + " "
        wg_ = rng.choice([None, 10, 11, 12])
        a_ = rng.choice(anchors)
        dx_ = rng.randint(-4, 4)
        rb_n += 1
        try:
            with warnings.catch_warnings(record=True) as wl_:
                warnings.simplefilter("always", FrakturSpacingWarning)
                g_l = line_before(a_, t_, dx_, word_gap=wg_).glyphs[-1]
        except Exception as e:  # noqa: BLE001 - reported as a failed check
            rb_exc.append(f"{t_!r}/{wg_}/{dx_}: {type(e).__name__} {e}"[:120])
            continue
        warned = any("no start within" in str(w_.message) for w_ in wl_)
        tol_ = 0.25 if len(f_.phases(g_l["char"])) == 2 else 0.5     # as line_before: one phase -> 0.5
        if g_l["to_kept_off"]:
            rb_off += 1
            rb_worst = max(rb_worst, abs(g_l["to_kept_err"]))
        if g_l["to_kept_off"] != warned or g_l["to_kept_off"] != (abs(g_l["to_kept_err"]) > tol_ + 1e-9):
            rb_unflagged.append(f"{t_!r}/{wg_}/{dx_}")
    sw_n, sw_off = 0, []
    for t_ in ("av ", "efter romanen av ", "efter spelet av ", "film med samma namn och ", "efter ", "och "):
        for a_ in anchors:
            for dx_ in range(-4, 5):
                for wg_ in (None, 10, 11, 12):
                    sw_n += 1
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", FrakturSpacingWarning)
                        if line_before(a_, t_, dx_, word_gap=wg_).glyphs[-1]["to_kept_off"]:
                            sw_off.append(f"{t_!r}/{a_[:3]}/{dx_}/{wg_}")
    checks.append((f"line_before robustness: {rb_n} seeded random texts (marked letters included) before the U of "
                   f"es/en 'Umberto' and the P of 'Paco', dx -4..4, word_gap None/10/11/12: {len(rb_exc)} exceptions"
                   + (f" {rb_exc[:2]}" if rb_exc else "") + f"; {rb_off} landed off target (nearest start, worst "
                   f"{rb_worst:.3f} px, each flagged to_kept_off + warned; mis-flagged: {rb_unflagged[:3] or 'none'}); "
                   f"Swedish wordings x 3 anchors x dx -4..4 x 4 word gaps: {len(sw_off)}/{sw_n} off target"
                   + (f" {sw_off[:3]}" if sw_off else ""),
                   not rb_exc and not rb_unflagged and not sw_off))
    # argument checks: positions, kern values, word gaps, first_phase
    errs = []
    for what, fn in (("x float", lambda: line("av", 40.5, 114)), ("x = 160 / 2", lambda: line("av", 320 / 2, 114)),
                     ("baseline float", lambda: line("av", 40, 114.0)), ("x bool", lambda: line("av", True, 114)),
                     ("x and pen", lambda: line("av", 40, 114, pen=40.0)), ("pen str", lambda: line("av", None, 114, pen="4")),
                     ("kern value str", lambda: line("av", 40, 114, kern={1: "1"})),
                     ("kern value bool", lambda: line("av", 40, 114, kern={1: True})),
                     ("kern value nan", lambda: line("av", 40, 114, kern={1: float("nan")})),
                     ("word_gap -5", lambda: line("av av", 40, 114, word_gap=-5)),
                     ("word_gap [-1]", lambda: line("av av", 40, 114, word_gap=[-1])),
                     ("word_gap [(-1, 0)]", lambda: line("av av", 40, 114, word_gap=[(-1, 0)])),
                     ("first_phase 2", lambda: line("av", 40, 114, first_phase=2)),
                     ("first_phase -1", lambda: line("av", 40, 114, first_phase=-1)),
                     ("first_phase True", lambda: line("av", 40, 114, first_phase=True)),
                     ("first_phase 0 of 'C' (phase 1 only)", lambda: line("Ca", 40, 114, first_phase=0)),
                     ("first_phase with pen", lambda: line("av", None, 114, pen=40.0, first_phase=1)),
                     ("first_phase + half-px kern", lambda: line("av", 40, 114, first_phase=0, kern={0: 0.5})),
                     ("line_before first_phase", lambda: line_before(u.id, "av ", first_phase=0)),
                     ("line_before x", lambda: line_before(u.id, "av ", x=3)),
                     ("line_after pen", lambda: line_after(d_it.id, "s", pen=3.0)),
                     ("line_before dx float", lambda: line_before(u.id, "av ", 1.5))):
        try:
            fn()
            errs.append(f"{what}: accepted")
        except ValueError:
            pass
        except Exception as e:  # noqa: BLE001 - the wrong error type is a failure too
            errs.append(f"{what}: {type(e).__name__}")
    ok_c = (line("Ca", 40, 114).glyphs[0]["phase"] == 1 and line("av", 40, 114).glyphs[0]["phase"] == 0
            and line("av", 40, 114, first_phase=1).glyphs[0]["phase"] == 1)
    # round 6: the unreviewed å needs allow_ring=True (line, line_before, line_after)
    ring_errs = []
    for what, fn in (("line('på')", lambda: line("på", 40, 114)),
                     ("line_before(U, 'på ')", lambda: line_before(u.id, "på ")),
                     ("line_after(d, 'å')", lambda: line_after(d_it.id, "å")),
                     ("allow_ring='yes'", lambda: line("på", 40, 114, allow_ring="yes"))):
        try:
            fn()
            ring_errs.append(f"{what}: accepted")
        except ValueError:
            pass
    ring_ok = (len(line("på", 40, 114, allow_ring=True).glyphs) == 2
               and len(line_before(u.id, "på ", allow_ring=True).glyphs) == 2
               and len(line("pä pö", 40, 114).glyphs) == 4)
    checks.append((f"å without allow_ring=True (line, line_before, line_after, a non-bool flag): "
                   f"{'all ValueError' if not ring_errs else ring_errs}; with allow_ring=True typeset, ä/ö need no "
                   f"flag: {ring_ok}", not ring_errs and ring_ok))
    # round 6: inverted boxes raise (they used to select nothing and leave the old text in place)
    inv = (300, 120, 20, 85)
    box_errs = []
    cv_i = Canvas.shipped("es", "novela")
    for what, fn in (("Canvas.erase", lambda: cv_i.erase(inv)), ("Canvas.erase_text", lambda: cv_i.erase_text(inv)),
                     ("Canvas.erase(whole_letters=False)", lambda: cv_i.erase(inv, whole_letters=False)),
                     ("Canvas.cut", lambda: cv_i.cut(inv)), ("Canvas.coverage_layer", lambda: cv_i.coverage_layer(inv)),
                     ("Canvas.erase_letters(box=)", lambda: cv_i.erase_letters("es", "novela", box=inv)),
                     ("block", lambda: block("es", "novela", inv)),
                     ("block(letters=True)", lambda: block("es", "novela", inv, letters=True)),
                     ("block(whole_components=False)", lambda: block("es", "novela", inv, whole_components=False)),
                     ("letters(box=)", lambda: letters("es", "novela", box=inv)),
                     ("erase()", lambda: erase(shipped("es", "novela"), [inv])),
                     ("composite(cut=)", lambda: composite(shipped("es", "novela"), cut=[inv])),
                     ("Canvas(script_boxes=[inverted])", lambda: Canvas(shipped("es", "novela"), [inv])),
                     ("Canvas.cut((1, 2, 3))", lambda: cv_i.cut((1, 2, 3))),
                     ("Canvas.cut(float box)", lambda: cv_i.cut((1.0, 2, 3, 4)))):
        try:
            fn()
            box_errs.append(f"{what}: accepted")
        except ValueError:
            pass
    one_px = Canvas.shipped("es", "novela").coverage_layer((5, 5, 5, 5))
    checks.append((f"inverted box {inv} (x1 < x0, y1 < y0), a 3-tuple, a float box: "
                   f"{'all ValueError' if not box_errs else box_errs}; canvas unchanged: {cv_i.c == cv_i.c0}; a "
                   f"1x1 box (x0 = x1) is fine: {one_px.w}x{one_px.h}",
                   not box_errs and cv_i.c == cv_i.c0 and (one_px.w, one_px.h) == (1, 1)))
    # round 6: coverage falling off the canvas raises unless clip_ok=True
    long_ = line("efter romanen efter romanen efter", 30, 174)
    cv_o = Canvas.shipped("es", "novela")
    try:
        cv_o.draw(long_)
        msg_o = "drawn"
    except ValueError as e:
        msg_o = "ValueError" if "fall off" in str(e) else f"ValueError? {e}"
    untouched = cv_o.c == cv_o.c0
    cv_o.draw(long_, clip_ok=True)
    clipped = cv_o.c != cv_o.c0
    neg = line("av", 0, 114)
    cv_n = Canvas.shipped("es", "novela")
    try:
        cv_n.draw(neg.moved(-3, 0))
        msg_n2 = "drawn"
    except ValueError:
        msg_n2 = "ValueError"
    try:
        cv_n.draw_script(neg.moved(0, 120))
        msg_s2 = "drawn"
    except ValueError:
        msg_s2 = "ValueError"
    try:
        composite(shipped("es", "novela"), long_)
        msg_c2 = "drawn"
    except ValueError:
        msg_c2 = "ValueError"
    inside_ok = True
    try:
        Canvas.shipped("es", "novela").draw(line("efter romanen", 28, 114))
    except ValueError:
        inside_ok = False
    checks.append((f"draw() of a line off the right edge (ink bbox {long_.ink_bbox()}): {msg_o}, canvas untouched "
                   f"{untouched}; with clip_ok=True drawn {clipped}; off the left edge {msg_n2}; draw_script off the "
                   f"bottom {msg_s2}; composite() {msg_c2}; a line inside the canvas draws: {inside_ok}",
                   msg_o == msg_n2 == msg_s2 == msg_c2 == "ValueError" and untouched and clipped and inside_ok))
    checks.append((f"argument checks (float/bool x or baseline, x with pen, str/bool/nan kern values, negative word "
                   f"gaps, first_phase 2/-1/True, a phase the first letter lacks, with pen, with a half-pixel kern, "
                   f"position args to line_before/line_after): {'all ValueError' if not errs else errs}; "
                   f"first_phase=None takes 'C' at its only phase 1: {ok_c}", not errs and ok_c))
    for msg, good in checks:
        print(f"   {'ok  ' if good else 'FAIL'} {msg}")
        ok &= good
    report["api_checks"] = [{"check": m, "ok": g} for m, g in checks]

    # 4. determinism: build the same image twice from scratch, compare bytes
    print("4. determinism")
    hashes = []
    for _ in range(2):
        global _OCC_CACHE, _OCC_INDEX, _DECOMP_CACHE, _DEFAULT_FONT, _OWNERS_CACHE
        _OCC_CACHE, _OCC_INDEX, _DECOMP_CACHE, _DEFAULT_FONT, _OWNERS_CACHE = None, None, {}, None, None
        demos = _demo_images()
        hashes.append({k: hashlib.sha256(save_rgba_png(img, None)).hexdigest() for k, (img, _) in demos.items()})
    same_h = hashes[0] == hashes[1]
    report["determinism"] = {"sha256_run1": hashes[0], "sha256_run2": hashes[1], "identical": same_h}
    for k in hashes[0]:
        print(f"   demo {k:9s} built twice from scratch: {hashes[0][k][:16]}… {hashes[1][k][:16]}… "
              f"identical={hashes[0][k] == hashes[1][k]}")
    ok &= same_h
    moon = {k: len(moon_pixels(demos[k][0])) for k in ("novela", "pacoyjuan", "pelicula")}
    report["demo_moon_pixels"] = moon
    print(f"   moon window (absolute rule: no alpha at x >= 250, y < 100) of the demo images: {moon}")
    ok &= not any(moon.values())
    (out / "selftest.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"comparisons and selftest.json in {out}")
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def _demo_images() -> dict[str, tuple[Image.Image, list[str]]]:
    """API demos on the three Swedish credit wordings (GLOSSARY §8). NOT the shipped assets:
    the novela/pacoyjuan/pelicula builders own those (script conjunctions, final placement)."""
    out = {}
    # novela: 'efter romanen' / '”Rosens namn”' / 'av Umberto Eco' on es novela
    cv = Canvas.shipped("es", "novela")
    cv.erase((20, 85, 300, 120))                 # line 1 'en la novela': its words + glow
    cv.erase((30, 121, 300, 150))                # line 2 '“El Nombre de la Rosa”'
    l3 = "de Umberto Eco"
    um = letters("es", "novela", l3, "Umberto Eco")         # the kept name, letter-exact
    u_id = um.glyphs[0]["source"]
    dx = align_before(u_id, "av ", 40)           # 'av' on line 2's left edge (x 40): dx = 3
    cv.erase_letters("es", "novela", l3)         # the whole old line 3
    cv.draw(line("efter romanen", 28, 114))
    cv.draw(line("”Rosens namn”", 40, 144))      # the opening ” is fitted to the R (1 px)
    cv.draw(um.moved(dx, 0))
    cv.draw(line_before(u_id, "av ", dx))        # the font's word space before the kept 'U'
    out["novela"] = (cv.render(), [f"base es novela; 'Umberto Eco' kept as shipped pixels, moved {dx:+d} px"
                                   " so that 'av' starts at x 40 like line 2"])
    # pacoyjuan: 'efter spelet av' / 'Paco Menéndez' / (script 'och') 'Juan Delcán'
    cv = Canvas.shipped("es", "pacoyjuan")
    cv.erase((20, 85, 300, 120))                 # 'inspirado en la obra de'
    cv.draw(line("efter spelet av", 28, 114))
    out["pacoyjuan"] = (cv.render(), ["base es pacoyjuan; the script 'y' is left for the builder"])
    # pelicula: (script 'och' own line) / 'Jean-Jacques Annauds' / 'film med samma namn'
    cv = Canvas.shipped("en", "pelicula")
    cv.erase((20, 100, 300, 132))                # 'in Jean-Jacques Annaud’s'
    cv.erase((20, 132, 300, 165))                # 'film of the same name'
    jja = block("it", "pelicula", (36, 131, 249, 162))     # it 'Jean-Jacques Annaud', baseline 156
    #   (row 130 holds the 'f' descender of the line above: a box reaching it raises ValueError)
    dx, dy = 0, 126 - 156
    cv.draw(jja.moved(dx, dy))
    d_it = occurrences("it", "pelicula", "Jean-Jacques Annaud", "d")[-1]
    cv.draw(line_after(d_it.id, "s", dx, dy))
    cv.draw(line("film med samma namn", 36, 156))
    out["pelicula"] = (cv.render(), ["base en pelicula; 'Jean-Jacques Annaud' = it pixels moved up 30;"
                                     " the script 'and' is left for the builder"])
    # composed letters (optional): a test card, not a planned wording
    cv = Canvas(Image.new("RGBA", (320, 208), (0, 0, 0, 0)), script_boxes=())
    cv.draw(line("löst höra kör män är", 20, 40))
    cv.draw(line("vän sätt både på åra", 20, 72, allow_ring=True))         # å: the review card
    cv.draw(line("”Rosens namn” är vår", 20, 104, kern={14: 0}, allow_ring=True))   # ” -> ä: unobserved, by eye
    cv.draw(line("list hit mina ríp lián", 20, 136))   # the font's own i-dots and accents
    cv.draw(line("född höll bröd söka", 20, 168))      # ö before ascenders: the mark fit
    out["composed"] = (cv.render(), ["ä/ö = a/o + two copies of the font's i-dot tick, each over a "
                                     "stem as on the i; å = a + a slanted elliptical ring (no model in the "
                                     "font; not for use without review)"])
    return out


def cmd_demo(args) -> int:
    out = Path(args.out) if args.out else KIT_OUT / "demo"
    out.mkdir(parents=True, exist_ok=True)
    bad = 0
    for name, (img, notes) in _demo_images().items():
        png = save_rgba_png(img, out / f"{name}.png")
        moon = moon_pixels(img)                  # the rule: absolute, not relative to the base
        bad += bool(moon) and name != "composed"
        print(f"{name}: {out / (name + '.png')} sha256 {hashlib.sha256(png).hexdigest()}  "
              f"moon-window pixels {len(moon)} {bbox_of(moon) or ''}  ({'; '.join(notes)})")
        if name == "composed":                   # the test card, scaled for viewing (black ground)
            bb = img.getchannel("A").getbbox()  # (x0, y0, x1 + 1, y1 + 1) of alpha > 0
            box = (max(0, bb[0] - 4), max(0, bb[1] - 4), min(img.width - 1, bb[2] + 3), min(img.height - 1, bb[3] + 3))
            for s_ in (2, 4, 6):
                _scaled(img, box, s_).save(out / f"composed_x{s_}.png")
    return 1 if bad else 0


# ----------------------------------------------------------------------------- CLI: others

def cmd_info(args) -> int:
    f = default_font()
    print(f"chars: {f.chars()}")
    print(f"x-height {X_HEIGHT}, cap top {CAP_TOP} above the baseline, line pitch {LINE_PITCH}")
    print(f"spacing fit: {f.n_obs} observations, word space advance {f.space:.2f} px")
    rs = [abs(d - p - f.pair_kern.get((a, b), 0.0)) if not sp else abs(d - p) for a, b, sp, d, p in f.residuals]
    print(f"  |residual| after pair kerning: mean {sum(rs) / len(rs):.3f} px, max {max(rs):.2f} px")
    print("variants (char phase: source, spread = mean L1 of the members vs the median on the pixels they own "
          "alone; shared px = pixels every member shares with a neighbour, set to the union minus that "
          "neighbour's own shape):")
    for (ch, ph), g in sorted(f._variants.items()):
        fi = f.fragment_info[(ch, ph)]
        print(f"  {ch!r} {ph}: {g.source:16s} spread {g.spread:5.2f}  {g.w}x{g.h} ox {g.ox} oy {g.oy} "
              f"ink {g.ink_left()}..{g.ink_right()}  R {f.R[ch]:.2f} L {f.L[ch]:.2f}"
              + (f"  shared px changed {fi['resolved_px']}" if fi["resolved_px"] else "")
              + (f"  joins kept {fi['joined_px_kept']}" if fi["joined_px_kept"] else ""))
    au = fragment_audit(f)
    print(f"fragment audit: {au['checked']} word-initial/final occurrences = their variant within 2 levels "
          f"(off: {au['boundary'] or 'none'}); dropped by the median: {[r[2] for r in au['rejected']]}; "
          f"neighbour ink left: {au['stubs'] or 'none'} (pass 1, before the subtraction: {au['stubs_pass1']})")
    guessed = sorted(f"{w} of {c!r}" for (w, c), n in f.n_side.items() if n == 0)
    once = sorted(f"{w} of {c!r}" for (w, c), n in f.n_side.items() if n == 1)
    print(f"sides never observed (guessed; line() sets spacing_guessed and warns): {', '.join(guessed) or 'none'}")
    print(f"sides observed in one pair only: {', '.join(once) or 'none'}")
    big = sorted(((abs(v), k, v) for k, v in f.pair_kern.items()), reverse=True)[:25]
    print("largest pair kerning (px):", ", ".join(f"{a}{b} {v:+.2f}" for _, (a, b), v in big))
    return 0


def cmd_sheet(args) -> int:
    from PIL import ImageDraw
    f = default_font()
    keys = sorted(f._variants) + [(c, p) for c in sorted(COMPOSED) for p in f.phases(c)]
    s = 6
    # each cell fits its widest/tallest glyph whole (round 6: the fixed 26 px cell cut the widest
    # glyphs' right edge, which draw() now refuses), with 6 px of margin for the glow at the left
    # and baseline row 25 (ascenders reach row 25 - 21 = 4)
    def place(g):
        return 6 - g.ox if g.ox < -6 else 6
    cell_w = max(26, max(place(f.glyph(c, p)) + f.glyph(c, p).ox + f.glyph(c, p).w for c, p in keys) + 6)
    cell_h = max(34, max(25 + f.glyph(c, p).oy + f.glyph(c, p).h for c, p in keys) + 4)
    cols = 12
    rows = (len(keys) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w * s, rows * (cell_h * s + 14)), (50, 50, 50))
    d = ImageDraw.Draw(sheet)
    for k, (ch, ph) in enumerate(keys):
        g = f.glyph(ch, ph)
        cv = Canvas(Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0)), script_boxes=())
        cv.draw(g.layer(place(g), 25))
        img = cv.render()
        bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
        bg.alpha_composite(img)
        cx, cy = (k % cols) * cell_w * s, (k // cols) * (cell_h * s + 14)
        sheet.paste(bg.convert("RGB").resize((cell_w * s, cell_h * s), Image.NEAREST), (cx, cy + 14))
        d.text((cx + 2, cy + 1), f"{ch} {ph} {g.source[:18]}", fill=(255, 255, 0))
    outp = Path(args.out) if args.out else KIT_OUT / "glyph_sheet.png"
    outp.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(outp)
    print(f"wrote {outp}")
    return 0


def _parse_box(s: str):
    v = tuple(int(t) for t in s.split(","))
    if len(v) != 4:
        raise ValueError(f"box {s!r}: give x0,y0,x1,y1")
    return v


def cmd_typeset(args) -> int:
    base = args.base or None
    img = load_rgba(base) if base else Image.new("RGBA", (320, 208), (0, 0, 0, 0))
    if args.script == ["none"] or not base:
        sb = ()
    elif args.script:
        sb = [_parse_box(b) for b in args.script]
    else:
        sb = None                    # a shipped --base finds its own; any other base must say
        if _shipped_key(base) is None:
            print(f"{base} is not a shipped credit image: give its script ink as --script x0,y0,x1,y1 "
                  f"(repeatable) or --script none", file=sys.stderr)
            return 2
    try:
        cv = Canvas(base if sb is None else img, sb)
        for b in args.cut:
            cv.cut(_parse_box(b))
    except ValueError as e:
        print(f"typeset: {e}", file=sys.stderr)
        return 2
    for b in args.erase:
        try:
            cv.erase(_parse_box(b), partial_ok=args.partial_ok)
        except ValueError as e:
            print(f"--erase: {e} (CLI: --partial-ok)", file=sys.stderr)
            return 2
    try:
        lay = line(args.text, args.x, args.baseline, word_gap=args.word_gap, first_phase=args.phase,
                   allow_ring=args.allow_ring)
        cv.draw(lay, clip_ok=args.clip_ok)
    except (ValueError, KeyError) as e:
        print(f"typeset: {e} (CLI: --allow-ring for an å, --clip-ok to cut ink off the canvas)", file=sys.stderr)
        return 2
    out = cv.render()
    outp = Path(args.out) if args.out else KIT_OUT / "typeset.png"
    png = save_rgba_png(out, outp)
    print(f"wrote {outp} sha256 {hashlib.sha256(png).hexdigest()}")
    print(f"ink bbox {lay.ink_bbox()}  glyphs: " + " ".join(
        f"{g['char']}@{g['x']}{'+' if g['phase'] else ''}" for g in lay.glyphs))
    print(f"moon-window pixels (the rule: must be 0): {len(moon_pixels(out))}; added by this edit "
          f"(diagnostic): {len(moon_pixels(out, base=img))}; changed box {cv.changed_box()}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("selftest")
    p.add_argument("--out")
    sub.add_parser("info")
    p = sub.add_parser("demo")
    p.add_argument("--out")
    p = sub.add_parser("sheet")
    p.add_argument("--out")
    p = sub.add_parser("typeset")
    p.add_argument("text")
    p.add_argument("--x", type=int, required=True)
    p.add_argument("--baseline", type=int, required=True)
    p.add_argument("--base")
    p.add_argument("--erase", action="append", default=[],
                   help="x0,y0,x1,y1: remove the connected components (whole words) mostly inside the box")
    p.add_argument("--partial-ok", action="store_true", help="let an --erase box split a joined component")
    p.add_argument("--cut", action="append", default=[], help="x0,y0,x1,y1: hard cut")
    p.add_argument("--script", action="append", default=[],
                   help="x0,y0,x1,y1 of script ink in --base, or 'none' (a shipped --base finds its own)")
    p.add_argument("--word-gap", type=int)
    p.add_argument("--phase", type=int, choices=(0, 1), default=None,
                   help="half-pixel phase of the first glyph (default: 0 where the letter has it)")
    p.add_argument("--allow-ring", action="store_true", help="typeset the unreviewed composed å")
    p.add_argument("--clip-ok", action="store_true", help="cut coverage that falls off the canvas")
    p.add_argument("--out")
    a = ap.parse_args(argv)
    return {"selftest": cmd_selftest, "info": cmd_info, "sheet": cmd_sheet, "typeset": cmd_typeset,
            "demo": cmd_demo}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())

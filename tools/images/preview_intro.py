# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Preview a Swedish intro image the way the game composites it (abadia.r, images.md §4), next to
the shipped es and en screens, plus zoomed crops of the text.

  uv run tools/images/preview_intro.py NAME [--sv PATH] [--out DIR] [--box x0,y0,x1,y1]

NAME is one of loading manuydani pacoyjuan novela pelicula pulsa. --sv defaults to
assets_sv/res/de/intro/NAME.png; --out to work/phaseD/preview/NAME/. Writes:
  sim_es.png sim_en.png sim_sv.png   the full 320x208 screen at 3x (black ground; the moon window
                                     clip (250,0,70,100) from manuydani on; monje and logo under pulsa)
  compare.png                        es / en / sv screens stacked at 2x, labelled
  zoom_es.png zoom_en.png zoom_sv.png  the text box at 6x (default: union of the alpha>0 boxes,
                                     below the title art for loading)
and prints rule findings: size, colour type, ink or glow inside the moon window (x >= 250, y < 100),
alpha outside the text box for logo-like files. It never writes into assets_sv/.
"""
import argparse
import pathlib
import sys

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[2]
RES = ROOT / "work" / "jar" / "res"
ORDER = ["loading", "manuydani", "pacoyjuan", "novela", "pelicula", "monje", "logo", "pulsa"]


def load(lang, name):
    return Image.open(RES / lang / "intro" / f"{name}.png").convert("RGBA")


def screen(img, name, lang_bg="es"):
    l = ORDER.index(name)
    scr = Image.new("RGBA", (320, 208), (0, 0, 0, 255))
    if l > 0:
        corner = Image.new("RGBA", (320, 208), (0, 0, 0, 0))
        corner.alpha_composite(load(lang_bg, "luna"))
        corner.alpha_composite(load(lang_bg, "niebla"))
        corner.alpha_composite(load(lang_bg, "ventana"))
        scr.alpha_composite(corner.crop((250, 0, 320, 100)), (250, 0))
    if l > 5:
        scr.alpha_composite(load(lang_bg, "monje"))
    if l > 6:
        scr.alpha_composite(load("es", "logo"))   # the Swedish build copies the es logo
    scr.alpha_composite(img, ((320 - img.width) // 2, (208 - img.height) // 2))
    return scr


def bbox(img, y_min=0):
    a = img.getchannel("A").point(lambda v: 255 if v > 0 else 0)
    if y_min:
        a = a.crop((0, y_min, img.width, img.height))
        b = a.getbbox()
        return None if b is None else (b[0], b[1] + y_min, b[2], b[3] + y_min)
    return a.getbbox()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", choices=[n for n in ORDER if n not in ("monje", "logo")])
    ap.add_argument("--sv")
    ap.add_argument("--out")
    ap.add_argument("--box")
    a = ap.parse_args()
    sv_path = pathlib.Path(a.sv) if a.sv else ROOT / "assets_sv" / "res" / "de" / "intro" / f"{a.name}.png"
    out = pathlib.Path(a.out) if a.out else ROOT / "work" / "phaseD" / "preview" / a.name
    if (ROOT / "assets_sv") in out.resolve().parents:
        sys.exit("refusing to write previews into assets_sv/")
    out.mkdir(parents=True, exist_ok=True)
    raw = Image.open(sv_path)
    orig_de = Image.open(RES / "de" / "intro" / f"{a.name}.png")
    findings = []
    if raw.size != (320, 208):
        findings.append(f"SIZE {raw.size}, must be (320, 208)")
    if raw.mode != orig_de.mode:
        findings.append(f"MODE {raw.mode}, the original de file is {orig_de.mode} (keep the colour type)")
    imgs = {"es": load("es", a.name), "en": load("en", a.name), "sv": raw.convert("RGBA")}
    alpha = imgs["sv"].getchannel("A")
    moon = [(x, y) for y in range(100) for x in range(250, 320) if alpha.getpixel((x, y)) > 0]
    if moon and a.name != "loading":
        findings.append(f"MOON WINDOW: {len(moon)} pixels with alpha > 0 at x >= 250, y < 100 (first {moon[:5]})")
    y_min = 175 if a.name == "loading" else 0
    if a.box:
        box = tuple(int(v) for v in a.box.split(","))
    else:
        boxes = [b for b in (bbox(im, y_min) for im in imgs.values()) if b]
        box = (max(0, min(b[0] for b in boxes) - 4), max(0, min(b[1] for b in boxes) - 4),
               min(320, max(b[2] for b in boxes) + 4), min(208, max(b[3] for b in boxes) + 4))
    sims = {}
    for lang, im in imgs.items():
        sims[lang] = screen(im, a.name)
        sims[lang].convert("RGB").resize((960, 624), Image.NEAREST).save(out / f"sim_{lang}.png")
        crop = sims[lang].crop(box)
        crop.convert("RGB").resize((crop.width * 6, crop.height * 6), Image.NEAREST).save(out / f"zoom_{lang}.png")
    sheet = Image.new("RGB", (640, 3 * (416 + 18)), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    for k, lang in enumerate(("es", "en", "sv")):
        d.text((4, k * 434 + 2), f"{lang}: {a.name}.png as composited in game", fill=(255, 255, 0))
        sheet.paste(sims[lang].convert("RGB").resize((640, 416), Image.NEAREST), (0, k * 434 + 16))
    sheet.save(out / "compare.png")
    print(f"previews in {out} (zoom box {box})")
    for f in findings:
        print("FINDING", f)
    print(f"{len(findings)} findings")


if __name__ == "__main__":
    main()

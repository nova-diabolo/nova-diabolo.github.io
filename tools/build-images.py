#!/usr/bin/env python3
"""
Regenerate the web-sized images in assets/img/ from the originals/ folder.

The originals are several MB each and must never be served directly. This script
makes the small WebP/JPEG derivatives the site actually loads.

Usage:   python3 tools/build-images.py
Needs:   pip3 install --user Pillow

Each entry below names a file in originals/ (without the .jpg) plus a crop:
centre-x, centre-y, and how much of the height to keep. Nudge those, re-run,
and look at the page.
"""
from PIL import Image, ImageOps
from pathlib import Path
import glob, sys

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / "originals"
OUT  = ROOT / "assets" / "img"

# ---- what goes where ------------------------------------------------------
# (photo number, centre-x, centre-y, fraction of height kept) — tune the crop
# by nudging the centre and the zoom, then re-run and look at the page.
HERO = ("group", 0.50, 0.46, 0.80)            # group shot, cropped to 4:5

TEAM = {                                       # one portrait each, cropped 3:4
    "anderson": ("anderson", 0.52, 0.56, 0.88),
    "hayato":   ("hayato",   0.50, 0.50, 0.92),
    "michael":  ("michael",  0.52, 0.52, 0.86),
    "tia":      ("tia",      0.50, 0.50, 0.92),
    # landscape stage shot: crop around her and the diabolo, keep the spotlight
    "emily":    ("emily",    0.46, 0.62, 0.80),
    # stand-in art until a real photo exists; source is already 3:4 so no crop
    "andy":     ("placeholder", 0.50, 0.50, 1.00),
}

# ---------------------------------------------------------------------------


def load(name):
    path = SRC / f"{name}.jpg"
    if not path.exists():
        sys.exit(f"Missing {path}")
    return ImageOps.exif_transpose(Image.open(path)).convert("RGB")


def crop(im, ratio, cx=0.5, cy=0.5, hf=1.0):
    """Crop to width/height == ratio, keeping hf of the height, centred on (cx, cy)."""
    W, H = im.size
    ch = int(H * hf)
    cw = int(ch * ratio)
    if cw > W:
        cw, ch = W, int(W / ratio)
    x = max(0, min(W - cw, int(W * cx - cw / 2)))
    y = max(0, min(H - ch, int(H * cy - ch / 2)))
    return im.crop((x, y, x + cw, y + ch))


def save(im, base, widths, q=82, jpg=False):
    base.parent.mkdir(parents=True, exist_ok=True)
    for w in widths:
        r = im.copy()
        r.thumbnail((w, 10**6), Image.LANCZOS)
        r.save(f"{base}-{w}.webp", "WEBP", quality=q, method=6)
        if jpg:
            r.convert("RGB").save(f"{base}-{w}.jpg", "JPEG",
                                  quality=q, optimize=True, progressive=True)


def knockout(im, lo=52, hi=104, color=(74, 74, 70), strength=0.85):
    """Drop a flat dark background to transparency, keeping the line art.

    The placeholder art is a light-grey drawing on a dark grey field. Mapping
    luminance to alpha removes the field entirely, so the tile's own background
    shows through and it matches the photo tiles beside it. `color` and
    `strength` keep the line work quiet rather than contrasty.
    """
    grey = im.convert("L")
    alpha = grey.point(lambda v: 0 if v <= lo else
                       int(255 * strength) if v >= hi
                       else int((v - lo) / (hi - lo) * 255 * strength))
    solid = Image.new("RGB", im.size, color)
    r, g, b = solid.split()
    return Image.merge("RGBA", (r, g, b, alpha))


def favicons():
    """Build the tab icons from the logo.

    Just the mark on transparency, no tile and no disc: a solid block reads as a
    blob among other favicons. Two inks, picked by the `media` attribute on the
    link tags, so the mark suits a light or dark tab bar. favicon.ico is the
    fallback for anything that ignores media, hence the dark ink: tab bars are
    light unless the OS is in dark mode.

    The frame is sized from the furthest lit pixel rather than the bounding box,
    because the mark's spokes radiate past its circle.
    """
    import math

    src = Image.open(OUT / "logo-square.jpg").convert("L")   # white mark on black
    lit = src.point(lambda v: 255 if v > 40 else 0)
    bbox = lit.getbbox()
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    px = lit.load()
    maxr = max(math.hypot(x - cx, y - cy)
               for y in range(bbox[1], bbox[3])
               for x in range(bbox[0], bbox[2]) if px[x, y])
    r = maxr * 1.06
    # the logo's own luminance is the coverage mask, so it becomes the alpha
    alpha = src.crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r)))

    def mark(size, rgb):
        a = alpha.resize((size, size), Image.LANCZOS)
        rr, gg, bb = Image.new("RGB", (size, size), rgb).split()
        return Image.merge("RGBA", (rr, gg, bb, a))

    for size in (32, 192):
        mark(size, (17, 17, 17)).save(OUT / f"favicon-light-{size}.png")
        mark(size, (255, 255, 255)).save(OUT / f"favicon-dark-{size}.png")

    mark(256, (17, 17, 17)).save(
        ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])

    # iOS composites the touch icon on white and masks it itself, so it has to
    # be opaque: white mark on the site's own near-black
    white = mark(180, (255, 255, 255))
    ios = Image.new("RGB", (180, 180), (13, 13, 14))
    ios.paste(white.convert("RGB"), (0, 0), white)
    ios.save(OUT / "apple-touch-icon.png")
    print("favicons   <- logo-square.jpg (light + dark marks)")


def main():
    name, cx, cy, hf = HERO
    save(crop(load(name), 4 / 5, cx, cy, hf), OUT / "hero" / "hero", [1400, 900], jpg=True)
    print(f"hero       <- {name}.jpg")

    for slug, (name, cx, cy, hf) in TEAM.items():
        img = crop(load(name), 3 / 4, cx, cy, hf)
        if name == "placeholder":
            img = knockout(img)
        save(img, OUT / "team" / slug, [700])
        print(f"{slug:<10} <- {name}.jpg")

    favicons()

    print("\nDone.")


if __name__ == "__main__":
    main()

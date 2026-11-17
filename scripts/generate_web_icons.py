"""Generate the web app icons (PWA, Apple touch, favicon).

The mark is the same one the download page uses: a rising analytics line
with two data points, in white on the app's accent gradient.

Run from the repository root::

    python scripts/generate_web_icons.py

Outputs into ``mobile/web/``:

    icons/Icon-192.png            rounded, purpose "any"
    icons/Icon-512.png
    icons/Icon-maskable-192.png   full bleed, mark inside the safe zone
    icons/Icon-maskable-512.png
    apple-touch-icon.png          full bleed (iOS applies its own mask)
    favicon.png                   64 px, rounded

Requires Pillow (``pip install pillow``). Icons are drawn at 4x and
downsampled with Lanczos, so edges stay smooth at every size.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "mobile" / "web"

# Accent gradient: the design system's #8B7CFF, deepened for contrast.
START = (155, 140, 255)  # #9B8CFF
MID = (124, 108, 247)    # #7C6CF7
END = (86, 70, 214)      # #5646D6

# The mark, in a 24x24 viewbox (same geometry as the download page logo).
LINE = [(4, 17), (9, 9), (13, 14), (16, 10), (20, 17)]
DOTS = [(9, 9), (16, 10)]

SS = 4  # supersampling factor


def gradient(size: int) -> Image.Image:
    """Diagonal two-stop gradient, built small and resized."""
    seed = Image.new("RGB", (2, 2))
    seed.putpixel((0, 0), START)
    seed.putpixel((1, 0), MID)
    seed.putpixel((0, 1), MID)
    seed.putpixel((1, 1), END)
    return seed.resize((size, size), Image.BICUBIC)


def mark_layer(size: int, ratio: float) -> Image.Image:
    """White chart mark, centered, spanning `ratio` of the canvas."""
    big = size * SS
    layer = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    box = big * ratio
    offset = (big - box) / 2

    def point(x: float, y: float) -> tuple[float, float]:
        return (offset + x / 24 * box, offset + y / 24 * box)

    width = max(2, round(box * 2.4 / 24))
    points = [point(x, y) for x, y in LINE]

    draw.line(points, fill=(255, 255, 255, 255), width=width, joint="curve")

    # Round caps: `joint` rounds the inner corners only.
    for end in (points[0], points[-1]):
        r = width / 2
        draw.ellipse([end[0] - r, end[1] - r, end[0] + r, end[1] + r], fill=(255, 255, 255, 255))

    for x, y in DOTS:
        r = box * 1.9 / 24
        cx, cy = point(x, y)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 255))

    return layer.resize((size, size), Image.LANCZOS)


def rounded_mask(size: int, radius_ratio: float = 0.225) -> Image.Image:
    big = size * SS
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, big - 1, big - 1], radius=round(big * radius_ratio), fill=255
    )
    return mask.resize((size, size), Image.LANCZOS)


def icon(size: int, *, ratio: float, rounded: bool) -> Image.Image:
    base = gradient(size).convert("RGBA")
    base.alpha_composite(mark_layer(size, ratio))
    if rounded:
        base.putalpha(rounded_mask(size))
    return base


def main() -> None:
    icons = WEB / "icons"
    icons.mkdir(parents=True, exist_ok=True)

    outputs = {
        icons / "Icon-192.png": icon(192, ratio=0.62, rounded=True),
        icons / "Icon-512.png": icon(512, ratio=0.62, rounded=True),
        # Maskable: full bleed; the mark stays inside the 80% safe circle.
        icons / "Icon-maskable-192.png": icon(192, ratio=0.46, rounded=False),
        icons / "Icon-maskable-512.png": icon(512, ratio=0.46, rounded=False),
        # iOS applies its own rounded mask, so ship it full bleed.
        WEB / "apple-touch-icon.png": icon(180, ratio=0.58, rounded=False),
        WEB / "favicon.png": icon(64, ratio=0.70, rounded=True),
    }

    for path, image in outputs.items():
        image.save(path, format="PNG", optimize=True)
        print(f"{path.relative_to(ROOT)}  {image.size[0]}x{image.size[1]}  {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()

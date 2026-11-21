"""Turn the AI-generated app icon into the full PWA icon set.

Source: the generated 1024x1024 square (dark navy, shield mark).
Outputs into web/public/ (rounded "any" icons, full-bleed maskable icons,
apple-touch icon) and a small favicon.
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(
    r"C:\Users\User\AppData\Local\Temp\opencode\images"
    r"\ses_e2d59f4e6ffeq3fqrU1ZkKoNwW\image_1fc652671001RGh3q5A47DMDZ3.webp"
)
PUBLIC = ROOT / "web" / "public"

SS = 4  # supersampling for the rounded mask


def rounded_mask(size: int, radius_ratio: float) -> Image.Image:
    big = size * SS
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, big - 1, big - 1], radius=round(big * radius_ratio), fill=255
    )
    return mask.resize((size, size), Image.LANCZOS)


def main() -> None:
    source = Image.open(SRC).convert("RGB").resize((1024, 1024), Image.LANCZOS)
    (PUBLIC / "icons").mkdir(parents=True, exist_ok=True)

    outputs = {
        # "any" purpose: rounded corners like a desktop app tile.
        PUBLIC / "icons" / "icon-192.png": (source.resize((192, 192), Image.LANCZOS), 0.18),
        PUBLIC / "icons" / "icon-512.png": (source.resize((512, 512), Image.LANCZOS), 0.18),
        # Maskable: full bleed - the shield already sits inside the safe zone.
        PUBLIC / "icons" / "icon-maskable-192.png": (source.resize((192, 192), Image.LANCZOS), None),
        PUBLIC / "icons" / "icon-maskable-512.png": (source.resize((512, 512), Image.LANCZOS), None),
        # iOS applies its own mask: full bleed.
        PUBLIC / "apple-touch-icon.png": (source.resize((180, 180), Image.LANCZOS), None),
        PUBLIC / "icons" / "favicon-64.png": (source.resize((64, 64), Image.LANCZOS), 0.22),
    }

    for path, (image, radius_ratio) in outputs.items():
        if radius_ratio is not None:
            image = image.convert("RGBA")
            image.putalpha(rounded_mask(image.size[0], radius_ratio))
            image.save(path, format="PNG", optimize=True)
        else:
            image.save(path, format="PNG", optimize=True)
        print(f"{path.relative_to(ROOT)}  {image.size[0]}x{image.size[1]}")


if __name__ == "__main__":
    main()

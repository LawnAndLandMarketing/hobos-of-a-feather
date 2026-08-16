from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "public" / "images"

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]
font_path = next((p for p in FONT_CANDIDATES if Path(p).exists()), None)


def sign_overlay(source, output, polygon, lines, font_sizes):
    image = Image.open(IMAGES / source).convert("RGB")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    mask = Image.new("L", image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.polygon(polygon, fill=255)

    random.seed(42)
    base = Image.new("RGBA", image.size, (157, 118, 68, 255))
    px = base.load()
    bounds = mask.getbbox()
    if bounds:
        for y in range(bounds[1], bounds[3]):
            for x in range(bounds[0], bounds[2]):
                if mask.getpixel((x, y)):
                    n = random.randint(-10, 10)
                    px[x, y] = (max(0, 157+n), max(0, 118+n), max(0, 68+n), 255)
    overlay = Image.composite(base, overlay, mask)
    draw = ImageDraw.Draw(overlay)

    min_x = min(x for x, _ in polygon)
    max_x = max(x for x, _ in polygon)
    min_y = min(y for _, y in polygon)
    max_y = max(y for _, y in polygon)
    center_x = (min_x + max_x) / 2
    total_h = sum(font_sizes) + (len(lines) - 1) * 4
    y = (min_y + max_y - total_h) / 2

    for line, size in zip(lines, font_sizes):
        font = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=1)
        w = bbox[2] - bbox[0]
        jitter = random.randint(-4, 4)
        draw.text((center_x - w / 2 + jitter, y), line, font=font, fill=(27, 23, 18, 245), stroke_width=1, stroke_fill=(27, 23, 18, 245))
        y += size + 4

    result = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    result.save(IMAGES / output, quality=91, optimize=True, progressive=True)


sign_overlay(
    "hero.jpg",
    "hero-final.jpg",
    [(270, 338), (678, 340), (689, 582), (273, 586)],
    ["WE SAW", "NOTHING"],
    [58, 64],
)

sign_overlay(
    "scene-c.jpg",
    "scene-c-final.jpg",
    [(281, 93), (557, 55), (595, 264), (311, 282)],
    ["ASK ME", "ABOUT", "PRIVACY"],
    [38, 32, 35],
)

print("created hero-final.jpg and scene-c-final.jpg")

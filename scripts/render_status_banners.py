"""Render the static per-status banner images shipped with the Telegram mirror.

These are **static assets**: generated once and committed under
``src/jira_nano/telegram/assets/``; the bot never renders images at runtime, it
just sends the matching PNG as a photo with the ticket details in the caption.

This is a manual developer tool — it needs Pillow (``pip install pillow``) and
the DejaVu fonts (``fonts-dejavu`` on Debian/Ubuntu). Re-run it when the banner
design or the status palette changes:

    python scripts/render_status_banners.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG = (247, 249, 252)
DARK = (24, 27, 34)
OUT = Path(__file__).resolve().parent.parent / "src" / "jira_nano" / "telegram" / "assets"

#: status name -> accent colour (bright palette; matches the workflow circles).
PALETTE = {
    "todo": (234, 179, 8),
    "in-progress": (59, 130, 246),
    "in-review": (168, 85, 247),
    "done": (34, 197, 94),
    "archived": (107, 114, 128),
    "blocked": (239, 68, 68),
}


def render(name: str, color: tuple[int, int, int], path: Path) -> None:
    """Render one flat, wide status banner (pill label + thin bottom accent)."""
    w, h, pad = 1200, 130, 34
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_BOLD, 40)
    text = name.upper().replace("-", " ")
    box = d.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    padx, ph = 30, 66
    y = (h - ph) // 2 - 3
    tcol = DARK if name == "todo" else (255, 255, 255)
    d.rounded_rectangle([pad, y, pad + tw + 2 * padx, y + ph], radius=ph // 2, fill=color)
    d.text((pad + padx, y + (ph - th) // 2 - box[1]), text, font=font, fill=tcol)
    d.rectangle([0, h - 8, w, h], fill=color)  # flat bottom accent bar
    img.save(path, "PNG")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, color in PALETTE.items():
        render(name, color, OUT / f"status_{name}.png")
        print(f"wrote {OUT / f'status_{name}.png'}")


if __name__ == "__main__":
    main()

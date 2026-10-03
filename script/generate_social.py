#!/usr/bin/env python3
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from presentation_data import read_header, read_palette

ROOT = Path(__file__).resolve().parents[1]


def load_font(names, size):
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    raise SystemExit(f"Police introuvable: {', '.join(names)}")


lines = (ROOT / "presentation.md").read_text(encoding="utf-8").splitlines()
title, fields = read_header(ROOT)
palette = read_palette(ROOT)
author_line = fields.get("Auteur", "")
author_match = re.search(r"\[([^]]+)]\([^)]+\)", author_line)
baseline_index = lines.index("## Baseline")
baseline = next(line for line in lines[baseline_index + 1:] if line)
if not author_match:
    raise SystemExit("Le champ Auteur doit être un lien Markdown")

title_lines = title.replace(" ", "\n", 1)
baseline_lines = baseline.replace(" en ", "\nen ", 1)
serif = load_font(("NotoSerif-Regular.ttf", "DejaVuSerif.ttf", "LiberationSerif-Regular.ttf"), 108)
serif_small = load_font(("NotoSerif-Italic.ttf", "DejaVuSerif-Italic.ttf", "LiberationSerif-Italic.ttf"), 42)
sans = load_font(("NotoSans-Regular.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"), 28)
image = Image.new("RGB", (1200, 630), palette["night"])
draw = ImageDraw.Draw(image)
draw.rectangle((88, 82, 96, 548), fill=palette["accent"])
draw.multiline_text(
    (140, 72), title_lines, font=serif,
    fill=palette["paper"], spacing=-14,
)
draw.multiline_text(
    (145, 350), baseline_lines, font=serif_small,
    fill=palette["paper"], spacing=4,
)
draw.text(
    (145, 528), author_match[1].upper(), font=sans,
    fill=palette["highlight"],
)
image.save(ROOT / "web/social-card.png", optimize=True)

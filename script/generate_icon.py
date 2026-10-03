#!/usr/bin/env python3
import html
from pathlib import Path

from presentation_data import read_header, read_palette

ROOT = Path(__file__).resolve().parents[1]
title, fields = read_header(ROOT)
palette = read_palette(ROOT)
if "Ico" not in fields:
    raise SystemExit("Le champ Ico est manquant dans presentation.md")
icon = fields["Ico"]
if not 1 <= len(icon) <= 3:
    raise SystemExit("Le champ Ico doit contenir entre un et trois caractères")
glyphs = html.escape(icon[0])
if icon[1:]:
    glyphs += f'<tspan fill="{palette["highlight"]}">{html.escape(icon[1:])}</tspan>'
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <title>{html.escape(title)}</title>
  <rect width="64" height="64" rx="14" fill="{palette["night"]}"/>
  <text x="32" y="41" text-anchor="middle" fill="{palette["paper"]}" font-family="Georgia,serif" font-size="28" font-weight="600" letter-spacing="-1">{glyphs}</text>
</svg>
'''
(ROOT / "web/favicon.svg").write_text(svg, encoding="utf-8")

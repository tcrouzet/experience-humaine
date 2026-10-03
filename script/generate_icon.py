#!/usr/bin/env python3
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
title = (ROOT / "presentation.md").read_text(encoding="utf-8").splitlines()[0].removeprefix("# ")
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <title>{html.escape(title)}</title>
  <rect width="64" height="64" rx="14" fill="#292d2a"/>
  <path d="M15 14v36m0-36h15M15 32h12M15 50h15" fill="none" stroke="#f3efe7" stroke-width="4"/>
  <path d="M38 14v36M52 14v36M38 32h14" fill="none" stroke="#d18a72" stroke-width="4"/>
</svg>
'''
(ROOT / "web/favicon.svg").write_text(svg, encoding="utf-8")

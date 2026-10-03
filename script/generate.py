#!/usr/bin/env python3
import html
import re
from pathlib import Path

from presentation_data import FIELD, read_header, read_palette

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://tcrouzet.github.io/experience-humaine"
LINK = re.compile(r"\[([^]]+)]\(([^)]+)\)")


def emphasis(text):
    parts = re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text)
    output = []
    for part in parts:
        if part.startswith("**"):
            output.append(f"<strong>{html.escape(part[2:-2])}</strong>")
        elif part.startswith("*"):
            output.append(f"<em>{html.escape(part[1:-1])}</em>")
        else:
            output.append(html.escape(part).replace(r"\n", "<br>"))
    return "".join(output)


def inline(text):
    output, position = [], 0
    for match in LINK.finditer(text):
        output.append(emphasis(text[position:match.start()]))
        output.append(f'<a href="{html.escape(match[2], quote=True)}">{emphasis(match[1])}</a>')
        position = match.end()
    output.append(emphasis(text[position:]))
    return "".join(output)


def paragraphs(lines):
    blocks = "\n".join(lines).strip().split("\n\n")
    return "\n        ".join(f"<p>{inline(block.replace(chr(10), ' '))}</p>" for block in blocks)


lines = (ROOT / "presentation.md").read_text(encoding="utf-8").splitlines()
title, fields = read_header(ROOT)
palette = read_palette(ROOT)
sections, current = {}, None
for line in lines[1:]:
    if line.startswith("## "):
        current = line[3:]
        sections[current] = []
    elif current:
        sections[current].append(line)

required = {"Auteur"}
if missing := required - fields.keys():
    raise SystemExit(f"Champs manquants dans presentation.md: {', '.join(sorted(missing))}")
for heading in ("Baseline", "Citation", "Action", "Copyright"):
    if heading not in sections:
        raise SystemExit(f"Section manquante dans presentation.md: {heading}")


def named_section(name):
    matches = [heading for heading in sections if heading == name or heading.startswith(f"{name} :") or heading.startswith(f"{name}:")]
    if len(matches) != 1:
        raise SystemExit(f"Section manquante ou ambiguë dans presentation.md: {name}")
    heading = matches[0]
    parts = re.split(r"[  ]*:[  ]*", heading, maxsplit=1)
    return heading, parts[0], parts[1] if len(parts) == 2 else ""


def section_header(title):
    if not title:
        return ""
    return f'<header class="section-heading"><h2>{inline(title)}</h2></header>'


author_match = LINK.fullmatch(fields["Auteur"])
if not author_match:
    raise SystemExit("Le champ Auteur doit être un lien Markdown")
author, author_url = author_match.groups()

action = {}
for line in sections["Action"]:
    if not line:
        continue
    match = FIELD.fullmatch(line)
    if not match:
        raise SystemExit(f"Action invalide: {line}")
    action[match[1].strip()] = match[2].strip()
action_match = LINK.fullmatch(action.get("Bouton", ""))
if not action_match:
    raise SystemExit("La section Action doit contenir un Bouton lié")

reference_key, references_heading, references_intro = named_section("Références")
reference_lines = [line for line in sections[reference_key] if line]
references = []
book_pattern = re.compile(r"^\* \[\*(.+)\*]\(([^)]+)\), (.+), (\d{4}), (.+)$")
for line in reference_lines:
    if line.startswith("> "):
        references.append(f'<p class="reference-context">{inline(line[2:])}</p>')
        continue
    if LINK.fullmatch(line):
        references.append(f'<p class="reference-source">{inline(line)}</p>')
        continue
    if not line.startswith("* "):
        references.append(f'<p class="reference-intro">{inline(line)}</p>')
        continue
    match = book_pattern.fullmatch(line)
    if not match:
        raise SystemExit(f"Référence invalide: {line}")
    book, url, writer, year, publisher = match.groups()
    references.append(
        f'<a href="{html.escape(url, quote=True)}"><span class="book-title">{html.escape(book)}</span>'
        f'<span>{html.escape(writer)} · {year} · {html.escape(publisher)}</span></a>'
    )

resonance_key, resonance_heading, kicker = named_section("Argumentaire")
themes = []
for line in (line for line in sections[resonance_key] if line):
    match = FIELD.fullmatch(line)
    if not match:
        raise SystemExit(f"Thème invalide: {line}")
    themes.append(f"<li><span>{html.escape(match[1].strip())}</span> {inline(match[2].strip())}</li>")

baseline = next(line for line in sections["Baseline"] if line)
citation = next(line for line in sections["Citation"] if line)
copyright = next(line for line in sections["Copyright"] if line)
story_key, story_heading, story_title = named_section("Quatrième")
template = (ROOT / "template.html").read_text(encoding="utf-8")
palette_css = ":root {\n" + "\n".join(
    f"  --{name}: {value};" for name, value in palette.items()
) + "\n" + """  --line: color-mix(in srgb, var(--ink) 20%, transparent);
  --night-line: color-mix(in srgb, var(--paper) 22%, transparent);
  --copyright: color-mix(in srgb, var(--paper) 58%, transparent);
  --shadow: color-mix(in srgb, var(--night) 20%, transparent);
}
"""
(ROOT / "web/palette.css").write_text(palette_css, encoding="utf-8")
page = template.format(
    title=html.escape(title),
    title_html=html.escape(title).replace(" ", "<br>", 1),
    description=html.escape(f"{title} de {author} — {baseline}", quote=True),
    author=html.escape(author),
    author_url=html.escape(author_url, quote=True),
    baseline=html.escape(baseline, quote=True),
    social_image=f"{SITE_URL}/social-card.png",
    social_alt=html.escape(f"{title} — {baseline} — {author}", quote=True),
    night=palette["night"],
    baseline_html=inline(baseline).replace(" en ", "<br>en ", 1),
    citation=inline(citation),
    story_header=section_header(story_title),
    story=paragraphs(sections[story_key]),
    references_header=section_header(references_intro),
    references="\n        ".join(references),
    resonance_header=section_header(kicker),
    themes="\n        ".join(themes),
    action=inline(action_match[1]),
    action_url=html.escape(action_match[2], quote=True),
    copyright=inline(copyright),
)
(ROOT / "web/index.html").write_text(page, encoding="utf-8")

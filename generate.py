#!/usr/bin/env python3
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LINK = re.compile(r"\[([^]]+)]\(([^)]+)\)")
FIELD = re.compile(r"^([^: ]+)[  ]*:[  ]*(.+)$")


def emphasis(text):
    parts = re.split(r"(\*[^*]+\*)", text)
    return "".join(
        f"<em>{html.escape(part[1:-1])}</em>" if part.startswith("*") else html.escape(part)
        for part in parts
    )


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
title = lines[0].removeprefix("# ")
sections, fields, current = {}, {}, None
for line in lines[1:]:
    if line.startswith("## "):
        current = line[3:]
        sections[current] = []
    elif current:
        sections[current].append(line)
    elif match := FIELD.match(line):
        fields[match[1].strip()] = match[2].strip()

required = {"Auteur"}
if missing := required - fields.keys():
    raise SystemExit(f"Champs manquants dans presentation.md: {', '.join(sorted(missing))}")
for heading in ("Baseline", "Citation", "Informations"):
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

information = {}
for line in sections["Informations"]:
    if not line:
        continue
    match = FIELD.fullmatch(line)
    if not match:
        raise SystemExit(f"Information invalide: {line}")
    information[match[1].strip()] = match[2].strip()
if missing := {"Auteur", "Contact", "Signes", "Type"} - information.keys():
    raise SystemExit(f"Informations manquantes: {', '.join(sorted(missing))}")
info_author_match = LINK.fullmatch(information["Auteur"])
contact_match = LINK.fullmatch(information["Contact"])
if not info_author_match or not contact_match:
    raise SystemExit("Auteur et Contact doivent être des liens Markdown")

reference_key, references_heading, references_intro = named_section("Références")
reference_lines = [line for line in sections[reference_key] if line]
books = []
book_pattern = re.compile(r"^\* \[\*(.+)\*]\(([^)]+)\), (.+), (\d{4}), (.+)$")
for line in reference_lines:
    match = book_pattern.fullmatch(line)
    if not match:
        raise SystemExit(f"Référence invalide: {line}")
    book, url, writer, year, publisher = match.groups()
    books.append(
        f'<a href="{html.escape(url, quote=True)}"><span class="book-title">{html.escape(book)}</span>'
        f'<span>{html.escape(writer)} · {year} · {html.escape(publisher)}</span></a>'
    )

resonance_key, resonance_heading, kicker = named_section("Argumentaire")
resonance = [line for line in sections[resonance_key] if line]
theme_lines = []
while resonance and not resonance[0].startswith("> "):
    theme_lines.append(resonance.pop(0))
themes = []
for line in theme_lines:
    match = FIELD.fullmatch(line)
    if not match:
        raise SystemExit(f"Thème invalide: {line}")
    themes.append(f"<li><span>{html.escape(match[1].strip())}</span> {inline(match[2].strip())}</li>")

if len(resonance) != 2:
    raise SystemExit("L’argumentaire doit finir par deux liens")
universal_match = LINK.fullmatch(resonance.pop(0).removeprefix("> "))
study_match = LINK.fullmatch(resonance.pop(0))
if not universal_match or not study_match or resonance:
    raise SystemExit("Liens finaux invalides dans la dernière section")

baseline = next(line for line in sections["Baseline"] if line)
citation = next(line for line in sections["Citation"] if line)
story_key, story_heading, story_title = named_section("Quatrième")
template = (ROOT / "template.html").read_text(encoding="utf-8")
page = template.format(
    title=html.escape(title),
    title_html=html.escape(title).replace(" ", "<br>", 1),
    description=html.escape(f"{title}, un {information['Type'].lower()} de {author} sur l’amour, la maladie et le deuil.", quote=True),
    author=html.escape(author),
    author_url=html.escape(author_url, quote=True),
    signs=html.escape(information["Signes"]),
    type=html.escape(information["Type"]),
    baseline=html.escape(baseline, quote=True),
    baseline_html=inline(baseline).replace(" en ", "<br>en ", 1),
    citation=inline(citation),
    story_header=section_header(story_title),
    story=paragraphs(sections[story_key]),
    references_header=section_header(references_intro),
    books="\n        ".join(books),
    resonance_header=section_header(kicker),
    themes="\n        ".join(themes),
    universal=inline(universal_match[1]),
    universal_url=html.escape(universal_match[2], quote=True),
    study=inline(study_match[1]),
    study_url=html.escape(study_match[2], quote=True),
    info_author=emphasis(info_author_match[1]),
    info_author_url=html.escape(info_author_match[2], quote=True),
    contact=emphasis(contact_match[1]),
    contact_url=html.escape(contact_match[2], quote=True),
)
(ROOT / "web/index.html").write_text(page, encoding="utf-8")

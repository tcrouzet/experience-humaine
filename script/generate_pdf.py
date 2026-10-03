#!/usr/bin/env python3
import html
import re
from pathlib import Path

from PIL import ImageFont
from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)
from presentation_data import FIELD, read_header, read_palette

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "presentation.md"
OUTPUT = ROOT / "web/experience-humaine.pdf"
SITE_URL = "https://tcrouzet.github.io/experience-humaine"
LINK = re.compile(r"\[([^]]+)]\(([^)]+)\)")
PALETTE = read_palette(ROOT)
rl_config.invariant = 1


def font_path(*names):
    for name in names:
        try:
            return ImageFont.truetype(name, 12).path
        except OSError:
            continue
    raise SystemExit(f"Police introuvable : {', '.join(names)}")


def register_fonts():
    fonts = {
        "Literary": ("NotoSerif-Regular.ttf", "DejaVuSerif.ttf", "LiberationSerif-Regular.ttf"),
        "Literary-Bold": ("NotoSerif-Bold.ttf", "DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf"),
        "Literary-Italic": ("NotoSerif-Italic.ttf", "DejaVuSerif-Italic.ttf", "LiberationSerif-Italic.ttf"),
        "Sans": ("NotoSans-Regular.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"),
        "Sans-Bold": ("NotoSans-Bold.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"),
    }
    for family, candidates in fonts.items():
        pdfmetrics.registerFont(TTFont(family, font_path(*candidates)))
    pdfmetrics.registerFontFamily(
        "Literary",
        normal="Literary",
        bold="Literary-Bold",
        italic="Literary-Italic",
        boldItalic="Literary-Bold",
    )
    pdfmetrics.registerFontFamily(
        "Sans",
        normal="Sans",
        bold="Sans-Bold",
        italic="Sans",
        boldItalic="Sans-Bold",
    )


def emphasis(text):
    parts = re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text)
    output = []
    for part in parts:
        if part.startswith("**"):
            output.append(f"<b>{html.escape(part[2:-2])}</b>")
        elif part.startswith("*"):
            output.append(f"<i>{html.escape(part[1:-1])}</i>")
        else:
            output.append(html.escape(part).replace(r"\n", "<br/>"))
    return "".join(output)


def link_markup(match, color):
    url = match[2]
    if not url.startswith(("http://", "https://")):
        url = f"{SITE_URL}/{url.lstrip('/')}"
    return (
        f'<link href="{html.escape(url, quote=True)}" color="{color}">'
        f"{emphasis(match[1])}</link>"
    )


def inline(text):
    output, position = [], 0
    for match in LINK.finditer(text):
        output.append(emphasis(text[position:match.start()]))
        output.append(link_markup(match, PALETTE["accent"]))
        position = match.end()
    output.append(emphasis(text[position:]))
    return "".join(output)


def heading_label(heading):
    parts = re.split(r"[  ]*:[  ]*", heading, maxsplit=1)
    return parts[1] if len(parts) == 2 else ""


register_fonts()
lines = SOURCE.read_text(encoding="utf-8").splitlines()
title, fields = read_header(ROOT)
author_line = fields.get("Auteur", "")
author_match = LINK.search(author_line)
if not author_match:
    raise SystemExit("Le champ Auteur doit être un lien Markdown")
author = author_match[1]

sections, current = {}, None
for line in lines[1:]:
    if line.startswith("## "):
        current = line[3:]
        sections[current] = []
    elif current is not None:
        sections[current].append(line)

styles = getSampleStyleSheet()
ink = colors.HexColor(PALETTE["ink"])
muted = colors.HexColor(PALETTE["muted"])
accent = colors.HexColor(PALETTE["accent"])
body = ParagraphStyle(
    "Body", parent=styles["BodyText"], fontName="Literary", fontSize=10.5,
    leading=14, textColor=ink, spaceAfter=6, allowWidows=0, allowOrphans=0,
)
section_title = ParagraphStyle(
    "Section", parent=body, fontSize=20, leading=22, textColor=accent,
    spaceAfter=8, keepWithNext=True,
)
label = ParagraphStyle(
    "Label", parent=body, fontName="Sans-Bold", fontSize=7.5, leading=10,
    textColor=accent, spaceAfter=2, keepWithNext=True,
)
quote = ParagraphStyle(
    "Quote", parent=body, fontName="Literary-Italic", fontSize=11.5, leading=15,
    leftIndent=8, borderColor=accent, borderWidth=0, borderLeftWidth=1.2,
    borderPadding=7, spaceBefore=6, spaceAfter=10,
)
reference = ParagraphStyle(
    "Reference", parent=body, fontSize=9.5, leading=12, leftIndent=5,
    borderColor=muted, borderWidth=0, borderBottomWidth=0.5,
    borderPadding=5, spaceAfter=3,
)
reference_source = ParagraphStyle(
    "ReferenceSource", parent=body, fontName="Sans", fontSize=8.5, leading=11,
    leftIndent=8, rightIndent=8, textColor=muted, spaceBefore=2, spaceAfter=2,
)
pdf_meta_first = ParagraphStyle(
    "PdfMetaFirst", parent=label, alignment=TA_CENTER, fontSize=11, leading=14,
    spaceBefore=10, spaceAfter=2,
)
pdf_meta = ParagraphStyle(
    "PdfMeta", parent=body, fontName="Sans", fontSize=9, leading=13,
    alignment=TA_CENTER, textColor=muted, spaceAfter=2,
)

story = []
story.extend((Spacer(1, 48 * mm), Paragraph(html.escape(title), ParagraphStyle(
    "Title", parent=body, fontSize=42, leading=42, alignment=TA_CENTER, spaceAfter=12,
)), Paragraph(html.escape(author.upper()), ParagraphStyle(
    "Author", parent=label, alignment=TA_CENTER, fontSize=11, leading=15, spaceAfter=20,
))))

baseline = next((line for line in sections.get("Baseline", []) if line), "")
if baseline:
    story.append(Paragraph(inline(baseline), ParagraphStyle(
        "Baseline", parent=quote, alignment=TA_CENTER, leftIndent=0,
        borderLeftWidth=0, fontSize=17, leading=22, spaceAfter=18,
    )))
citation = next((line for line in sections.get("Citation", []) if line), "")
if citation:
    story.append(Paragraph(inline(citation), ParagraphStyle(
        "CoverQuote", parent=quote, fontSize=15, leading=21, leftIndent=12,
        borderLeftWidth=1.5, borderPadding=10, spaceBefore=10, spaceAfter=18,
    )))
pdf_lines = [line for line in sections.get("PDF", []) if line]
if pdf_lines:
    story.append(Paragraph(inline(pdf_lines[0]), pdf_meta_first))
    story.extend(Paragraph(inline(line), pdf_meta) for line in pdf_lines[1:])

story.append(NextPageTemplate("Content"))
first_section = True
for heading, raw_lines in sections.items():
    if heading in {"Baseline", "Citation", "Action", "Copyright", "PDF"}:
        continue
    content = [line for line in raw_lines if line]
    if not content:
        continue
    if first_section:
        story.append(PageBreak())
        first_section = False
    else:
        story.append(Spacer(1, 5 * mm))
    displayed = heading_label(heading)
    if displayed:
        story.append(Paragraph(inline(displayed), section_title))
    for line in content:
        if line.startswith("* "):
            story.append(KeepTogether([Paragraph(f"• {inline(line[2:])}", reference)]))
        elif line.startswith("> "):
            story.append(KeepTogether([Paragraph(inline(line[2:]), quote)]))
        elif (
            heading.startswith(("Références :", "Références:"))
            and (match := LINK.fullmatch(line))
        ):
            story.append(Paragraph(link_markup(match, PALETTE["muted"]), reference_source))
        elif (
            heading.startswith(("Argumentaire :", "Argumentaire:"))
            and not line.startswith("[")
            and (match := FIELD.fullmatch(line))
        ):
            story.append(KeepTogether([
                Paragraph(html.escape(match[1].strip()).upper(), label),
                Paragraph(inline(match[2].strip()), body),
            ]))
        else:
            story.append(Paragraph(inline(line), body))

page_width, page_height = A4
horizontal_margin = 18 * mm
vertical_margin = 16 * mm
gutter = 9 * mm
frame_height = page_height - 2 * vertical_margin
column_width = (page_width - 2 * horizontal_margin - gutter) / 2
frame_options = {
    "leftPadding": 0,
    "rightPadding": 0,
    "topPadding": 0,
    "bottomPadding": 0,
}
cover_frame = Frame(
    horizontal_margin,
    vertical_margin,
    page_width - 2 * horizontal_margin,
    frame_height,
    id="cover",
    **frame_options,
)
left_frame = Frame(
    horizontal_margin,
    vertical_margin,
    column_width,
    frame_height,
    id="left",
    **frame_options,
)
right_frame = Frame(
    horizontal_margin + column_width + gutter,
    vertical_margin,
    column_width,
    frame_height,
    id="right",
    **frame_options,
)
document = BaseDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    title=title,
    author=author,
)
document.addPageTemplates([
    PageTemplate(id="Cover", frames=[cover_frame]),
    PageTemplate(id="Content", frames=[left_frame, right_frame]),
])
document.build(story)

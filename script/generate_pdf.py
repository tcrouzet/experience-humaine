#!/usr/bin/env python3
import html
import re
from io import BytesIO
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
    FrameBreak,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
)
from presentation_data import FIELD, read_header, read_palette

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "presentation.md"
OUTPUT = ROOT / "web/experience-humaine.pdf"
SITE_URL = "https://tcrouzet.github.io/experience-humaine"
LINK = re.compile(r"\[([^]]+)]\(([^)]+)\)")
EMAIL = re.compile(r"(?<![\w@.])([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})(?![\w@.])")
BOOK = re.compile(r"^\[\*(.+)\*](?:\(([^)]+)\))?, (.+), (\d{4}), (.+)$")
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
    content = emphasis(match[1])
    if match[1] == "Source":
        color = PALETTE["muted"]
        content = f'<font name="Sans" size="{reference_source.fontSize:.2f}">{content}</font>'
    return (
        f'<link href="{html.escape(url, quote=True)}" color="{color}">'
        f"{content}</link>"
    )


def inline(text):
    output, position = [], 0
    for match in LINK.finditer(text):
        output.append(emphasis(text[position:match.start()]))
        output.append(link_markup(match, PALETTE["accent"]))
        position = match.end()
    output.append(emphasis(text[position:]))
    return "".join(output)


def pdf_inline(text):
    output, position = [], 0
    for match in EMAIL.finditer(text):
        output.append(inline(text[position:match.start()]))
        address = html.escape(match[1])
        output.append(
            f'<link href="mailto:{address}" color="{PALETTE["muted"]}">{address}</link>'
        )
        position = match.end()
    output.append(inline(text[position:]))
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
author_url = author_match[2]

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
    "Body", parent=styles["BodyText"], fontName="Literary", fontSize=9.5,
    leading=12, textColor=ink, spaceAfter=4.5, allowWidows=0, allowOrphans=0,
)
section_title = ParagraphStyle(
    "Section", parent=body, fontSize=18, leading=19, textColor=accent,
    spaceAfter=6, keepWithNext=True,
)
label = ParagraphStyle(
    "Label", parent=body, fontName="Sans-Bold", fontSize=7, leading=8.5,
    textColor=accent, spaceAfter=1.5, keepWithNext=True,
)
quote = ParagraphStyle(
    "Quote", parent=body, fontName="Literary-Italic", fontSize=10.2, leading=12.7,
    leftIndent=6, borderColor=accent, borderWidth=0, borderLeftWidth=1,
    borderPadding=5, spaceBefore=4, spaceAfter=7,
)
reference = ParagraphStyle(
    "Reference", parent=body, fontSize=8.3, leading=10, leftIndent=3,
    borderColor=muted, borderWidth=0, borderBottomWidth=0.5,
    borderPadding=3, spaceAfter=2.5,
)
reference_source = ParagraphStyle(
    "ReferenceSource", parent=body, fontName="Sans", fontSize=7, leading=8.5,
    leftIndent=6, rightIndent=6, textColor=muted, spaceBefore=1, spaceAfter=1,
)
title_style = ParagraphStyle(
    "Title", parent=body, fontSize=30, leading=37, alignment=TA_CENTER,
    spaceAfter=3,
)
author_style = ParagraphStyle(
    "Author", parent=label, alignment=TA_CENTER, fontSize=8.5, leading=10,
    spaceAfter=4,
)
baseline_style = ParagraphStyle(
    "Baseline", parent=body, fontName="Literary-Italic", fontSize=11.5,
    leading=13, alignment=TA_CENTER, spaceAfter=3,
)
pdf_meta = ParagraphStyle(
    "PdfMeta", parent=body, fontName="Sans", fontSize=7.5, leading=9,
    alignment=TA_CENTER, textColor=muted, spaceAfter=0,
)

scalable_styles = [
    (body, ("fontSize", "leading", "spaceAfter")),
    (section_title, ("fontSize", "leading", "spaceAfter")),
    (label, ("fontSize", "leading", "spaceAfter")),
    (quote, ("fontSize", "leading", "leftIndent", "borderPadding", "spaceBefore", "spaceAfter")),
    (reference, ("fontSize", "leading", "leftIndent", "borderPadding", "spaceAfter")),
    (reference_source, ("fontSize", "leading", "leftIndent", "rightIndent", "spaceBefore", "spaceAfter")),
    (title_style, ("fontSize", "leading", "spaceAfter")),
    (author_style, ("fontSize", "leading", "spaceAfter")),
    (baseline_style, ("fontSize", "leading", "spaceAfter")),
    (pdf_meta, ("fontSize", "leading", "spaceAfter")),
]
base_dimensions = {
    (style.name, attribute): getattr(style, attribute)
    for style, attributes in scalable_styles
    for attribute in attributes
}


def resize_styles(scale):
    for style, attributes in scalable_styles:
        for attribute in attributes:
            setattr(style, attribute, base_dimensions[(style.name, attribute)] * scale)


def make_story(scale, header_width):
    resize_styles(scale)
    header = [
        Paragraph(html.escape(title), title_style),
        Paragraph(
            f'<link href="{html.escape(author_url, quote=True)}" color="{PALETTE["accent"]}">'
            f"{html.escape(author.upper())}</link>",
            author_style,
        ),
    ]
    baseline = next((line for line in sections.get("Baseline", []) if line), "")
    if baseline:
        header.append(Paragraph(inline(baseline), baseline_style))
    pdf_lines = [line for line in sections.get("PDF", []) if line]
    if pdf_lines:
        header.append(Paragraph(" · ".join(pdf_inline(line) for line in pdf_lines), pdf_meta))
    citation = next((line for line in sections.get("Citation", []) if line), "")
    if citation:
        header.append(Paragraph(inline(citation), quote))
    header_table = Table(
        [[header]],
        colWidths=[header_width],
        style=[
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ],
    )
    _, header_height = header_table.wrap(header_width, A4[1])
    story = [header_table, FrameBreak()]

    first_section = True
    for heading, raw_lines in sections.items():
        if heading in {"Baseline", "Citation", "Action", "Copyright", "PDF"}:
            continue
        content = [line for line in raw_lines if line]
        if not content:
            continue
        if first_section:
            first_section = False
        else:
            story.append(Spacer(1, 2.5 * mm * scale))
        displayed = heading_label(heading)
        if displayed:
            story.append(Paragraph(inline(displayed), section_title))
        for line in content:
            if line.startswith("* "):
                match = BOOK.fullmatch(line[2:])
                if not match:
                    raise SystemExit(f"Référence invalide: {line}")
                book, url, writer, year, publisher = match.groups()
                title_markup = f"<i>{html.escape(book)}</i>"
                if url:
                    title_markup = (
                        f'<link href="{html.escape(url, quote=True)}" color="{PALETTE["accent"]}">'
                        f"{title_markup}</link>"
                    )
                text = f"• {title_markup}, {html.escape(writer)}, {year}, {html.escape(publisher)}"
                story.append(Paragraph(text, reference))
            elif line.startswith("> "):
                story.append(Paragraph(inline(line[2:]), quote))
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
    return story, header_height


def render_pdf(target, scale):
    page_width, page_height = A4
    horizontal_margin = 13 * mm
    top_margin = 10 * mm
    bottom_margin = 10 * mm
    header_gap = 8 * mm
    gutter = 7 * mm
    header_width = page_width - 2 * horizontal_margin
    story, header_height = make_story(scale, header_width)
    header_height += 1
    content_top = page_height - top_margin - header_height - header_gap
    frame_height = content_top - bottom_margin
    if frame_height <= 0:
        return 2
    column_width = (page_width - 2 * horizontal_margin - gutter) / 2
    frame_options = {
        "leftPadding": 0,
        "rightPadding": 0,
        "topPadding": 0,
        "bottomPadding": 0,
    }
    frames = [
        Frame(
            horizontal_margin,
            page_height - top_margin - header_height,
            header_width,
            header_height,
            id="header",
            **frame_options,
        ),
        Frame(
            horizontal_margin,
            bottom_margin,
            column_width,
            frame_height,
            id="left",
            **frame_options,
        ),
        Frame(
            horizontal_margin + column_width + gutter,
            bottom_margin,
            column_width,
            frame_height,
            id="right",
            **frame_options,
        ),
    ]
    document = BaseDocTemplate(target, pagesize=A4, title=title, author=author)
    document.addPageTemplates([PageTemplate(id="Presentation", frames=frames)])
    document.build(story)
    return document.page


def fitted_scale():
    minimum, maximum = 0.6, 2.0
    if render_pdf(BytesIO(), minimum) != 1:
        raise SystemExit("Le contenu est trop long pour tenir sur une page")
    for _ in range(12):
        scale = (minimum + maximum) / 2
        if render_pdf(BytesIO(), scale) == 1:
            minimum = scale
        else:
            maximum = scale
    return int(minimum * 1000) / 1000


scale = fitted_scale()
if render_pdf(str(OUTPUT), scale) != 1:
    raise SystemExit("Impossible de générer le PDF sur une page")

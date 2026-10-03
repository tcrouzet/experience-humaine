import re

FIELD = re.compile(r"^([^: ]+)[  ]*:[  ]*(.+)$")
PALETTE_FIELDS = {
    "paper": "Papier",
    "ink": "Encre",
    "muted": "Atténué",
    "accent": "Accent",
    "highlight": "Exergue",
    "night": "Nuit",
}


def read_header(root):
    lines = (root / "presentation.md").read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ")
    fields = {}
    for line in lines[1:]:
        if line.startswith("## "):
            break
        if match := FIELD.fullmatch(line):
            fields[match[1].strip()] = match[2].strip()
    return title, fields


def read_palette(root):
    _, fields = read_header(root)
    missing = [field for field in PALETTE_FIELDS.values() if field not in fields]
    if missing:
        raise SystemExit(f"Couleurs manquantes dans presentation.md: {', '.join(missing)}")
    palette = {name: fields[field] for name, field in PALETTE_FIELDS.items()}
    for field, value in palette.items():
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise SystemExit(f"Couleur invalide pour {PALETTE_FIELDS[field]}: {value}")
    return palette

"""Toolkit card and repo cards in the same night-glass style."""
import base64
import random
import textwrap

from data import fetch_text
from theme import AMBER, FONT, INK, MONO, SUB, esc, glass_panel, sky_defs, stars, svg_doc

LANG_COLORS = {"Python": "#3572A5", "HTML": "#e34c26", "Jupyter Notebook": "#DA5B0B",
               "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Java": "#b07219",
               "C++": "#f34b7d", "PHP": "#4F5D95", "CSS": "#663399"}
ICON_URL = "https://skillicons.dev/icons?i={ids}&theme=dark"
ICON_H = 40


def _night(w, h, seed):
    rng = random.Random(seed)
    return (f'<rect width="{w}" height="{h}" fill="url(#sky)"/>'
            f'<ellipse cx="{w*0.7}" cy="{h}" rx="{w*0.6}" ry="{h*0.7}" fill="url(#glow)"/>'
            + stars(rng, w, 8, h - 8, max(12, w // 30)))


def _icon_row(ids, x, y):
    svg = fetch_text(ICON_URL.format(ids=",".join(ids)))
    if not svg:
        chips = "  ·  ".join(ids)
        return f'<text x="{x}" y="{y+26}" font-family="{MONO}" font-size="14" fill="{INK}">{esc(chips)}</text>'
    width = ICON_H * (len(ids) * 300 - 44) / 256
    b64 = base64.b64encode(svg.encode()).decode()
    return (f'<image x="{x}" y="{y}" width="{width:.1f}" height="{ICON_H}" '
            f'href="data:image/svg+xml;base64,{b64}"/>')


def build_skills(groups, note, seed):
    w, cols, cell_w, cell_h, top = 1200, 3, 372, 104, 92
    rows = -(-(len(groups) + 1) // cols)
    h = top + rows * cell_h + 26
    cells = []
    for i, (label, ids) in enumerate(list(groups.items())):
        x, y = 30 + (i % cols) * (cell_w + 12), top + (i // cols) * cell_h
        cells.append(glass_panel(x, y, cell_w, cell_h - 12, 20)
                     + f'<text x="{x+20}" y="{y+28}" font-family="{MONO}" font-size="12" '
                       f'font-weight="700" letter-spacing="2.5" fill="{AMBER}">{esc(label.upper())}</text>'
                     + _icon_row(ids, x + 20, y + 40))
    i = len(groups)
    x, y = 30 + (i % cols) * (cell_w + 12), top + (i // cols) * cell_h
    cells.append(glass_panel(x, y, cell_w, cell_h - 12, 20)
                 + f'<text x="{x+20}" y="{y+28}" font-family="{MONO}" font-size="12" font-weight="700" '
                   f'letter-spacing="2.5" fill="{AMBER}">RIGHT NOW</text>'
                 + f'<text x="{x+20}" y="{y+62}" font-family="{FONT}" font-size="17" font-weight="600" '
                   f'fill="{INK}">{esc(note)}</text>')
    head = (f'<text x="40" y="52" font-family="{FONT}" font-size="28" font-weight="800" '
            f'letter-spacing="-.5" fill="{INK}">Toolkit</text>'
            f'<text x="148" y="52" font-family="{FONT}" font-size="15" fill="{SUB}">'
            f'what the city is built with</text>')
    return svg_doc(w, h, _night(w, h, seed) + head + "".join(cells), "", sky_defs(h, h * 0.92), "Toolkit")


def build_repo(repo, seed):
    w, h = 590, 176
    lines = textwrap.wrap(repo.description or "No description yet.", 62)[:2]
    if len(textwrap.wrap(repo.description or "", 62)) > 2:
        lines[-1] = lines[-1].rstrip(".,; ") + "…"
    desc = "".join(f'<text x="30" y="{88+i*22}" font-family="{FONT}" font-size="15" fill="{SUB}">'
                   f'{esc(t)}</text>' for i, t in enumerate(lines))
    color = LANG_COLORS.get(repo.language, "#8b949e")
    lang = (f'<circle cx="36" cy="146" r="6" fill="{color}"/><text x="50" y="151" font-family="{FONT}" '
            f'font-size="14" fill="{INK}">{esc(repo.language or "Code")}</text>')
    meta = (f'<text x="{60+len(repo.language or "Code")*8.2:.0f}" y="151" font-family="{FONT}" font-size="14" '
            f'fill="{SUB}">★ {repo.stars}   ⑂ {repo.forks}</text>')
    book = ('<path d="M30 34h10a4 4 0 0 1 4 4v18a3 3 0 0 0-3-3H30zM58 34H48a4 4 0 0 0-4 4v18a3 3 0 0 1 3-3h11z" '
            f'fill="none" stroke="{AMBER}" stroke-width="2" stroke-linejoin="round"/>')
    body = (_night(w, h, seed) + glass_panel(10, 10, w - 20, h - 20, 26) + book
            + f'<text x="70" y="52" font-family="{FONT}" font-size="21" font-weight="700" fill="{INK}">'
              f'{esc(repo.name)}</text>' + desc + lang + meta
            + f'<text x="{w-34}" y="151" text-anchor="end" font-family="{FONT}" font-size="14" '
              f'font-weight="600" fill="{AMBER}">Open ›</text>')
    return svg_doc(w, h, body, "", sky_defs(h, h * 0.95), repo.name)

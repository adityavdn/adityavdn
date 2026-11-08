"""Toolkit and pinned-repo cards that share one Death Star backdrop.

The toolkit frames the whole station on the left; every repo card frames it large
on the right, so any newly pinned repo gets the same backdrop automatically.
"""
import re
import textwrap

import numpy as np
from PIL import Image, ImageEnhance

from scene import to_data_uri
from theme import DISPLAY, INK, MUTED, ROOT, SANS, esc, svg_doc

W = 1200
TOOLKIT_H = 340
CARD_W, CARD_H = 590, 190
CARD_RADIUS = 22
SRC = ROOT / "assets" / "deathstar.jpg"
ICON_DIR = ROOT / "assets" / "icons"
FONTS = (("Inter", 400), ("Inter", 600), ("Inter", 800), ("Orbitron", 700))
CYAN = "#6fd6ff"
HUD_CSS = (".blink{animation:tw 1.6s steps(2,jump-none) infinite}"
           ".scan{animation:scan 9s linear infinite}@keyframes scan{from{transform:translateY(-40px)}to{transform:translateY(400px)}}")
SCAN_DEFS = ('<pattern id="lines" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" '
             'fill="#fff" opacity=".035"/></pattern><linearGradient id="scanfill" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0" stop-color="#6fd6ff" stop-opacity="0"/><stop offset="1" stop-color="#6fd6ff" '
             'stop-opacity=".12"/></linearGradient>')


def _brackets(x, y, w, h, n=14):
    p = (f"M{x} {y+n}V{y}H{x+n} M{x+w-n} {y}H{x+w}V{y+n} M{x+w} {y+h-n}V{y+h}H{x+w-n} "
         f"M{x+n} {y+h}H{x}V{y+h-n}")
    return f'<path d="{p}" fill="none" stroke="{CYAN}" stroke-opacity=".7" stroke-width="1.5"/>'


def _insignia(cx, cy, r):
    """Generic squadron mark: hexagon ring with six spokes."""
    import math
    hexp = " ".join(f"{cx+r*math.cos(math.radians(a)):.1f},{cy+r*math.sin(math.radians(a)):.1f}" for a in range(30, 390, 60))
    spokes = "".join(f'M{cx+r*.42*math.cos(math.radians(a)):.1f} {cy+r*.42*math.sin(math.radians(a)):.1f}L{cx+r*.82*math.cos(math.radians(a)):.1f} {cy+r*.82*math.sin(math.radians(a)):.1f}' for a in range(0, 360, 60))
    return (f'<g fill="none" stroke="{CYAN}" stroke-opacity=".8" stroke-width="1.4"><polygon points="{hexp}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r*.32:.1f}"/><path d="{spokes}"/></g>')


ART_SCALE, ART_X, ART_Y = .48, 70, -10   # puts the whole sphere inside the toolkit band


def _fade_mask(w, h, ramp):
    m = np.ones((h, w), np.float32)
    m[-ramp:] *= np.linspace(1, 0, ramp)[:, None]
    m[:, -ramp:] *= np.linspace(1, 0, ramp)[None, :]
    m[:, :ramp] *= np.linspace(0, 1, ramp)[None, :]
    return Image.fromarray((m * 255).astype(np.uint8), "L")


def canvas():
    total_h = TOOLKIT_H
    src = Image.open(SRC).convert("RGB")
    size = (round(src.width * ART_SCALE), round(src.height * ART_SCALE))
    art = src.resize(size, Image.LANCZOS)
    tile = src.crop((1100, 0, src.width, src.height)).resize(
        (round((src.width - 1100) * ART_SCALE), size[1]), Image.LANCZOS)
    out = Image.new("RGB", (W, total_h), (0, 0, 0))
    for y in range(0, total_h, tile.height):
        for x in range(0, W, tile.width):
            flip = (y // tile.height + x // tile.width) % 2
            out.paste(tile.transpose(Image.FLIP_TOP_BOTTOM) if flip else tile, (x, y))
    out.paste(art, (ART_X, ART_Y), _fade_mask(*size, 90))
    return out


SPHERE = (560, 415)        # station centre in the source image


def repo_backdrop(w, h, scale=.5):
    src = Image.open(SRC).convert("RGB")
    size = (round(src.width * scale), round(src.height * scale))
    art = src.resize(size, Image.LANCZOS)
    tile = src.crop((1100, 0, src.width, src.height)).resize(
        (round((src.width - 1100) * scale), size[1]), Image.LANCZOS)
    out = Image.new("RGB", (w, h), (0, 0, 0))
    for x in range(0, w, tile.width):
        out.paste(tile, (x, 0))
    ox = round(w - 130 - SPHERE[0] * scale)
    oy = round(h / 2 - SPHERE[1] * scale)
    out.paste(art, (ox, oy), _fade_mask(*size, 120))
    return out


def _slice(img, rect, dim):
    x, y, w, h = rect
    piece = img.crop((x, y, x + w, y + h))
    return to_data_uri(ImageEnhance.Brightness(piece).enhance(dim), "JPEG", 84)


def _icon(slug, x, y, size, color="#e9edf6"):
    path = ICON_DIR / f"{slug}.svg"
    if not path.exists():
        return f'<circle cx="{x+size/2}" cy="{y+size/2}" r="{size/5}" fill="{color}"/>'
    d = re.search(r'<path d="([^"]+)"', path.read_text())
    if not d:
        return ""
    return f'<path transform="translate({x} {y}) scale({size/24:.4f})" d="{d.group(1)}" fill="{color}"/>'


def build_toolkit(groups, art):
    bg = _slice(art, (0, 0, W, TOOLKIT_H), .95)
    x0, label_w, cell_w, row_h, top = 548, 104, 74, 45, 104
    rows = []
    for r, (label, items) in enumerate(groups.items()):
        y = top + r * row_h
        rows.append(f'<text x="{x0}" y="{y+16}" font-family="{SANS}" font-size="11" font-weight="600" '
                    f'letter-spacing="1.6" fill="{MUTED}">{esc(label.upper())}</text>')
        for c, (name, slug) in enumerate(items):
            cx = x0 + label_w + c * cell_w + cell_w / 2
            rows.append(_icon(slug, cx - 10, y, 20)
                        + f'<text x="{cx}" y="{y+37}" text-anchor="middle" font-family="{SANS}" '
                          f'font-size="10.5" fill="#c3cad9">{esc(name)}</text>')
    head = (f'<text x="{x0}" y="38" font-family="{SANS}" font-size="11" font-weight="600" letter-spacing="2.4" '
            f'fill="{CYAN}">SYSTEM LOADOUT · CONSOLE 07</text>'
            f'<circle class="blink" cx="{W-150}" cy="34" r="4" fill="#3ddc84"/><text x="{W-40}" y="38" text-anchor="end" '
            f'font-family="{SANS}" font-size="11" font-weight="600" letter-spacing="2" fill="#3ddc84">ARMED</text>'
            f'<text x="{x0}" y="70" font-family="{DISPLAY}" font-size="27" font-weight="700" letter-spacing="2" '
            f'fill="{INK}">STACK</text><text x="{x0+140}" y="70" font-family="{SANS}" font-size="14" '
            f'fill="{MUTED}">languages, frameworks and tools I ship with</text>'
            f'<rect x="{x0}" y="84" width="{W-x0-40}" height="1" fill="{CYAN}" opacity=".3"/>')
    body = (f'<image href="{bg}" width="{W}" height="{TOOLKIT_H}"/>'
            '<rect width="1200" height="340" fill="url(#rfade)"/><rect width="1200" height="340" fill="url(#lines)"/>'
            + _brackets(12, 12, W - 24, TOOLKIT_H - 24) + head + "".join(rows)
            + f'<rect class="scan" x="{x0-20}" y="0" width="{W-x0}" height="40" fill="url(#scanfill)"/>')
    fade = ('<linearGradient id="rfade" x1="0" y1="0" x2="1" y2="0"><stop offset=".38" stop-color="#000" '
            'stop-opacity="0"/><stop offset=".6" stop-color="#000" stop-opacity=".55"/></linearGradient>')
    return svg_doc(W, TOOLKIT_H, body, HUD_CSS, fade + SCAN_DEFS, "Stack", FONTS, CARD_RADIUS)


def build_repo(repo, index, bg_img):
    w, h = bg_img.size
    bg = _slice(bg_img, (0, 0, w, h), .8)
    lines = textwrap.wrap(repo.description or "Briefing classified. Open the file to read the full mission log.", 66)
    if len(lines) > 2:
        lines = lines[:2]
        lines[-1] = lines[-1].rstrip(".,;: ") + "…"
    desc = "".join(f'<text x="30" y="{106+i*21}" font-family="{SANS}" font-size="14.5" fill="#bcc4d6">'
                   f'{esc(t)}</text>' for i, t in enumerate(lines))
    lang = repo.language or "Code"
    color = repo.color or "#8b949e"
    stats_x = 54 + len(lang) * 7.6
    name_size = min(23, (w - 130) / (len(repo.name) * .6))
    body = (f'<image href="{bg}" width="{w}" height="{h}"/>'
            f'<rect width="{w}" height="{h}" fill="url(#cfade)"/>'
            f'<rect width="{w}" height="{h}" fill="url(#lines)"/>' + _brackets(10, 10, w - 20, h - 20, 12)
            + _insignia(42, 38, 11)
            + f'<text x="62" y="42" font-family="{SANS}" font-size="11.5" font-weight="600" letter-spacing="2.2" '
            f'fill="{CYAN}">MISSION FILE {index:02d}  ·  ACTIVE</text>'
            f'<text x="30" y="76" font-family="{SANS}" font-size="{name_size:.1f}" font-weight="800" letter-spacing="-.4" '
            f'fill="{INK}">{esc(repo.name)}</text>{desc}'
            f'<circle cx="36" cy="161" r="9" fill="{color}" opacity=".25" class="blink"/><circle cx="36" cy="161" r="5" fill="{color}"/><text x="48" y="166" font-family="{SANS}" '
            f'font-size="13.5" fill="#dde3ee">{esc(lang)}</text>'
            f'<text x="{stats_x:.0f}" y="166" font-family="{SANS}" font-size="13.5" fill="{MUTED}">'
            f'★ {repo.stars}    ⑂ {repo.forks}</text>'
            f'<circle cx="{w-46}" cy="{h-38}" r="17" fill="#000" fill-opacity=".35" stroke="#fff" stroke-opacity=".3"/>'
            f'<path d="M{w-52} {h-32}l12-12M{w-49} {h-44}h9v9" fill="none" stroke="{INK}" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')
    fade = ('<linearGradient id="cfade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000" '
            'stop-opacity=".8"/><stop offset=".55" stop-color="#000" stop-opacity=".35"/>'
            '<stop offset=".85" stop-color="#000" stop-opacity="0"/></linearGradient>')
    return svg_doc(w, h, body, HUD_CSS, fade + SCAN_DEFS, repo.name, FONTS, CARD_RADIUS)


def build_section(groups, repos):
    """Return {filename: svg} for the toolkit and every repo card."""
    files = {"skills.svg": build_toolkit(groups, canvas())}
    card_bg = repo_backdrop(CARD_W, CARD_H)
    for i, repo in enumerate(repos, start=1):
        files[f"repo-{repo.name}.svg"] = build_repo(repo, i, card_bg)
    return files

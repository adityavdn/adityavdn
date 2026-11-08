"""Hero banner: the ship in hyperspace, live star streaks, the name arriving out of the jump."""
import math
import random

from PIL import Image

from scene import to_data_uri
from theme import DISPLAY, ROOT, SANS, esc, svg_doc

W, H = 1200, 600
SRC = ROOT / "assets" / "falcon.jpg"
VP = (294, 170)               # vanishing point of the star streaks in card units
SHIP = (800, 330, 445, 250, -24)   # ellipse covering the ship: cx, cy, rx, ry, rotation
YELLOW = "#ffe81f"
FONTS = (("Inter", 400), ("Inter", 600), ("Orbitron", 900))

CSS = f"""
.push{{transform-origin:{VP[0]}px {VP[1]}px;animation:push 16s ease-in-out infinite alternate}}
@keyframes push{{from{{transform:scale(1)}}to{{transform:scale(1.07)}}}}
.st{{animation-name:jump;animation-timing-function:cubic-bezier(.55,0,1,.45);animation-iteration-count:infinite}}
@keyframes jump{{from{{stroke-dashoffset:0}}to{{stroke-dashoffset:-1100}}}}
.engine{{animation:engine 2.8s ease-in-out infinite}}
@keyframes engine{{0%,100%{{opacity:.25}}50%{{opacity:.6}}}}
.arrive{{animation:arrive 1.8s cubic-bezier(.16,1,.3,1) both}}
@keyframes arrive{{from{{opacity:0;letter-spacing:22px}}to{{opacity:1;letter-spacing:3px}}}}
.rise{{animation:rise 1.4s cubic-bezier(.16,1,.3,1) both}}
@keyframes rise{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:none}}}}
"""


def background():
    with Image.open(SRC) as im:
        img = im.convert("RGB").resize((W, round(W * im.height / im.width)), Image.LANCZOS)
    top = 40
    return to_data_uri(img.crop((0, top, W, top + H)), "JPEG", 82)


def streaks(rng, n=150):
    out = []
    for _ in range(n):
        a = rng.uniform(0, math.tau)
        x2, y2 = VP[0] + math.cos(a) * 1100, VP[1] + math.sin(a) * 1100
        seg = rng.uniform(25, 140)
        dur = rng.uniform(1.1, 2.6)
        color = rng.choice(("#ffffff", "#ffffff", "#cfe2ff", "#9cc4ff", "#ffe2b8"))
        out.append(f'<path class="st" d="M{VP[0]} {VP[1]}L{x2:.0f} {y2:.0f}" stroke="{color}" '
                   f'stroke-width="{rng.choice((1, 1.2, 1.6, 2))}" stroke-linecap="round" '
                   f'stroke-dasharray="{seg:.0f} 2400" style="animation-duration:{dur:.2f}s;'
                   f'animation-delay:-{rng.uniform(0, dur):.2f}s"/>')
    return "".join(out)


def defs():
    cx, cy, rx, ry, rot = SHIP
    return ('<radialGradient id="vpfade" cx="{0}" cy="{1}" r="620" gradientUnits="userSpaceOnUse">'
            '<stop offset="0" stop-color="#000"/><stop offset=".12" stop-color="#666"/>'
            '<stop offset=".4" stop-color="#fff"/></radialGradient>'.format(*VP)
            + f'<mask id="streakmask" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
              f'<rect width="{W}" height="{H}" fill="url(#vpfade)"/>'
              f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" transform="rotate({rot} {cx} {cy})" fill="#000"/></mask>'
            + '<linearGradient id="scrimL" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000" '
              'stop-opacity=".82"/><stop offset=".5" stop-color="#000" stop-opacity=".25"/>'
              '<stop offset=".7" stop-color="#000" stop-opacity="0"/></linearGradient>'
            + '<linearGradient id="scrimB" x1="0" y1="0" x2="0" y2="1"><stop offset=".5" stop-color="#000" '
              'stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".75"/></linearGradient>'
            + '<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="7"/></filter>'
            + '<filter id="yglow" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur in="SourceAlpha" '
              'stdDeviation="9" result="b"/><feFlood flood-color="#ffb800" flood-opacity=".35"/>'
              '<feComposite in2="b" operator="in"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>')


def headline(name, role, tagline):
    first, _, last = name.upper().rpartition(" ")
    x = 58
    return (f'<text class="rise" x="{x}" y="356" font-family="{SANS}" font-size="13" font-weight="600" '
            f'letter-spacing="3.2" fill="#9cc4ff">A LONG TIME AGO, IN A REPO FAR, FAR AWAY…</text>'
            f'<g filter="url(#yglow)"><text class="arrive" x="{x}" y="420" font-family="{DISPLAY}" '
            f'font-size="50" font-weight="900" fill="{YELLOW}">{esc(first)}</text>'
            f'<text class="arrive" style="animation-delay:.15s" x="{x}" y="478" font-family="{DISPLAY}" '
            f'font-size="50" font-weight="900" fill="{YELLOW}">{esc(last)}</text></g>'
            f'<g class="rise" style="animation-delay:.5s"><text x="{x+2}" y="518" font-family="{SANS}" '
            f'font-size="19" fill="#e2e8f5">{esc(role)}</text>'
            f'<circle cx="{x+7}" cy="549" r="4" fill="#34d27b"/><text x="{x+20}" y="554" font-family="{SANS}" '
            f'font-size="14.5" font-weight="600" fill="#b9c4dc">{esc(tagline)}</text></g>')


def build_hero(name, role, tagline, seed):
    rng = random.Random(seed)
    body = (f'<rect width="{W}" height="{H}" fill="#000"/>'
            f'<g class="push"><image href="{background()}" width="{W}" height="{H}"/>'
            f'<g mask="url(#streakmask)" opacity=".85">{streaks(rng)}</g></g>'
            f'<path class="engine" d="M560 600Q1060 520 1185 112" fill="none" stroke="#5fb4ff" '
            f'stroke-width="22" filter="url(#soft)"/>'
            f'<rect width="{W}" height="{H}" fill="url(#scrimL)"/><rect width="{W}" height="{H}" fill="url(#scrimB)"/>'
            + headline(name, role, tagline))
    return svg_doc(W, H, body, CSS, defs(), f"{name}: hyperspace banner", FONTS)

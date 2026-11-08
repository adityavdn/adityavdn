"""Contribution city: an orbital platform in deep space, one Imperial tower per active day.

Towers rise in a ripple that spreads from a random point each day, then the whole
platform sways gently like the surface of water. A Star Destroyer holds station
and TIE fighters pass overhead.
"""
import base64
import math
import random
from datetime import date
from pathlib import Path

from PIL import Image

from scene import CITY_SPACE, paint_space, to_data_uri
from theme import DISPLAY, INK, MUTED, SANS, esc, svg_doc, twinkles

W, H = 1200, 800
TW, TH = 36, 18
OX, OY = 150, 228
SLAB = 22
HEIGHT_BY_LEVEL = {1: 54, 2: 88, 3: 132, 4: 206}
CYCLE_S = 22
RISE_END_PCT = {1: 5.5, 2: 7, 3: 8.5, 4: 10.5}
HOLD_END_PCT, SINK_END_PCT = 88, 95
ANCHOR = date(2020, 1, 5)
CYAN = "#6fd6ff"
FONTS = (("Inter", 400), ("Inter", 600), ("Orbitron", 700))


def iso(w, d):
    return OX + (w - d) * TW / 2, OY + (w + d) * TH / 2


def city_css():
    rules = [".b{transform-box:fill-box;transform-origin:50% 100%}",
             ".sway{animation:sway 5s ease-in-out infinite}",
             "@keyframes sway{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}",
             ".run{animation:tw 2.4s steps(2,jump-none) infinite}",
             ".sd{animation:sd 70s ease-in-out infinite alternate}",
             "@keyframes sd{from{transform:translate(0,0)}to{transform:translate(-60px,6px)}}",
             ".eng{animation:eng 1.6s ease-in-out infinite}",
             "@keyframes eng{0%,100%{opacity:.55}50%{opacity:1}}",
             ".tie{animation:tie 24s linear infinite;opacity:0}",
             "@keyframes tie{0%{transform:translate(1290px,300px) scale(.35);opacity:0}"
             "1%{opacity:1}30%{transform:translate(-120px,70px) scale(.85);opacity:1}"
             "31%,100%{transform:translate(-120px,70px) scale(.85);opacity:0}}"]
    for lvl, end in RISE_END_PCT.items():
        rules.append(
            f".b{lvl}{{animation:r{lvl} {CYCLE_S}s infinite both}}"
            f"@keyframes r{lvl}{{0%{{transform:translateY(12px) scale(.25,0);opacity:0;"
            f"animation-timing-function:cubic-bezier(.34,1.56,.64,1)}}"
            f"{end}%{{transform:none;opacity:1}}"
            f"{HOLD_END_PCT}%{{transform:none;opacity:1;animation-timing-function:cubic-bezier(.55,0,.75,0)}}"
            f"{SINK_END_PCT}%,100%{{transform:translateY(12px) scale(.25,0);opacity:0}}}}")
    return "".join(rules)


def sprite_defs(sprite_dir):
    defs, aspects = [], {}
    for path in sorted(Path(sprite_dir).glob("b*.webp")):
        with Image.open(path) as im:
            sw, sh = im.size
        b64 = base64.b64encode(path.read_bytes()).decode()
        defs.append(f'<symbol id="{path.stem}" viewBox="0 0 {sw} {sh}"><image width="{sw}" height="{sh}" '
                    f'href="data:image/webp;base64,{b64}"/></symbol>')
        aspects[path.stem] = sw / sh
    if not aspects:
        raise FileNotFoundError(f"No b*.webp sprites in {sprite_dir}")
    return "".join(defs), aspects


_BAGS = {}


def _bag(ids, user, k):
    key = (ids, user, k)
    if key not in _BAGS:
        order = list(ids)
        random.Random(f"{user}-bag-{k}").shuffle(order)
        if k > 0 and len(order) > 1 and order[0] == _bag(ids, user, k - 1)[-1]:
            order[0], order[-1] = order[-1], order[0]
        _BAGS[key] = order
    return _BAGS[key]


def sprite_for(day_iso, ids, user):
    """Stable per date: each run of len(ids) days uses every sprite once, no back-to-back repeats."""
    idx = (date.fromisoformat(day_iso) - ANCHOR).days
    n = len(ids)
    return _bag(tuple(sorted(ids)), user, idx // n)[idx % n]


def ripple(rng):
    """Delay function for a ripple spreading from a random tile, with a little chop."""
    ew, ed = rng.uniform(8, 44), rng.uniform(0, 6)
    phase = rng.uniform(0, math.tau)

    def delay(day):
        dist = math.hypot(day.week - ew, (day.weekday - ed) * 1.6)
        chop = .28 * math.sin(day.week * .55 + day.weekday * .9 + phase)
        return .3 + dist * .21 + chop + rng.uniform(0, .25)
    return delay


def board():
    def pt(w, d, dy=0):
        x, y = iso(w, d)
        return f"{x:.1f},{y+dy:.1f}"
    lo, hi = -0.7, (52.7, 6.7)
    top, right, bottom, left = pt(lo, lo), pt(hi[0], lo), pt(*hi), pt(lo, hi[1])
    lx, ly = iso(lo, hi[1])
    bx, by = iso(*hi)
    rx, ry = iso(hi[0], lo)
    lights = [(lx + (bx - lx) * i / 70, ly + (by - ly) * i / 70) for i in range(71)]
    lights += [(bx + (rx - bx) * i / 10, by + (ry - by) * i / 10) for i in range(1, 11)]
    dots = "".join(f'<circle class="run" style="animation-delay:-{(i % 4) * .6:.1f}s" cx="{x:.1f}" '
                   f'cy="{y+SLAB*.45:.1f}" r="1.7" fill="{CYAN}"/>' for i, (x, y) in enumerate(lights))
    grooves = "".join(f'<path d="M{pt(lo, hi[1], SLAB*f)} L{pt(*hi, SLAB*f)} L{pt(hi[0], lo, SLAB*f)}" '
                      f'fill="none" stroke="#000" stroke-opacity=".35"/>' for f in (.25, .75))
    return (f'<ellipse cx="{(lx+rx)/2+40:.0f}" cy="{by-200:.0f}" rx="560" ry="260" fill="url(#cityglow)"/>'
            f'<polygon points="{left} {bottom} {pt(*hi, SLAB)} {pt(lo, hi[1], SLAB)}" fill="url(#slabL)"/>'
            f'<polygon points="{bottom} {right} {pt(hi[0], lo, SLAB)} {pt(*hi, SLAB)}" fill="url(#slabR)"/>'
            f'{grooves}<polygon points="{top} {right} {bottom} {left}" fill="#141a26"/>'
            f'<path d="M{left} L{bottom} L{right}" fill="none" stroke="{CYAN}" stroke-width="1.6" stroke-opacity=".9"/>'
            f'<path d="M{left} L{bottom} L{right}" fill="none" stroke="{CYAN}" stroke-width="10" stroke-opacity=".1"/>'
            f'{dots}')


def tile(w, d):
    x, y = iso(w, d)
    s = .9
    return (f'<polygon points="{x:.1f},{y-TH/2*s:.1f} {x+TW/2*s:.1f},{y:.1f} {x:.1f},{y+TH/2*s:.1f} '
            f'{x-TW/2*s:.1f},{y:.1f}" fill="#1e2534" stroke="#2f3a52" stroke-width=".6"/>')


def building(day, sid, aspect, delay, sway_delay):
    x, y = iso(day.week, day.weekday)
    lvl = max(day.level, 1)
    h = HEIGHT_BY_LEVEL[lvl]
    bw = h * aspect
    return (f'<g class="sway" style="animation-delay:-{sway_delay:.2f}s"><g class="b b{lvl}" '
            f'style="animation-delay:{delay:.2f}s"><use href="#{sid}" x="{x-bw/2:.1f}" '
            f'y="{y+TH*0.42-h:.1f}" width="{bw:.1f}" height="{h}"/></g></g>')


def star_destroyer(x, y, s):
    lights = "".join(f'<circle cx="{40+i*16}" cy="{39-i*1.7:.1f}" r=".9" fill="#cfe6ff" opacity=".8"/>' for i in range(10))
    return (f'<g transform="translate({x} {y}) scale({s})"><g class="sd">'
            '<polygon points="0,40 220,16 220,40" fill="#9aa4b6"/>'
            '<polygon points="0,40 220,40 220,64" fill="#3f4757"/>'
            '<polygon points="0,40 220,40 220,42" fill="#c7d0de"/>'
            '<path d="M60 34 L200 20 M90 31 L210 22" stroke="#6d7688" stroke-width="1"/>'
            '<rect x="170" y="4" width="26" height="14" fill="#7f899b"/><rect x="160" y="0" width="46" height="6" fill="#aab3c3"/>'
            '<circle cx="164" cy="-1" r="3" fill="#aab3c3"/><circle cx="202" cy="-1" r="3" fill="#aab3c3"/>'
            f'{lights}<g class="eng"><circle cx="222" cy="30" r="5" fill="#7cc8ff"/><circle cx="223" cy="42" r="6" fill="#9fd8ff"/>'
            '<circle cx="222" cy="54" r="5" fill="#7cc8ff"/><ellipse cx="226" cy="42" rx="16" ry="20" fill="url(#engglow)"/></g>'
            '</g></g>')


TIE = ('<symbol id="tie" viewBox="-30 -28 60 56"><g fill="#2a303c" stroke="#7b8496" stroke-width="1.2">'
       '<polygon points="-22,-26 -15,-13 -15,13 -22,26 -29,13 -29,-13"/>'
       '<polygon points="22,-26 15,-13 15,13 22,26 29,13 29,-13"/></g>'
       '<path d="M-22 -26V26M22 -26V26M-29 0H29" stroke="#596276" stroke-width=".8"/>'
       '<rect x="-15" y="-2" width="30" height="4" fill="#8d96a8"/>'
       '<circle r="8" fill="#9aa3b5"/><circle r="4.5" fill="#1a1f29" stroke="#c1c9d6" stroke-width=".8"/></symbol>')


def tie_flyby():
    out = []
    for i, (dy, delay, size) in enumerate(((0, 0, 46), (26, .45, 38), (-18, 9.5, 42))):
        out.append(f'<g class="tie" style="animation-delay:{delay}s"><use href="#tie" x="{-size/2}" '
                   f'y="{dy-size/2}" width="{size}" height="{size}"/></g>')
    return "".join(out)


def brackets(x, y, w, h, n=14, color=CYAN, opacity=.7):
    p = (f"M{x} {y+n}V{y}H{x+n} M{x+w-n} {y}H{x+w}V{y+n} M{x+w} {y+h-n}V{y+h}H{x+w-n} "
         f"M{x+n} {y+h}H{x}V{y+h-n}")
    return f'<path d="{p}" fill="none" stroke="{color}" stroke-opacity="{opacity}" stroke-width="1.6"/>'


def hud_title(active):
    x, y = 792, 44
    return (brackets(x - 22, y - 18, 390, 112)
            + f'<text x="{x}" y="{y+8}" font-family="{SANS}" font-size="11.5" font-weight="600" '
              f'letter-spacing="2.6" fill="{CYAN}">ORBITAL SECTOR · LAST 365 DAYS</text>'
            + f'<text x="{x}" y="{y+44}" font-family="{DISPLAY}" font-size="27" font-weight="700" '
              f'letter-spacing="1" fill="{INK}">CONTRIBUTION CITY</text>'
            + f'<text x="{x}" y="{y+72}" font-family="{SANS}" font-size="14.5" fill="{MUTED}">'
              f'{active} towers raised · one for every day I shipped</text>')


def scenery_defs():
    return ('<radialGradient id="cityglow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ff5a3c" '
            'stop-opacity=".3"/><stop offset=".6" stop-color="#ff5a3c" stop-opacity=".08"/>'
            '<stop offset="1" stop-color="#ff5a3c" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="engglow" cx=".2" cy=".5" r=".8"><stop offset="0" stop-color="#9fd8ff" '
            'stop-opacity=".6"/><stop offset="1" stop-color="#9fd8ff" stop-opacity="0"/></radialGradient>'
            '<linearGradient id="slabL" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a4256"/>'
            '<stop offset="1" stop-color="#151a25"/></linearGradient>'
            '<linearGradient id="slabR" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#262c3b"/>'
            '<stop offset="1" stop-color="#0b0e15"/></linearGradient>' + TIE)


def build_city(user, total, days, sprite_dir, seed, today=None):
    rng = random.Random(seed)
    sprites, aspects = sprite_defs(sprite_dir)
    ids = sorted(aspects)
    delay = ripple(rng)
    bg = to_data_uri(paint_space(W, H, "city", **CITY_SPACE), "JPEG", 80)

    tiles = "".join(tile(d.week, d.weekday) for d in days)
    towers = []
    for d in sorted(days, key=lambda d: (d.week + d.weekday, d.week)):
        if d.count <= 0:
            continue
        sid = sprite_for(d.date, ids, user)
        towers.append(building(d, sid, aspects[sid], delay(d), d.week * .22 + d.weekday * .45))

    active = sum(d.count > 0 for d in days)
    stamp = (today or date.today()).strftime("%d %b %Y")
    footer = (f'<text x="40" y="{H-28}" font-family="{SANS}" font-size="13" letter-spacing="1.2" '
              f'fill="{MUTED}">UPDATED {esc(stamp.upper())}  ·  @{esc(user.upper())}</text>')
    body = (f'<image href="{bg}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/>'
            + twinkles(rng, W, 10, 420, 50)
            + star_destroyer(880, 200, .95) + tie_flyby()
            + board() + tiles + "".join(towers) + hud_title(active) + footer)
    return svg_doc(W, H, body, city_css(), scenery_defs() + sprites,
                   f"{user}'s contribution city", FONTS)

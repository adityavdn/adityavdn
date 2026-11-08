"""Contribution city: a floating Imperial platform in deep space, one tower per week.

The platform photo is warped onto a true perspective view (the near end is bigger),
towers scale with depth, rise in a ripple from a random point each day, and the
whole city sways gently like the surface of water.
"""
import base64
import io
import math
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from PIL import Image

from theme import DISPLAY, INK, MUTED, ROOT, SANS, esc, svg_doc, twinkles

W, H = 1200, 643
SS = 2                                    # supersample for the platform warp
SPACE = ROOT / "assets" / "space.jpg"
PLATFORM = ROOT / "assets" / "platform.webp"
# Top face of the platform photo (outer rim), and where it lands in the scene.
SRC_QUAD = [(7, 70), (1188, 203), (1330, 102), (260, 3)]          # FL, FR, BR, BL
DST_QUAD = [(30, 250), (960, 560), (1170, 455), (165, 186)]
# Grid area on the top face, in face coordinates (u along the length, v front -> back).
U0, U1 = .035, .84                        # the landing pad at the near end stays clear
ROW_V = (.33, .7)                         # two staggered rows: odd weeks front, even weeks back
TOWER_SCALE = .98                         # sprite pixels -> scene pixels at the near end
LEVEL_SCALE = {1: .6, 2: .74, 3: .87, 4: 1.0}
CYCLE_S = 22
RISE_END_PCT = {1: 5.5, 2: 7, 3: 8.5, 4: 10.5}
HOLD_END_PCT, SINK_END_PCT = 88, 95
ANCHOR = date(2020, 1, 5)
FONTS = (("Inter", 400), ("Inter", 600), ("Orbitron", 700))


def homography(src, dst):
    """3x3 matrix mapping the four src points onto the four dst points."""
    rows, rhs = [], []
    for (x, y), (u, v) in zip(src, dst):
        rows += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        rhs += [u, v]
    h = np.linalg.solve(np.array(rows, float), np.array(rhs, float))
    return np.append(h, 1).reshape(3, 3)


def apply(m, x, y):
    px, py, pw = m @ (x, y, 1)
    return px / pw, py / pw


UNIT = [(0, 0), (1, 0), (1, 1), (0, 1)]
FACE = homography(UNIT, DST_QUAD)          # (u, v) on the top face -> scene pixels


def face(u, v):
    return apply(FACE, u, v)


def depth_scale(u, v):
    """How big one unit of platform looks here, relative to the near end of the grid."""
    def step(uu, vv):
        (x0, y0), (x1, y1) = face(uu, vv), face(uu + .01, vv)
        return math.hypot(x1 - x0, y1 - y0)
    return step(u, v) / step(U1, ROW_V[0])


def warped_platform():
    """Warp the platform photo so its top face matches DST_QUAD (true perspective)."""
    src = Image.open(PLATFORM).convert("RGBA")
    back = homography([(x * SS, y * SS) for x, y in DST_QUAD], SRC_QUAD)
    coeffs = (back / back[2, 2]).flatten()[:8]
    out = src.transform((W * SS, H * SS), Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC)
    return out.resize((W, H), Image.LANCZOS)


def data_uri(img, fmt, quality):
    buf = io.BytesIO()
    img.save(buf, fmt, quality=quality, **({"method": 6} if fmt == "WEBP" else {"optimize": True}))
    mime = "image/webp" if fmt == "WEBP" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(buf.getvalue()).decode()}"


def sprite_defs(sprite_dir):
    defs, sizes = [], {}
    for path in sorted(Path(sprite_dir).glob("b*.webp")):
        with Image.open(path) as im:
            sw, sh = im.size
        b64 = base64.b64encode(path.read_bytes()).decode()
        defs.append(f'<symbol id="{path.stem}" viewBox="0 0 {sw} {sh}"><image width="{sw}" height="{sh}" '
                    f'href="data:image/webp;base64,{b64}"/></symbol>')
        sizes[path.stem] = (sw, sh)
    if not sizes:
        raise FileNotFoundError(f"No b*.webp sprites in {sprite_dir}")
    return "".join(defs), sizes


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


def sprite_for(week_start, ids, user):
    """Stable per calendar week: every run of len(ids) weeks uses each tower once, no back-to-back repeats."""
    idx = (week_start - ANCHOR).days // 7
    n = len(ids)
    return _bag(tuple(sorted(ids)), user, idx // n)[idx % n]


def weeks_of(days):
    """[(week index, first date, total, level 1-4)] for weeks with any contributions."""
    totals, first = defaultdict(int), {}
    for d in days:
        totals[d.week] += d.count
        first.setdefault(d.week, date.fromisoformat(d.date) - timedelta(days=d.weekday))
    active = sorted(v for v in totals.values() if v > 0)
    if not active:
        return []
    cuts = [active[int(len(active) * q)] for q in (.25, .5, .75)]
    out = []
    for w in sorted(totals):
        t = totals[w]
        if t > 0:
            out.append((w, first[w], t, 1 + sum(t > c for c in cuts)))
    return out


def ripple(rng, n_weeks):
    ew, er = rng.uniform(4, n_weeks - 4), rng.choice((0, 1))
    phase = rng.uniform(0, math.tau)

    def delay(week, row):
        dist = math.hypot(week - ew, (row - er) * 3)
        return .4 + dist * .32 + .3 * math.sin(week * .7 + phase) + rng.uniform(0, .2)
    return delay


def city_css():
    rules = [".b{transform-box:fill-box;transform-origin:50% 100%}",
             ".sway{animation:sway 5s ease-in-out infinite}",
             "@keyframes sway{0%,100%{transform:translateY(0)}50%{transform:translateY(-2.5px)}}",
             ".bob{animation:bob 9s ease-in-out infinite}",
             "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}",
             ".smoke{transform-box:fill-box;transform-origin:50% 100%;animation:smoke 7s ease-out infinite both}",
             "@keyframes smoke{0%{transform:translate(0,0) scale(.4);opacity:0}15%{opacity:.55}"
             "100%{transform:translate(14px,-46px) scale(1.6);opacity:0}}",
             ".sd{animation:sd 70s ease-in-out infinite alternate}",
             "@keyframes sd{from{transform:translate(0,0)}to{transform:translate(-40px,4px)}}",
             ".eng{animation:eng 1.6s ease-in-out infinite}",
             "@keyframes eng{0%,100%{opacity:.55}50%{opacity:1}}",
             ".tie{animation:tie 26s linear infinite;opacity:0}",
             "@keyframes tie{0%{transform:translate(1250px,300px) scale(.3);opacity:0}1%{opacity:1}"
             "30%{transform:translate(160px,40px) scale(.75);opacity:1}31%,100%{transform:translate(160px,40px) scale(.75);opacity:0}}"]
    for lvl, end in RISE_END_PCT.items():
        rules.append(
            f".b{lvl}{{animation:r{lvl} {CYCLE_S}s infinite both}}"
            f"@keyframes r{lvl}{{0%{{transform:translateY(8px) scale(.3,0);opacity:0;"
            f"animation-timing-function:cubic-bezier(.34,1.56,.64,1)}}"
            f"{end}%{{transform:none;opacity:1}}"
            f"{HOLD_END_PCT}%{{transform:none;opacity:1;animation-timing-function:cubic-bezier(.55,0,.75,0)}}"
            f"{SINK_END_PCT}%,100%{{transform:translateY(8px) scale(.3,0);opacity:0}}}}")
    return "".join(rules)


def tower(sid, size, u, v, level, delay, sway_delay):
    x, y = face(u, v)
    s = depth_scale(u, v) * TOWER_SCALE * LEVEL_SCALE[level]
    w, h = size[0] * s, size[1] * s
    return (f'<g class="sway" style="animation-delay:-{sway_delay:.2f}s"><g class="b b{level}" '
            f'style="animation-delay:{delay:.2f}s"><use href="#{sid}" x="{x-w/2:.1f}" y="{y-h*.97:.1f}" '
            f'width="{w:.1f}" height="{h:.1f}"/></g></g>'), (x, y - h * .9, s)


def smoke(rng, tops):
    out = []
    for x, y, s in rng.sample(tops, min(14, len(tops))):
        r = 7 * s / TOWER_SCALE
        out.append(f'<ellipse class="smoke" style="animation-delay:{rng.uniform(0, 7):.2f}s" cx="{x+rng.uniform(-8, 8)*s:.1f}" '
                   f'cy="{y:.1f}" rx="{r:.1f}" ry="{r*.8:.1f}" fill="url(#puff)"/>')
    return "".join(out)


def star_destroyer(x, y, s):
    lights = "".join(f'<circle cx="{40+i*16}" cy="{39-i*1.7:.1f}" r=".9" fill="#cfe6ff" opacity=".8"/>' for i in range(10))
    return (f'<g transform="translate({x} {y}) scale({s})"><g class="sd">'
            '<polygon points="0,40 220,16 220,40" fill="#aeb7c6"/>'
            '<polygon points="0,40 220,40 220,62" fill="#4a5262"/>'
            '<polygon points="0,40 220,40 220,42" fill="#d7dee8"/>'
            '<path d="M60 34 L200 20 M90 31 L210 22 M120 28 L214 20" stroke="#7a8395" stroke-width="1"/>'
            '<rect x="170" y="4" width="26" height="14" fill="#8a94a6"/><rect x="160" y="0" width="46" height="6" fill="#b8c0ce"/>'
            '<circle cx="164" cy="-1" r="3" fill="#b8c0ce"/><circle cx="202" cy="-1" r="3" fill="#b8c0ce"/>'
            f'{lights}<g class="eng"><ellipse cx="232" cy="42" rx="26" ry="22" fill="url(#engglow)"/>'
            '<circle cx="222" cy="31" r="5" fill="#bfe6ff"/><circle cx="223" cy="44" r="6" fill="#e6f6ff"/>'
            '<circle cx="222" cy="56" r="5" fill="#bfe6ff"/></g></g></g>')


TIE = ('<symbol id="tie" viewBox="-30 -28 60 56"><g fill="#2a303c" stroke="#8b94a6" stroke-width="1.2">'
       '<polygon points="-22,-26 -15,-13 -15,13 -22,26 -29,13 -29,-13"/>'
       '<polygon points="22,-26 15,-13 15,13 22,26 29,13 29,-13"/></g>'
       '<path d="M-22 -26V26M22 -26V26M-29 0H29" stroke="#596276" stroke-width=".8"/>'
       '<rect x="-15" y="-2" width="30" height="4" fill="#8d96a8"/>'
       '<circle r="8" fill="#9aa3b5"/><circle r="4.5" fill="#1a1f29" stroke="#c1c9d6" stroke-width=".8"/></symbol>')


def tie_flyby():
    return "".join(f'<g class="tie" style="animation-delay:{d}s"><use href="#tie" x="{-s/2}" y="{dy-s/2}" '
                   f'width="{s}" height="{s}"/></g>' for dy, d, s in ((0, 0, 40), (24, .5, 32), (-14, 11, 36)))


def scenery_defs():
    return ('<radialGradient id="engglow" cx=".3" cy=".5" r=".7"><stop offset="0" stop-color="#9fd8ff" '
            'stop-opacity=".8"/><stop offset="1" stop-color="#9fd8ff" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="puff" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#d9dde4" '
            'stop-opacity=".7"/><stop offset="1" stop-color="#d9dde4" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="cityglow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ff7a3c" '
            'stop-opacity=".22"/><stop offset="1" stop-color="#ff7a3c" stop-opacity="0"/></radialGradient>' + TIE)


def build_city(user, total, days, sprite_dir, seed, today=None):
    rng = random.Random(seed)
    sprites, sizes = sprite_defs(sprite_dir)
    ids = sorted(sizes)
    weeks = weeks_of(days)
    n_weeks = max(d.week for d in days) + 1
    delay = ripple(rng, n_weeks)

    placed = []
    for w, start, _total, level in weeks:
        row = w % 2                                   # 0 = back row, 1 = front row
        u = U0 + (w + .5) / n_weeks * (U1 - U0) + random.Random(f"{user}-{start}").uniform(-.003, .003)
        v = ROW_V[1] if row == 0 else ROW_V[0]
        placed.append((face(u, v)[1], w, row, start, level, u, v))
    towers, tops = [], []
    for _y, w, row, start, level, u, v in sorted(placed):
        sid = sprite_for(start, ids, user)
        svg, top = tower(sid, sizes[sid], u, v, level, delay(w, row), w * .22 + row * .9)
        towers.append(svg)
        tops.append(top)

    stamp = (today or date.today()).strftime("%d %b %Y")
    cx, cy = face((U0 + U1) / 2, .5)
    caption = (f'<text x="{W-28}" y="{H-24}" text-anchor="end" font-family="{SANS}" font-size="13" '
               f'letter-spacing="1.2" fill="{MUTED}">ONE TOWER PER WEEK  ·  {total:,} CONTRIBUTIONS  ·  '
               f'UPDATED {esc(stamp.upper())}</text>'
               f'<text x="28" y="40" font-family="{DISPLAY}" font-size="15" font-weight="700" letter-spacing="3" '
               f'fill="{INK}" opacity=".85">CONTRIBUTION CITY</text>')
    body = (f'<image href="{data_uri(Image.open(SPACE).convert("RGB"), "JPEG", 84)}" width="{W}" height="{H}"/>'
            + twinkles(rng, W, 10, 260, 40, (1110, 140, 200))
            + star_destroyer(800, 22, .74) + tie_flyby()
            + f'<g class="bob"><ellipse cx="{cx:.0f}" cy="{cy-40:.0f}" rx="520" ry="200" fill="url(#cityglow)"/>'
            + f'<image href="{data_uri(warped_platform(), "WEBP", 88)}" width="{W}" height="{H}"/>'
            + "".join(towers) + smoke(rng, tops) + "</g>" + caption)
    return svg_doc(W, H, body, city_css(), scenery_defs() + sprites, f"{user}'s contribution city", FONTS)

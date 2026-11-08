"""Hero banner: London at night on an iOS-style screen, with the name over the skyline."""
import random

from theme import (AMBER, FONT, INK, SUB, esc, far_skyline, home_indicator, moon, river,
                   sky_defs, stars, status_bar, svg_doc, windows)

W, H, HORIZON = 1200, 560, 440
SIL, EDGE = "#060a1a", "#22335f"

CSS = """
.wheel{transform-origin:1060px 290px;animation:spin 90s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.beacon{animation:tw 2.4s ease-in-out infinite both}
"""


def clock_tower(rng, x):
    top, w = 200, 44
    return (f'<rect x="{x}" y="{top}" width="{w}" height="{HORIZON-top}" fill="{SIL}" stroke="{EDGE}"/>'
            f'<rect x="{x-4}" y="{top}" width="{w+8}" height="56" fill="{SIL}" stroke="{EDGE}"/>'
            f'<circle cx="{x+w/2}" cy="{top+28}" r="16" fill="#ffe3a3"/>'
            f'<circle cx="{x+w/2}" cy="{top+28}" r="30" fill="url(#glow)"/>'
            f'<path d="M{x+w/2} {top+28}v-11M{x+w/2} {top+28}h8" stroke="#4a3412" stroke-width="2"/>'
            f'<path d="M{x-4} {top}L{x+w/2} {top-62}L{x+w+4} {top}Z" fill="{SIL}" stroke="{EDGE}"/>'
            f'<path d="M{x+w/2} {top-62}v-22" stroke="{EDGE}" stroke-width="2"/>'
            + "".join(f'<path d="M{px} {top}v-16" stroke="{EDGE}" stroke-width="2"/>'
                      for px in (x - 2, x + w + 2))
            + windows(rng, x + 4, top + 62, w - 8, HORIZON - top - 70, 0.35, 2))


def parliament(rng, x0, x1, top):
    spikes = "".join(f'<path d="M{x} {top}l3 -14l3 14Z" fill="{SIL}"/>' for x in range(int(x0), int(x1), 14))
    return (f'<rect x="{x0}" y="{top}" width="{x1-x0}" height="{HORIZON-top}" fill="{SIL}" stroke="{EDGE}"/>'
            f"{spikes}{windows(rng, x0+4, top+6, x1-x0-8, HORIZON-top-10, 0.3, 1.8)}")


def dome(rng, cx):
    base = HORIZON - 70
    return (f'<rect x="{cx-48}" y="{base}" width="96" height="70" fill="{SIL}" stroke="{EDGE}"/>'
            f'<rect x="{cx-30}" y="{base-26}" width="60" height="26" fill="{SIL}" stroke="{EDGE}"/>'
            f'<path d="M{cx-30} {base-26}A30 34 0 0 1 {cx+30} {base-26}Z" fill="{SIL}" stroke="{EDGE}"/>'
            f'<rect x="{cx-5}" y="{base-76}" width="10" height="18" fill="{SIL}" stroke="{EDGE}"/>'
            f'<path d="M{cx} {base-76}v-12" stroke="{EDGE}" stroke-width="2"/>'
            + windows(rng, cx - 44, base + 6, 88, 60, 0.3, 1.8))


def bridge_tower(rng, x, w=46, top=262, deck=412):
    spires = "".join(f'<path d="M{px-3} {top-4}l3 -20l3 20Z" fill="{SIL}" stroke="{EDGE}"/>'
                     for px in (x + 3, x + w - 3))
    return (f'<rect x="{x}" y="{top}" width="{w}" height="{HORIZON-top}" fill="{SIL}" stroke="{EDGE}"/>'
            f'<path d="M{x-2} {top}L{x+w/2} {top-46}L{x+w+2} {top}Z" fill="{SIL}" stroke="{EDGE}"/>'
            f'<path d="M{x+w/2} {top-46}v-14" stroke="{AMBER}" stroke-width="2"/>'
            f'<circle class="beacon" cx="{x+w/2}" cy="{top-62}" r="2.6" fill="#ff5b5b"/>'
            f'{spires}<path d="M{x+10} {deck}v-26a13 13 0 0 1 26 0v26Z" fill="#0d1838"/>'
            + windows(rng, x + 5, top + 8, w - 10, deck - top - 50, 0.4, 2.2))


def chain(x0, y0, cx, cy, x1, y1, n=11):
    pts = []
    for i in range(1, n):
        t = i / n
        px = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1
        py = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1
        pts.append(f'<circle class="tw" style="animation-delay:-{i*0.4:.1f}s" cx="{px:.1f}" '
                   f'cy="{py:.1f}" r="2" fill="#bfe1ff"/>')
    return (f'<path d="M{x0} {y0}Q{cx} {cy} {x1} {y1}" fill="none" stroke="#7fb1e6" '
            f'stroke-opacity=".75" stroke-width="2.4"/>' + "".join(pts))


def bridge(rng):
    deck, lx, rx = 412, 520, 690
    lamps = "".join(f'<circle cx="{x}" cy="{deck-4}" r="1.8" fill="{AMBER}"/>' for x in range(400, 862, 18))
    return (f'<rect x="380" y="{deck}" width="500" height="9" fill="{SIL}" stroke="{EDGE}"/>{lamps}'
            f'<rect x="{lx+46}" y="276" width="{rx-lx-46}" height="7" fill="{SIL}" stroke="{EDGE}"/>'
            f'<rect x="{lx+46}" y="290" width="{rx-lx-46}" height="7" fill="{SIL}" stroke="{EDGE}"/>'
            + chain(lx, 280, 470, 400, 382, 410) + chain(rx + 46, 280, 786, 400, 878, 410)
            + chain(lx + 46, 300, 605, 360, rx, 300, 8)
            + bridge_tower(rng, lx) + bridge_tower(rng, rx))


def shard(cx):
    lines = "".join(f'<path d="M{cx-30+i*6} {HORIZON}L{cx} 168" stroke="#5f8fd6" stroke-opacity=".25"/>'
                    for i in range(1, 10))
    return (f'<path d="M{cx-34} {HORIZON}L{cx-3} 160L{cx+4} 172L{cx+34} {HORIZON}Z" fill="#081128" '
            f'stroke="{EDGE}"/>{lines}<circle class="beacon" cx="{cx}" cy="160" r="2.4" fill="#ff5b5b"/>')


def wheel(cx=1060, cy=290, r=104):
    spokes = "".join(f'<path d="M{cx} {cy}L{cx+r*_cos(a)} {cy+r*_sin(a)}" stroke="#7fb1e6" '
                     f'stroke-opacity=".45"/>' for a in range(0, 360, 15))
    pods = "".join(f'<circle cx="{cx+r*_cos(a):.1f}" cy="{cy+r*_sin(a):.1f}" r="4" fill="#bfe1ff"/>'
                   for a in range(0, 360, 12))
    return (f'<path d="M{cx} {cy}L{cx-46} {HORIZON}M{cx} {cy}L{cx+46} {HORIZON}" stroke="{EDGE}" '
            f'stroke-width="5"/><g class="wheel"><circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
            f'stroke="#8ec5ff" stroke-opacity=".8" stroke-width="2.5"/>{spokes}{pods}</g>'
            f'<circle cx="{cx}" cy="{cy}" r="7" fill="#1c2c55" stroke="#8ec5ff"/>')


def _cos(deg):
    import math
    return round(math.cos(math.radians(deg)), 4)


def _sin(deg):
    import math
    return round(math.sin(math.radians(deg)), 4)


def landmarks(rng):
    return (parliament(rng, 40, 330, HORIZON - 52) + clock_tower(rng, 150) + dome(rng, 360)
            + shard(930) + bridge(rng) + wheel())


def headline(name, role, tagline):
    pill_w = 18 + len(tagline) * 8.2
    return (f'<g class="fadeup">'
            f'<text x="{W/2}" y="120" text-anchor="middle" font-family="{FONT}" font-size="52" '
            f'font-weight="800" letter-spacing="-1" fill="{INK}">{esc(name)}</text>'
            f'<text x="{W/2}" y="158" text-anchor="middle" font-family="{FONT}" font-size="20" '
            f'font-weight="500" fill="{SUB}">{esc(role)}</text></g>'
            f'<g class="fadeup" style="animation-delay:.35s">'
            f'<rect x="{W/2-pill_w/2}" y="176" width="{pill_w}" height="32" rx="16" fill="#ffffff" '
            f'fill-opacity=".1" stroke="#fff" stroke-opacity=".2"/>'
            f'<circle cx="{W/2-pill_w/2+18}" cy="192" r="4" fill="#34c759"/>'
            f'<text x="{W/2+8}" y="197" text-anchor="middle" font-family="{FONT}" font-size="14.5" '
            f'font-weight="600" fill="{INK}">{esc(tagline)}</text></g>')


def build_hero(name, role, tagline, seed):
    rng = random.Random(seed)
    lm = landmarks(rng)
    defs = (sky_defs(H, HORIZON) + f'<g id="lm">{lm}</g>'
            '<filter id="blur" x="-5%" y="-5%" width="110%" height="110%">'
            '<feGaussianBlur stdDeviation="2.2"/></filter>')
    body = (f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
            + stars(rng, W, 40, HORIZON - 160, 90) + moon(1090, 90, 22)
            + f'<ellipse cx="{W/2}" cy="{HORIZON}" rx="{W*0.6}" ry="120" fill="url(#glow)"/>'
            + far_skyline(rng, W, HORIZON, 120, "#0b1330", 0.9)
            + '<use href="#lm"/>' + river(rng, W, HORIZON, H)
            + f'<use href="#lm" transform="matrix(1 0 0 -0.55 0 {HORIZON*1.55})" opacity=".22" filter="url(#blur)"/>'
            + status_bar(W) + headline(name, role, tagline) + home_indicator(W, H))
    return svg_doc(W, H, body, CSS, defs, f"{name}: London at night")

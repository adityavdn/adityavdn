"""Contribution city: a moonlit valley, an isometric board, one landmark per active day.

Buildings rise in a ripple that spreads from a random point each day, then the
whole city sways gently like the surface of water.
"""
import base64
import math
import random
from datetime import date
from pathlib import Path

from PIL import Image

from scene import MOON, mist_strip, paint_backdrop, to_data_uri
from theme import AMBER, INK, MONO, MUTED, SANS, esc, svg_doc, twinkles

W, H = 1200, 652
TW, TH = 25, 12.5
OX, OY = 490, 236
SLAB = 18
HEIGHT_BY_LEVEL = {1: 32, 2: 54, 3: 86, 4: 150}
CYCLE_S = 20
RISE_END_PCT = {1: 6, 2: 7.5, 3: 9, 4: 11}
HOLD_END_PCT, SINK_END_PCT = 87, 95
ANCHOR = date(2020, 1, 5)
FONTS = (("Inter", 400), ("Inter", 600), ("Inter", 800))

ICONS = {
    "castle": '<path fill="{c}" d="M3 21V8h2.5v2H7V8h2.5v2H11V8h2v2h1.5V8H17v2h1.5V8H21v13h-6.5v-4.5a2.5 2.5 0 0 0-5 0V21z"/>',
    "calendar": ('<g fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round"><rect x="3.5" y="5" '
                 'width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/></g><g fill="{c}">'
                 '<rect x="7" y="13" width="2.4" height="2.4" rx=".6"/><rect x="10.8" y="13" width="2.4" height="2.4" rx=".6"/>'
                 '<rect x="14.6" y="13" width="2.4" height="2.4" rx=".6"/><rect x="7" y="16.6" width="2.4" height="2.4" rx=".6"/>'
                 '<rect x="10.8" y="16.6" width="2.4" height="2.4" rx=".6"/></g>'),
    "flame": '<path fill="{c}" d="M12.5 2.5c.8 3.4 5.5 5.6 5.5 11a6 6 0 0 1-12 0c0-2.6 1.3-4.3 2.6-5.4.1 2.1 1 3.4 2.3 3.6-.6-3.5.2-6.6 1.6-9.2z"/>',
    "streak": ('<g fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
               '<path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3"/><path d="M19.8 4.2v4.6h-4.6"/></g>'),
    "bars": ('<g fill="{c}"><rect x="4" y="13" width="3.6" height="7.5" rx="1"/><rect x="10.2" y="9" width="3.6" '
             'height="11.5" rx="1"/><rect x="16.4" y="4" width="3.6" height="16.5" rx="1"/></g>'),
    "layers": ('<g fill="none" stroke="{c}" stroke-width="1.7" stroke-linejoin="round"><path d="M12 3.5l8.5 4.6L12 12.7 '
               '3.5 8.1z"/><path d="M3.5 12l8.5 4.6 8.5-4.6M3.5 15.9l8.5 4.6 8.5-4.6"/></g>'),
}


def icon(name, x, y, size, color=AMBER):
    s = size / 24
    return f'<g transform="translate({x} {y}) scale({s:.3f})">{ICONS[name].format(c=color)}</g>'


def iso(w, d):
    return OX + (w - d) * TW / 2, OY + (w + d) * TH / 2


def city_css():
    rules = [".b{transform-box:fill-box;transform-origin:50% 100%}",
             ".sway{animation:sway 5s ease-in-out infinite}",
             "@keyframes sway{0%,100%{transform:translateY(0)}50%{transform:translateY(-2.4px)}}",
             ".mist{animation:drift 46s ease-in-out infinite alternate}",
             ".mist2{animation:drift 64s ease-in-out infinite alternate-reverse}",
             "@keyframes drift{from{transform:translateX(-140px)}to{transform:translateX(60px)}}",
             ".halo{animation:halo 7s ease-in-out infinite;transform-box:fill-box;transform-origin:center}",
             "@keyframes halo{0%,100%{opacity:.55;transform:scale(1)}50%{opacity:.9;transform:scale(1.06)}}",
             ".edge{animation:tw 3.6s ease-in-out infinite both}"]
    for lvl, end in RISE_END_PCT.items():
        rules.append(
            f".b{lvl}{{animation:r{lvl} {CYCLE_S}s infinite both}}"
            f"@keyframes r{lvl}{{0%{{transform:translateY(10px) scale(.2,0);opacity:0;"
            f"animation-timing-function:cubic-bezier(.34,1.56,.64,1)}}"
            f"{end}%{{transform:none;opacity:1}}"
            f"{HOLD_END_PCT}%{{transform:none;opacity:1;animation-timing-function:cubic-bezier(.55,0,.75,0)}}"
            f"{SINK_END_PCT}%,100%{{transform:translateY(10px) scale(.2,0);opacity:0}}}}")
    return "".join(rules)


def sprite_defs(sprite_dir):
    defs, aspects = [], {}
    for path in sorted(Path(sprite_dir).glob("b*.webp")):
        with Image.open(path) as im:
            sw, sh = im.size
        b64 = base64.b64encode(_warm(path)).decode()
        defs.append(f'<symbol id="{path.stem}" viewBox="0 0 {sw} {sh}"><image width="{sw}" height="{sh}" '
                    f'href="data:image/webp;base64,{b64}"/></symbol>')
        aspects[path.stem] = sw / sh
    if not aspects:
        raise FileNotFoundError(f"No b*.webp sprites in {sprite_dir}")
    return "".join(defs), aspects


def sprite_for(day_iso, ids, user):
    """Stable per date: each run of len(ids) days uses every sprite once, no back-to-back repeats."""
    idx = (date.fromisoformat(day_iso) - ANCHOR).days
    n = len(ids)
    return _bag(tuple(sorted(ids)), user, idx // n)[idx % n]


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


def _warm(path):
    """Push a sprite toward lamp-lit amber so the city glows like it is lit from inside."""
    import io
    from PIL import ImageEnhance
    with Image.open(path) as im:
        rgba = im.convert("RGBA")
    alpha = rgba.getchannel("A")
    rgb = ImageEnhance.Color(rgba.convert("RGB")).enhance(1.25)
    rgb = ImageEnhance.Brightness(rgb).enhance(1.1)
    r, g, b = rgb.split()
    rgb = Image.merge("RGB", (r.point(lambda v: min(255, int(v * 1.08 + 6))), g, b.point(lambda v: int(v * .8))))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    buf = io.BytesIO()
    out.save(buf, "WEBP", quality=82, method=6)
    return buf.getvalue()


def board():
    def pt(w, d, dy=0):
        x, y = iso(w, d)
        return f"{x:.1f},{y+dy:.1f}"
    lo, hi = -0.7, (52.7, 6.7)
    top, right, bottom, left = pt(lo, lo), pt(hi[0], lo), pt(*hi), pt(lo, hi[1])
    lx, ly = iso(lo, hi[1])
    bx, by = iso(*hi)
    rx, ry = iso(hi[0], lo)
    lamps = []
    for i in range(0, 61):
        t = i / 60
        lamps.append((lx + (bx - lx) * t, ly + (by - ly) * t))
    for i in range(1, 9):
        t = i / 8
        lamps.append((bx + (rx - bx) * t, by + (ry - by) * t))
    dots = "".join(f'<circle class="edge" style="animation-delay:-{(i*0.37)%3.6:.2f}s" cx="{x:.1f}" '
                   f'cy="{y+2.5:.1f}" r="1.5" fill="#ffd48a"/>' for i, (x, y) in enumerate(lamps))
    return (f'<ellipse cx="{(lx+rx)/2+40:.0f}" cy="{by-150:.0f}" rx="470" ry="230" fill="url(#cityglow)"/>'
            f'<polygon points="{left} {bottom} {pt(*hi, SLAB)} {pt(lo, hi[1], SLAB)}" fill="url(#slabL)"/>'
            f'<polygon points="{bottom} {right} {pt(hi[0], lo, SLAB)} {pt(*hi, SLAB)}" fill="url(#slabR)"/>'
            f'<polygon points="{top} {right} {bottom} {left}" fill="#26252c"/>'
            f'<path d="M{left} L{bottom} L{right}" fill="none" stroke="#ffb35c" stroke-width="2.4" '
            f'stroke-opacity=".75"/><path d="M{left} L{bottom} L{right}" fill="none" stroke="#ffb35c" '
            f'stroke-width="9" stroke-opacity=".12"/>{dots}')


def tile(w, d):
    x, y = iso(w, d)
    s = .9
    return (f'<polygon points="{x:.1f},{y-TH/2*s:.1f} {x+TW/2*s:.1f},{y:.1f} {x:.1f},{y+TH/2*s:.1f} '
            f'{x-TW/2*s:.1f},{y:.1f}" fill="#3a3740" stroke="#4b4752" stroke-width=".5"/>')


def building(day, sid, aspect, delay, sway_delay):
    x, y = iso(day.week, day.weekday)
    lvl = max(day.level, 1)
    h = HEIGHT_BY_LEVEL[lvl]
    bw = h * aspect
    return (f'<g class="sway" style="animation-delay:-{sway_delay:.2f}s"><g class="b b{lvl}" '
            f'style="animation-delay:{delay:.2f}s"><use href="#{sid}" x="{x-bw/2:.1f}" '
            f'y="{y+TH*0.45-h:.1f}" width="{bw:.1f}" height="{h}"/></g></g>')


def ripple(rng):
    """Delay function for a ripple spreading from a random tile, with a little chop."""
    ew, ed = rng.uniform(8, 44), rng.uniform(0, 6)
    phase = rng.uniform(0, math.tau)

    def delay(day):
        dist = math.hypot(day.week - ew, (day.weekday - ed) * 1.6)
        chop = .28 * math.sin(day.week * .55 + day.weekday * .9 + phase)
        return .3 + dist * .21 + chop + rng.uniform(0, .25)
    return delay


def streaks(days):
    ordered = sorted(days, key=lambda d: d.date)
    longest = run = 0
    for d in ordered:
        run = run + 1 if d.count > 0 else 0
        longest = max(longest, run)
    current = 0
    tail = ordered[:-1] if ordered and ordered[-1].count == 0 else ordered
    for d in reversed(tail):
        if d.count == 0:
            break
        current += 1
    return current, longest


def compact(n):
    return f"{n/1000:.1f}K".replace(".0K", "K") if n >= 1000 else str(n)


def stat_panel(user, total, days):
    active = sum(d.count > 0 for d in days)
    busiest = max(days, key=lambda d: d.count)
    current, longest = streaks(days)
    rows = [("calendar", "Active days", f"{active}"),
            ("flame", "Busiest day", f"{busiest.count} · {date.fromisoformat(busiest.date):%d %b}"),
            ("streak", "Current streak", f"{current} days"),
            ("bars", "Longest streak", f"{longest} days"),
            ("castle", "Landmarks built", f"{active}")]
    x, y, w, h = 34, 56, 344, 530
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="26" fill="#0a111f" fill-opacity=".66"/>',
           f'<rect x="{x+.5}" y="{y+.5}" width="{w-1}" height="{h-1}" rx="26" fill="none" stroke="#fff" stroke-opacity=".14"/>',
           icon("castle", x + 30, y + 26, 30),
           f'<rect x="{x+76}" y="{y+26}" width="1" height="30" fill="#fff" opacity=".22"/>',
           f'<text x="{x+94}" y="{y+48}" font-family="{SANS}" font-size="17.5" font-weight="600" '
           f'letter-spacing="1.4" fill="{INK}">CONTRIBUTION CITY</text>',
           f'<text x="{x+28}" y="{y+138}" font-family="{SANS}" font-size="72" font-weight="800" '
           f'letter-spacing="-2.5" fill="{INK}">{compact(total)}</text>',
           f'<text x="{x+30}" y="{y+172}" font-family="{SANS}" font-size="17" fill="#c8cfe0">'
           f'contributions in the last year</text>',
           f'<rect x="{x+30}" y="{y+196}" width="{w-60}" height="1" fill="#fff" opacity=".14"/>']
    for i, (ic, label, value) in enumerate(rows):
        ry = y + 240 + i * 46
        out.append(icon(ic, x + 30, ry - 16, 21)
                   + f'<text x="{x+64}" y="{ry}" font-family="{SANS}" font-size="16" fill="#e4e8f2">{esc(label)}</text>'
                   + f'<text x="{x+w-30}" y="{ry}" text-anchor="end" font-family="{SANS}" font-size="16" '
                     f'font-weight="600" fill="{AMBER}">{esc(value)}</text>')
    out.append(f'<rect x="{x+30}" y="{y+h-68}" width="{w-60}" height="1" fill="#fff" opacity=".14"/>'
               f'<text x="{x+30}" y="{y+h-30}" font-family="{MONO}" font-size="16" fill="#dfe4f0">@{esc(user)}</text>')
    return "".join(out)


def scenery_defs():
    return ('<radialGradient id="cityglow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ff9b3d" '
            'stop-opacity=".42"/><stop offset=".6" stop-color="#ff9b3d" stop-opacity=".12"/>'
            '<stop offset="1" stop-color="#ff9b3d" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="moonglow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#dfe6ff" '
            'stop-opacity=".35"/><stop offset="1" stop-color="#dfe6ff" stop-opacity="0"/></radialGradient>'
            '<linearGradient id="slabL" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2d2a2c"/>'
            '<stop offset="1" stop-color="#141318"/></linearGradient>'
            '<linearGradient id="slabR" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1d1b20"/>'
            '<stop offset="1" stop-color="#0c0b10"/></linearGradient>')


def build_city(user, total, days, sprite_dir, seed, today=None):
    rng = random.Random(seed)
    sprites, aspects = sprite_defs(sprite_dir)
    ids = sorted(aspects)
    delay = ripple(rng)
    bg = to_data_uri(paint_backdrop(), "JPEG", 80)
    mist = to_data_uri(mist_strip(), "WEBP", 70)

    tiles = "".join(tile(d.week, d.weekday) for d in days)
    towers = []
    for d in sorted(days, key=lambda d: (d.week + d.weekday, d.week)):
        if d.count <= 0:
            continue
        sid = sprite_for(d.date, ids, user)
        towers.append(building(d, sid, aspects[sid], delay(d), d.week * .22 + d.weekday * .45))

    mx, my, mr = MOON
    stamp = (today or date.today()).strftime("%d %b %Y")
    note = f"One landmark per active day  ·  Updated {stamp}"
    footer = (icon("layers", W - 36 - len(note) * 7.4 - 30, H - 44, 20, "#cfd6e6")
              + f'<text x="{W-36}" y="{H-28}" text-anchor="end" font-family="{SANS}" font-size="14.5" '
                f'fill="#cfd6e6">{esc(note)}</text>')
    body = (f'<image href="{bg}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/>'
            + twinkles(rng, W, 10, 230, 46, (mx, my, 120))
            + f'<circle class="halo" cx="{mx}" cy="{my}" r="{mr*3.2}" fill="url(#moonglow)"/>'
            + f'<image class="mist" href="{mist}" x="-60" y="300" width="1500" height="150" opacity=".8"/>'
            + f'<image class="mist2" href="{mist}" x="-200" y="420" width="1500" height="150" opacity=".6"/>'
            + board() + tiles + "".join(towers) + stat_panel(user, total, days) + footer)
    return svg_doc(W, H, body, city_css(), scenery_defs() + sprites,
                   f"{user}'s contribution city", FONTS)

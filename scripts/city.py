"""Contribution city: an isometric board, one landmark sprite rising per active day."""
import base64
import random
from datetime import date
from pathlib import Path

from theme import (AMBER, FONT, INK, MONO, SUB, esc, far_skyline, glass_panel, moon, river,
                   sky_defs, stars, svg_doc)

W, H, HORIZON = 1200, 680, 330
TW, TH = 26, 13              # tile width / height on screen
OX, OY = 470, 236            # screen position of week 0, weekday 0
SLAB = 14                    # board thickness
SPRITE_SRC_H = 300
HEIGHT_BY_LEVEL = {1: 30, 2: 52, 3: 84, 4: 150}
CYCLE_S = 20
RISE_END_PCT = {1: 8, 2: 10, 3: 12, 4: 15}   # bigger days rise for longer
HOLD_END_PCT, SINK_END_PCT = 86, 94


def iso(w, d):
    return OX + (w - d) * TW / 2, OY + (w + d) * TH / 2


def city_css():
    rules = [".b,.t{transform-box:fill-box;transform-origin:50% 100%}"]
    for lvl, end in RISE_END_PCT.items():
        rules.append(
            f".b{lvl}{{animation:r{lvl} {CYCLE_S}s infinite both}}"
            f"@keyframes r{lvl}{{0%{{transform:scaleY(0) translateY(6px);opacity:0;"
            f"animation-timing-function:cubic-bezier(.16,1,.3,1)}}"
            f"{end}%{{transform:none;opacity:1}}"
            f"{HOLD_END_PCT}%{{transform:none;opacity:1;animation-timing-function:cubic-bezier(.7,0,.84,0)}}"
            f"{SINK_END_PCT}%,100%{{transform:scaleY(0) translateY(6px);opacity:0}}}}"
            f".t{lvl}{{animation:l{lvl} {CYCLE_S}s ease-out infinite both}}"
            f"@keyframes l{lvl}{{0%{{opacity:.1}}{end}%{{opacity:1}}{HOLD_END_PCT}%{{opacity:1}}"
            f"{SINK_END_PCT}%,100%{{opacity:.1}}}}")
    return "".join(rules)


def sprite_defs(sprite_dir):
    defs, aspects = [], {}
    for path in sorted(Path(sprite_dir).glob("b*.webp")):
        from PIL import Image
        with Image.open(path) as im:
            sw, sh = im.size
        sid = path.stem
        b64 = base64.b64encode(path.read_bytes()).decode()
        defs.append(f'<symbol id="{sid}" viewBox="0 0 {sw} {sh}"><image width="{sw}" height="{sh}" '
                    f'href="data:image/webp;base64,{b64}"/></symbol>')
        aspects[sid] = sw / sh
    if not aspects:
        raise FileNotFoundError(f"No b*.webp sprites in {sprite_dir}")
    return "".join(defs), aspects


def shuffle_bag(ids, rng):
    """Yield sprite ids so none repeats until every one has been used."""
    last = None
    while True:
        bag = list(ids)
        rng.shuffle(bag)
        if len(bag) > 1 and bag[0] == last:
            bag[0], bag[-1] = bag[-1], bag[0]
        for item in bag:
            last = item
            yield item


def board():
    def pt(w, d):
        x, y = iso(w, d)
        return f"{x:.1f},{y:.1f}"
    top, right, bottom, left = pt(-0.6, -0.6), pt(52.6, -0.6), pt(52.6, 6.6), pt(-0.6, 6.6)
    lx, ly = iso(-0.6, 6.6)
    bx, by = iso(52.6, 6.6)
    rx, ry = iso(52.6, -0.6)
    return (f'<ellipse cx="{(lx+rx)/2:.0f}" cy="{by-110:.0f}" rx="430" ry="190" fill="url(#glow)" opacity=".7"/>'
            f'<polygon points="{left} {bottom} {bx:.1f},{by+SLAB} {lx:.1f},{ly+SLAB}" fill="#0b1331"/>'
            f'<polygon points="{bottom} {right} {rx:.1f},{ry+SLAB} {bx:.1f},{by+SLAB}" fill="#060b22"/>'
            f'<polygon points="{top} {right} {bottom} {left}" fill="#111a3c" stroke="#2b3c78" stroke-width="1"/>'
            f'<path d="M{left} L{bottom} L{right}" fill="none" stroke="#3b4f93" stroke-opacity=".6"/>')


def tile(w, d, active, level, delay):
    x, y = iso(w, d)
    s = 0.84
    pts = (f"{x:.1f},{y-TH/2*s:.1f} {x+TW/2*s:.1f},{y:.1f} "
           f"{x:.1f},{y+TH/2*s:.1f} {x-TW/2*s:.1f},{y:.1f}")
    base = f'<polygon points="{pts}" fill="#1a2552" stroke="#2a3a73" stroke-width=".6"/>'
    if not active:
        return base
    return (base + f'<g class="t{level}" style="animation-delay:{delay:.2f}s">'
            f'<polygon points="{pts}" fill="{AMBER}" opacity="{0.35+0.12*level:.2f}"/>'
            f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{TW*0.9:.1f}" ry="{TH*0.9:.1f}" fill="url(#lamp)"/></g>')


def building(w, d, level, sid, aspect, delay):
    x, y = iso(w, d)
    h = HEIGHT_BY_LEVEL[level]
    bw = h * aspect
    return (f'<g class="b b{level}" style="animation-delay:{delay:.2f}s">'
            f'<use href="#{sid}" x="{x-bw/2:.1f}" y="{y+TH*0.42-h:.1f}" width="{bw:.1f}" height="{h}"/></g>')


def delay_for(day):
    return 0.25 + day.week * 0.13 + day.weekday * 0.03


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
    active = [d for d in days if d.count > 0]
    busiest = max(days, key=lambda d: d.count)
    current, longest = streaks(days)
    busiest_date = date.fromisoformat(busiest.date).strftime("%d %b")
    rows = [("Active days", f"{len(active)}"),
            ("Busiest day", f"{busiest.count} · {busiest_date}"),
            ("Current streak", f"{current} days"),
            ("Longest streak", f"{longest} days"),
            ("Landmarks built", f"{len(active)}")]
    x, y = 44, 64
    out = [glass_panel(x, y, 300, 420),
           f'<text x="{x+26}" y="{y+42}" font-family="{MONO}" font-size="13" font-weight="700" '
           f'letter-spacing="3.5" fill="{AMBER}">CONTRIBUTION CITY</text>',
           f'<text x="{x+24}" y="{y+112}" font-family="{FONT}" font-size="66" font-weight="800" '
           f'letter-spacing="-2" fill="{INK}">{compact(total)}</text>',
           f'<text x="{x+26}" y="{y+140}" font-family="{FONT}" font-size="16" font-weight="500" '
           f'fill="{SUB}">contributions in the last year</text>',
           f'<rect x="{x+26}" y="{y+162}" width="248" height="1" fill="#fff" opacity=".14"/>']
    for i, (label, value) in enumerate(rows):
        ry = y + 196 + i * 38
        out.append(f'<text x="{x+26}" y="{ry}" font-family="{FONT}" font-size="15" fill="{SUB}">{esc(label)}</text>'
                   f'<text x="{x+274}" y="{ry}" text-anchor="end" font-family="{FONT}" font-size="15" '
                   f'font-weight="700" fill="{INK}">{esc(value)}</text>')
    out.append(f'<text x="{x+26}" y="{y+398}" font-family="{MONO}" font-size="13" fill="{SUB}">@{esc(user)}</text>')
    return "".join(out)


def build_city(user, total, days, sprite_dir, seed, today=None):
    rng = random.Random(seed)
    sprites, aspects = sprite_defs(sprite_dir)
    bag = shuffle_bag(sorted(aspects), rng)
    defs = (sky_defs(H, HORIZON) + sprites +
            '<radialGradient id="lamp" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ffcf7a" '
            'stop-opacity=".9"/><stop offset=".45" stop-color="#ff9d3c" stop-opacity=".35"/>'
            '<stop offset="1" stop-color="#ff9d3c" stop-opacity="0"/></radialGradient>')

    by_date = sorted(days, key=lambda d: d.date)
    picks = {d.date: next(bag) for d in by_date if d.count > 0}
    tiles = "".join(tile(d.week, d.weekday, d.count > 0, max(d.level, 1), delay_for(d)) for d in days)
    towers = "".join(
        building(d.week, d.weekday, max(d.level, 1), picks[d.date], aspects[picks[d.date]], delay_for(d))
        for d in sorted(days, key=lambda d: (d.week + d.weekday, d.week))
        if d.count > 0)

    stamp = (today or date.today()).strftime("%d %b %Y")
    body = (f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
            + stars(rng, W, 20, HORIZON - 60, 70) + moon(1110, 70, 18)
            + far_skyline(rng, W, HORIZON, 90, "#0b1330", 0.75) + river(rng, W, HORIZON, H, 50)
            + board() + tiles + towers + stat_panel(user, total, days)
            + f'<text x="{W-36}" y="{H-24}" text-anchor="end" font-family="{FONT}" font-size="12.5" '
              f'fill="{SUB}" opacity=".75">one landmark per active day · updated {stamp}</text>')
    return svg_doc(W, H, body, city_css(), defs, f"{user}'s contribution city")


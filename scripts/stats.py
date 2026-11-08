"""Imperial operations readout: the headline numbers plus a weekly activity bar strip."""
import random
from collections import defaultdict
from datetime import date

from scene import paint_space, to_data_uri
from theme import DISPLAY, INK, MUTED, SANS, esc, svg_doc

W, H = 1200, 340
CYAN = "#6fd6ff"
GREEN = "#3ddc84"
FONTS = (("Inter", 400), ("Inter", 600), ("Orbitron", 700))

CSS = """
.bar{transform-box:fill-box;transform-origin:50% 100%;animation:grow 1.2s cubic-bezier(.16,1,.3,1) both}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
.scan{animation:scan 7s linear infinite}
@keyframes scan{from{transform:translateX(-80px)}to{transform:translateX(1280px)}}
.blink{animation:tw 1.4s steps(2,jump-none) infinite}
.count{animation:fadein 1s ease-out both}
@keyframes fadein{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
"""


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


def _brackets(x, y, w, h, n=16):
    p = (f"M{x} {y+n}V{y}H{x+n} M{x+w-n} {y}H{x+w}V{y+n} M{x+w} {y+h-n}V{y+h}H{x+w-n} "
         f"M{x+n} {y+h}H{x}V{y+h-n}")
    return f'<path d="{p}" fill="none" stroke="{CYAN}" stroke-opacity=".75" stroke-width="1.6"/>'


def _tiles(total, days):
    active = sum(d.count > 0 for d in days)
    busiest = max(days, key=lambda d: d.count)
    current, longest = streaks(days)
    tiles = [("CONTRIBUTIONS", compact(total), "transmissions in 12 months"),
             ("ACTIVE DAYS", str(active), f"of {len(days)} days on duty"),
             ("BUSIEST DAY", str(busiest.count), f"{date.fromisoformat(busiest.date):%d %b %Y}"),
             ("CURRENT STREAK", str(current), "days unbroken"),
             ("LONGEST STREAK", str(longest), "days, personal record")]
    out, x0, tw = [], 40, 224
    for i, (label, value, sub) in enumerate(tiles):
        x = x0 + i * tw
        if i:
            out.append(f'<rect x="{x}" y="84" width="1" height="104" fill="#fff" opacity=".1"/>')
        tx = x + (22 if i else 4)
        out.append(f'<g class="count" style="animation-delay:{.1+i*.12:.2f}s">'
                   f'<text x="{tx}" y="100" font-family="{SANS}" font-size="11" font-weight="600" '
                   f'letter-spacing="2" fill="{MUTED}">{esc(label)}</text>'
                   f'<text x="{tx-2}" y="152" font-family="{DISPLAY}" font-size="40" font-weight="700" '
                   f'fill="{INK}">{esc(value)}</text>'
                   f'<text x="{tx}" y="180" font-family="{SANS}" font-size="13" fill="{CYAN}">{esc(sub)}</text></g>')
    return "".join(out)


def _weekly(days):
    weeks = defaultdict(int)
    for d in days:
        weeks[d.week] += d.count
    n = max(weeks) + 1
    peak = max(weeks.values()) or 1
    x0, x1, base, top = 40, 1160, 306, 236
    bw = (x1 - x0) / n
    out = [f'<text x="{x0}" y="222" font-family="{SANS}" font-size="11" font-weight="600" letter-spacing="2" '
           f'fill="{MUTED}">HYPERSPACE ACTIVITY · WEEKLY</text>',
           f'<text x="{x1}" y="222" text-anchor="end" font-family="{SANS}" font-size="11" font-weight="600" '
           f'letter-spacing="2" fill="{MUTED}">PEAK {peak:,} / WEEK</text>',
           f'<rect x="{x0}" y="{base}" width="{x1-x0}" height="1" fill="{CYAN}" opacity=".35"/>']
    for w in range(n):
        v = weeks.get(w, 0)
        h = max(2, (base - top) * v / peak)
        out.append(f'<rect class="bar" style="animation-delay:{.4+w*.018:.3f}s" x="{x0+w*bw+1.5:.1f}" '
                   f'y="{base-h:.1f}" width="{bw-3:.1f}" height="{h:.1f}" rx="1.5" fill="url(#barfill)"/>')
    return "".join(out)


def build_stats(user, total, days, seed):
    bg = to_data_uri(paint_space(W, H, "stats", nebulae=[(980, 80, 200, 60, (40, 90, 150), .3),
                                                         (200, 300, 200, 60, (120, 40, 90), .22)], stars=380),
                     "JPEG", 80)
    defs = ('<linearGradient id="barfill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9fe6ff"/>'
            '<stop offset="1" stop-color="#2b7fb0"/></linearGradient>'
            '<linearGradient id="scanfill" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6fd6ff" '
            'stop-opacity="0"/><stop offset="1" stop-color="#6fd6ff" stop-opacity=".16"/></linearGradient>'
            '<pattern id="lines" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" '
            'fill="#fff" opacity=".03"/></pattern>')
    head = (f'<text x="40" y="52" font-family="{DISPLAY}" font-size="15" font-weight="700" letter-spacing="3" '
            f'fill="{INK}">IMPERIAL OPERATIONS READOUT</text>'
            f'<circle class="blink" cx="{W-262}" cy="47" r="4.5" fill="{GREEN}"/>'
            f'<text x="{W-40}" y="52" text-anchor="end" font-family="{SANS}" font-size="12" font-weight="600" '
            f'letter-spacing="2" fill="{GREEN}">ALL SYSTEMS OPERATIONAL</text>'
            f'<rect x="40" y="66" width="{W-80}" height="1" fill="#fff" opacity=".12"/>')
    body = (f'<image href="{bg}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/>'
            f'<rect width="{W}" height="{H}" fill="#03060d" opacity=".45"/><rect width="{W}" height="{H}" fill="url(#lines)"/>'
            + _brackets(14, 14, W - 28, H - 28) + head + _tiles(total, days) + _weekly(days)
            + f'<rect class="scan" x="0" y="14" width="80" height="{H-28}" fill="url(#scanfill)"/>')
    return svg_doc(W, H, body, CSS, defs, f"{user}: contribution stats", FONTS)

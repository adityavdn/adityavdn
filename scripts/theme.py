"""Shared night-London look: iOS-style card frame, sky, stars, moon, skyline, river."""
from html import escape

FONT = ("-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', "
        "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif")
MONO = "'SF Mono', ui-monospace, Menlo, Consolas, monospace"
RADIUS = 34
INK = "#f5f7ff"
SUB = "#aab6e8"
AMBER = "#ffc46b"
WINDOW_COLORS = ("#ffd58a", "#ffcf7a", "#fff1c9", "#9fd2ff")

BASE_CSS = """
.tw{animation:tw 4.5s ease-in-out infinite both}
@keyframes tw{0%,100%{opacity:.25}50%{opacity:1}}
.shim{animation:shim 3.2s ease-in-out infinite alternate both}
@keyframes shim{from{transform:translateX(-6px);opacity:.25}to{transform:translateX(6px);opacity:.85}}
.fadeup{animation:fadeup 1.4s cubic-bezier(.22,1,.36,1) both}
@keyframes fadeup{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}
"""


def esc(text):
    return escape(str(text), quote=True)


def svg_doc(w, h, body, css="", defs="", title=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">'
        f"<title>{esc(title)}</title><style>{BASE_CSS}{css}</style>"
        f'<defs><clipPath id="card"><rect width="{w}" height="{h}" rx="{RADIUS}"/></clipPath>'
        f"{defs}</defs>"
        f'<g clip-path="url(#card)">{body}</g>'
        f'<rect x=".75" y=".75" width="{w-1.5}" height="{h-1.5}" rx="{RADIUS}" fill="none" '
        f'stroke="#ffffff" stroke-opacity=".14" stroke-width="1.5"/></svg>'
    )


def sky_defs(h, horizon):
    stop = horizon / h
    return (
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#02040b"/>'
        f'<stop offset="{stop*0.55:.3f}" stop-color="#081230"/>'
        f'<stop offset="{stop*0.9:.3f}" stop-color="#1b1d4d"/>'
        f'<stop offset="{stop:.3f}" stop-color="#3b2552"/>'
        f'<stop offset="{min(stop+0.001,1):.3f}" stop-color="#0b1431"/>'
        '<stop offset="1" stop-color="#01030a"/></linearGradient>'
        '<radialGradient id="glow" cx=".5" cy=".5" r=".5">'
        '<stop offset="0" stop-color="#ff9e57" stop-opacity=".35"/>'
        '<stop offset="1" stop-color="#ff9e57" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="moonhalo" cx=".5" cy=".5" r=".5">'
        '<stop offset="0" stop-color="#dfe8ff" stop-opacity=".45"/>'
        '<stop offset="1" stop-color="#dfe8ff" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="glass" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#ffffff" stop-opacity=".13"/>'
        '<stop offset="1" stop-color="#ffffff" stop-opacity=".04"/></linearGradient>'
    )


def stars(rng, w, top, bottom, n):
    out = []
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(top, bottom)
        r = rng.choice((0.5, 0.7, 0.9, 1.2))
        delay = rng.uniform(0, 4.5)
        out.append(f'<circle class="tw" style="animation-delay:-{delay:.2f}s" cx="{x:.1f}" '
                   f'cy="{y:.1f}" r="{r}" fill="#ffffff"/>')
    return "".join(out)


def moon(cx, cy, r):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r*4}" fill="url(#moonhalo)"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#eef2ff"/>'
            f'<circle cx="{cx+r*0.38}" cy="{cy-r*0.2}" r="{r*0.92}" fill="#0a1433" opacity=".9"/>')


def windows(rng, x, y, w, h, density=0.28, size=2.2):
    """Lit window dots inside a facade rectangle; some twinkle."""
    out = []
    step = size * 3.2
    cols, rows = int(w // step), int(h // step)
    for c in range(cols):
        for r in range(rows):
            if rng.random() > density:
                continue
            wx = x + (w - cols * step) / 2 + c * step + step / 2 - size / 2
            wy = y + 4 + r * step
            color = rng.choice(WINDOW_COLORS)
            cls = ' class="tw"' if rng.random() < 0.18 else ""
            delay = f' style="animation-delay:-{rng.uniform(0,4.5):.2f}s"' if cls else ""
            out.append(f'<rect{cls}{delay} x="{wx:.1f}" y="{wy:.1f}" width="{size}" '
                       f'height="{size*1.3:.1f}" fill="{color}" opacity="{rng.uniform(.55,.95):.2f}"/>')
    return "".join(out)


def far_skyline(rng, w, horizon, max_h, fill="#0a1029", opacity=1.0):
    out, x = [], -10.0
    while x < w + 10:
        bw = rng.uniform(18, 46)
        bh = rng.uniform(max_h * 0.25, max_h)
        out.append(f'<rect x="{x:.1f}" y="{horizon-bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{fill}"/>')
        out.append(windows(rng, x + 2, horizon - bh + 2, bw - 4, bh - 6, 0.18, 1.6))
        x += bw + rng.uniform(-4, 3)
    return f'<g opacity="{opacity}">{"".join(out)}</g>'


def river(rng, w, horizon, h, n_streaks=70):
    """Water below the horizon with shimmering light reflections."""
    out = [f'<rect x="0" y="{horizon}" width="{w}" height="{h-horizon}" fill="url(#sky)"/>',
           f'<rect x="0" y="{horizon}" width="{w}" height="1" fill="#ffd9a0" opacity=".25"/>']
    for _ in range(n_streaks):
        x = rng.uniform(0, w)
        y = rng.uniform(horizon + 4, h - 6)
        depth = (y - horizon) / max(h - horizon, 1)
        length = 6 + depth * 30 * rng.uniform(0.5, 1.4)
        color = rng.choice(WINDOW_COLORS)
        delay = rng.uniform(0, 3.2)
        out.append(f'<rect class="shim" style="animation-delay:-{delay:.2f}s" x="{x:.1f}" '
                   f'y="{y:.1f}" width="{length:.1f}" height="{1+depth*1.4:.1f}" rx="1" '
                   f'fill="{color}" opacity=".6"/>')
    return "".join(out)


def status_bar(w, y=26, time_text="9:41"):
    """iOS-like status bar: time, dynamic island, signal, wifi, battery."""
    cx = w / 2
    bars = "".join(f'<rect x="{w-150+i*6}" y="{y-3-i*2.5}" width="4" height="{5+i*2.5}" rx="1" fill="{INK}"/>'
                   for i in range(4))
    wifi = (f'<g transform="translate({w-112},{y+2})" fill="none" stroke="{INK}" stroke-width="2.2" '
            f'stroke-linecap="round"><path d="M-9 -8 Q0 -16 9 -8"/><path d="M-5.5 -4.5 Q0 -9 5.5 -4.5"/>'
            f'</g><circle cx="{w-112}" cy="{y}" r="1.8" fill="{INK}"/>')
    battery = (f'<rect x="{w-92}" y="{y-11}" width="30" height="14" rx="4.5" fill="none" stroke="{INK}" '
               f'stroke-opacity=".5" stroke-width="1.4"/><rect x="{w-89.5}" y="{y-8.5}" width="20" '
               f'height="9" rx="2.5" fill="{INK}"/><rect x="{w-60}" y="{y-6}" width="2.4" height="5" rx="1" '
               f'fill="{INK}" opacity=".5"/>')
    return (f'<text x="56" y="{y+2}" font-family="{FONT}" font-size="17" font-weight="600" '
            f'fill="{INK}">{esc(time_text)}</text>'
            f'<rect x="{cx-62}" y="{y-16}" width="124" height="34" rx="17" fill="#000"/>'
            f'<circle cx="{cx+40}" cy="{y+1}" r="5" fill="#0d1530"/>'
            f"{bars}{wifi}{battery}")


def home_indicator(w, h):
    return f'<rect x="{w/2-70}" y="{h-14}" width="140" height="5" rx="2.5" fill="#fff" opacity=".55"/>'


def glass_panel(x, y, w, h, r=24):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#glass)"/>'
            f'<rect x="{x+.5}" y="{y+.5}" width="{w-1}" height="{h-1}" rx="{r}" fill="none" '
            f'stroke="#fff" stroke-opacity=".16"/>')

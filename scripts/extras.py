"""Opening crawl, lightsaber dividers and the footer strip."""
import random

from scene import paint_space, to_data_uri
from theme import DISPLAY, MUTED, SANS, esc, svg_doc

YELLOW = "#ffe81f"
SABERS = {"blue": "#4fb4ff", "red": "#ff3b3b", "green": "#4dff7a"}

# Crawl geometry: text lies on a plane tilted away from the viewer. A line at depth z sits at
# screen y = HORIZON + K / z, is 1/z as wide and 1/z^2 as tall (foreshortening), so spacing stays even.
CRAWL_W, CRAWL_H = 1200, 560
HORIZON, K = 50, 520
Z0, Z1, FADE_FROM = 1.0, 7.5, 4.5
TRAVEL_S, GAP_S, PAUSE_S = 64, .95, 4
STEPS = 26


def _crawl_keyframes(period):
    frames = []
    travel_pct = TRAVEL_S / period * 100
    for k in range(STEPS + 1):
        z = Z0 + (Z1 - Z0) * k / STEPS
        y = HORIZON + K / z
        op = 1 if z < FADE_FROM else max(0, 1 - (z - FADE_FROM) / (Z1 - FADE_FROM))
        frames.append(f"{k/STEPS*travel_pct:.3f}%{{transform:translate(600px,{y:.1f}px) scale({1/z:.4f},{1/z**2:.4f});"
                      f"opacity:{op:.2f}}}")
    frames.append(f"{min(travel_pct+.01, 100):.3f}%,100%{{transform:translate(600px,{HORIZON + K / Z1:.1f}px) "
                  f"scale({1/Z1:.4f},{1/Z1**2:.4f});opacity:0}}")
    return "@keyframes crawl{" + "".join(frames) + "}"


def build_crawl(lines):
    """lines: list of (text, kind) where kind is 'episode', 'title', 'body' or 'gap'."""
    starts, t = [], 0.0
    for text, kind in lines:
        if kind == "gap":
            t += GAP_S * 1.2
            continue
        starts.append((text, kind, t))
        t += GAP_S * (1.6 if kind == "title" else 1.25 if kind == "episode" else 1)
    period = t + PAUSE_S + 2
    period = max(period, TRAVEL_S + 1)
    css = (f".ln{{animation:crawl {period:.2f}s linear infinite both}}" + _crawl_keyframes(period)
           + ".fadeout{animation:none}")
    out = []
    for text, kind, start in starts:
        font = DISPLAY if kind in ("episode", "title") else SANS
        size, weight, spacing = {"episode": (26, 700, 4), "title": (48, 900, 3), "body": (34, 800, .5)}[kind]
        out.append(f'<g class="ln" style="animation-delay:{start:.2f}s"><text text-anchor="middle" '
                   f'font-family="{font}" font-size="{size}" font-weight="{weight}" letter-spacing="{spacing}" '
                   f'fill="{YELLOW}">{esc(text)}</text></g>')
    bg = to_data_uri(paint_space(CRAWL_W, CRAWL_H, "crawl", stars=700), "JPEG", 78)
    defs = ('<linearGradient id="topfade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" '
            'stop-opacity=".95"/><stop offset=".28" stop-color="#000" stop-opacity="0"/></linearGradient>')
    body = (f'<image href="{bg}" width="{CRAWL_W}" height="{CRAWL_H}"/>{"".join(out)}'
            f'<rect width="{CRAWL_W}" height="{CRAWL_H}" fill="url(#topfade)"/>')
    fonts = (("Inter", 800), ("Orbitron", 700), ("Orbitron", 900))
    return svg_doc(CRAWL_W, CRAWL_H, body, css, defs, "Opening crawl: about me", fonts)


def build_saber(color_name, flip=False):
    w, h = 1200, 56
    color = SABERS[color_name]
    hx, blade_x0, blade_x1, cy = 34, 128, 1166, h / 2
    css = (f".blade{{transform-box:fill-box;transform-origin:0% 50%;animation:ignite 14s cubic-bezier(.2,.9,.2,1) infinite both}}"
           "@keyframes ignite{0%{transform:scaleX(0)}5%{transform:scaleX(1)}90%{transform:scaleX(1);"
           "animation-timing-function:cubic-bezier(.7,0,.9,.4)}95%,100%{transform:scaleX(0)}}"
           ".hum{animation:hum .11s steps(2,jump-none) infinite}@keyframes hum{0%{opacity:.85}100%{opacity:1}}")
    blade_len = blade_x1 - blade_x0
    hilt = (f'<rect x="{hx}" y="{cy-7}" width="94" height="14" rx="3" fill="url(#metal)"/>'
            + "".join(f'<rect x="{hx+10+i*7}" y="{cy-7}" width="3.2" height="14" fill="#1c1f26"/>' for i in range(6))
            + f'<rect x="{hx+60}" y="{cy-9}" width="12" height="18" rx="2" fill="#3a3f4a"/>'
            + f'<rect x="{hx+62}" y="{cy-3}" width="8" height="3" rx="1" fill="#c33"/>'
            + f'<rect x="{hx+82}" y="{cy-10}" width="12" height="20" rx="2" fill="url(#metal)"/>')
    blade = (f'<g class="blade"><g class="hum">'
             f'<rect x="{blade_x0}" y="{cy-14}" width="{blade_len}" height="28" rx="14" fill="{color}" opacity=".16" filter="url(#bl)"/>'
             f'<rect x="{blade_x0}" y="{cy-6}" width="{blade_len}" height="12" rx="6" fill="{color}" opacity=".75" filter="url(#bl2)"/>'
             f'<rect x="{blade_x0}" y="{cy-2.4}" width="{blade_len}" height="4.8" rx="2.4" fill="#fff"/></g></g>')
    defs = ('<linearGradient id="metal" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e4e8ef"/>'
            '<stop offset=".5" stop-color="#8b929e"/><stop offset="1" stop-color="#4b505a"/></linearGradient>'
            '<filter id="bl" x="-5%" y="-100%" width="110%" height="300%"><feGaussianBlur stdDeviation="7"/></filter>'
            '<filter id="bl2" x="-5%" y="-100%" width="110%" height="300%"><feGaussianBlur stdDeviation="2.5"/></filter>')
    flip_attr = f' transform="translate({w} 0) scale(-1 1)"' if flip else ""
    body = f"<g{flip_attr}>{blade}{hilt}</g>"
    return svg_doc(w, h, body, css, defs, f"{color_name} lightsaber divider", (), 0, border=False)


def build_footer(user, tie_symbol):
    w, h = 1200, 200
    css = (".fly{animation:fly 11s linear infinite}"
           "@keyframes fly{0%{transform:translate(-120px,54px) scale(.75)}100%{transform:translate(1320px,46px) scale(1.1)}}"
           ".fly2{animation:fly 11s linear infinite;animation-delay:-.7s}")
    bg = to_data_uri(paint_space(w, h, "footer", nebulae=[(900, 120, 180, 40, (60, 40, 120), .3)], stars=320),
                     "JPEG", 78)
    body = (f'<image href="{bg}" width="{w}" height="{h}"/>'
            f'<g class="fly"><use href="#tie" x="-26" y="-22" width="52" height="44"/></g>'
            f'<g class="fly2"><use href="#tie" x="-84" y="-40" width="34" height="30"/></g>'
            f'<text x="{w/2}" y="104" text-anchor="middle" font-family="{DISPLAY}" font-size="26" font-weight="900" '
            f'letter-spacing="5" fill="{YELLOW}">MAY THE SOURCE BE WITH YOU</text>'
            f'<text x="{w/2}" y="138" text-anchor="middle" font-family="{SANS}" font-size="13" letter-spacing="1.5" '
            f'fill="{MUTED}">@{esc(user)}  ·  this page rebuilds itself every day</text>')
    return svg_doc(w, h, body, css, tie_symbol, "May the source be with you",
                   (("Inter", 400), ("Orbitron", 900)))

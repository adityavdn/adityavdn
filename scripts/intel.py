"""Two half-width HUD cards: a language hologram and a transmission log of recent activity."""
from datetime import datetime

from scene import paint_space, to_data_uri
from theme import DISPLAY, INK, MUTED, SANS, esc, svg_doc

W, H = 590, 320
RADIUS = 22
CYAN = "#6fd6ff"
FONTS = (("Inter", 400), ("Inter", 600), ("Orbitron", 700))
TAGS = {"PUSH": "#6fd6ff", "NEW REPO": "#3ddc84", "PR": "#b48cff", "RELEASE": "#ffa94d",
        "ISSUE": "#ff6b6b", "FORK": "#a9b2c7", "STARRED": "#ffe81f"}

BASE_CSS = """
.in{animation:in .7s cubic-bezier(.16,1,.3,1) both}
@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}
.flick{animation:flick 6s steps(1,end) infinite}
@keyframes flick{0%,100%{opacity:1}92%{opacity:.82}93%{opacity:1}96%{opacity:.9}97%{opacity:1}}
.cursor{animation:tw 1s steps(2,jump-none) infinite}
"""
DEFS = ('<pattern id="lines" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" '
        'fill="#fff" opacity=".035"/></pattern>'
        '<filter id="glow" x="-10%" y="-80%" width="120%" height="260%"><feGaussianBlur stdDeviation="3"/></filter>')


def _brackets(x, y, w, h, n=14):
    p = (f"M{x} {y+n}V{y}H{x+n} M{x+w-n} {y}H{x+w}V{y+n} M{x+w} {y+h-n}V{y+h}H{x+w-n} "
         f"M{x+n} {y+h}H{x}V{y+h-n}")
    return f'<path d="{p}" fill="none" stroke="{CYAN}" stroke-opacity=".7" stroke-width="1.5"/>'


def _frame(seed, title, right):
    bg = to_data_uri(paint_space(W, H, seed, nebulae=[(470, 60, 140, 50, (40, 90, 150), .3),
                                                      (120, 280, 140, 40, (120, 40, 90), .2)], stars=180), "JPEG", 80)
    return (f'<image href="{bg}" width="{W}" height="{H}"/>'
            f'<rect width="{W}" height="{H}" fill="#03060d" opacity=".5"/><rect width="{W}" height="{H}" fill="url(#lines)"/>'
            + _brackets(10, 10, W - 20, H - 20)
            + f'<text x="30" y="46" font-family="{DISPLAY}" font-size="14" font-weight="700" letter-spacing="2.6" '
              f'fill="{INK}">{esc(title)}</text>'
              f'<text x="{W-30}" y="46" text-anchor="end" font-family="{SANS}" font-size="11" font-weight="600" '
              f'letter-spacing="2" fill="{CYAN}">{esc(right)}</text>'
              f'<rect x="30" y="60" width="{W-60}" height="1" fill="{CYAN}" opacity=".3"/>')


def build_languages(langs):
    if not langs:
        return None
    top = max(l.repos for l in langs)
    x0, bar_x, bar_w, row_h, y0 = 30, 190, 250, 38, 100
    rows = []
    for i, l in enumerate(langs):
        y = y0 + i * row_h
        w = max(6, bar_w * l.repos / top)
        pct = f"{l.share*100:.1f}%" if l.share >= .001 else "under 0.1%"
        d = f"{.15+i*.12:.2f}"
        rows.append(
            f'<g class="in" style="animation-delay:{d}s">'
            f'<circle cx="{x0+5}" cy="{y-5}" r="5" fill="{l.color}"/>'
            f'<text x="{x0+18}" y="{y}" font-family="{SANS}" font-size="14" font-weight="600" fill="{INK}">{esc(l.name)}</text>'
            f'<rect x="{bar_x}" y="{y-11}" width="{bar_w}" height="10" rx="5" fill="#fff" opacity=".06"/>'
            f'<g class="flick"><rect class="bar" style="animation-delay:{d}s" x="{bar_x}" y="{y-11}" width="{w:.1f}" height="10" rx="5" '
            f'fill="{l.color}" opacity=".55" filter="url(#glow)"/>'
            f'<rect class="bar" style="animation-delay:{d}s" x="{bar_x}" y="{y-11}" width="{w:.1f}" height="10" rx="5" fill="url(#holo{i})"/></g>'
            f'<text x="{W-30}" y="{y-1}" text-anchor="end" font-family="{SANS}" font-size="13" font-weight="600" fill="{INK}">'
            f'{l.repos} repos</text>'
            f'<text x="{W-30}" y="{y+13}" text-anchor="end" font-family="{SANS}" font-size="10.5" fill="{MUTED}">{esc(pct)} of code</text>'
            f'</g>')
    grads = "".join(f'<linearGradient id="holo{i}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{l.color}"/>'
                    f'<stop offset="1" stop-color="{CYAN}"/></linearGradient>' for i, l in enumerate(langs))
    sweep = (f'<rect class="sweep" x="{bar_x}" y="{y0-16}" width="60" height="{row_h*len(langs)}" fill="url(#sweepfill)" '
             f'clip-path="url(#bars)"/>')
    clip = (f'<clipPath id="bars"><rect x="{bar_x}" y="{y0-16}" width="{bar_w}" height="{row_h*len(langs)}"/></clipPath>'
            '<linearGradient id="sweepfill" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            '<stop offset=".5" stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    css = (BASE_CSS + ".bar{transform-box:fill-box;transform-origin:0 50%;animation:grow 1.3s cubic-bezier(.16,1,.3,1) both}"
           "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
           f".sweep{{animation:sweep 5s ease-in-out infinite}}@keyframes sweep{{from{{transform:translateX(-80px)}}"
           f"to{{transform:translateX({bar_w+40}px)}}}}")
    body = _frame("langs", "LANGUAGE HOLOGRAM", "USED IN · PUBLIC REPOS") + "".join(rows) + sweep
    return svg_doc(W, H, body, css, DEFS + grads + clip, "Languages across my public repositories", FONTS, RADIUS)


def _fit(text, chars):
    return text if len(text) <= chars else text[:chars - 1].rstrip(" .,;:-") + "…"


def build_activity(events):
    if not events:
        return None
    y0, row_h = 96, 34
    rows = []
    for i, e in enumerate(events):
        y = y0 + i * row_h
        color = TAGS.get(e.kind, CYAN)
        tag_w = 12 + len(e.kind) * 7
        when = datetime.fromisoformat(e.when.replace("Z", "+00:00")).strftime("%d %b").upper()
        repo = _fit(e.repo, 30)
        rows.append(
            f'<g class="in" style="animation-delay:{.2+i*.28:.2f}s">'
            f'<text x="30" y="{y}" font-family="{SANS}" font-size="11" font-weight="600" letter-spacing="1" fill="{MUTED}">{when}</text>'
            f'<rect x="82" y="{y-12}" width="{tag_w}" height="17" rx="8.5" fill="{color}" fill-opacity=".14" '
            f'stroke="{color}" stroke-opacity=".6"/>'
            f'<text x="{82+tag_w/2}" y="{y+.5}" text-anchor="middle" font-family="{SANS}" font-size="9.5" font-weight="600" '
            f'letter-spacing="1" fill="{color}">{esc(e.kind)}</text>'
            f'<text x="{92+tag_w}" y="{y}" font-family="{SANS}" font-size="13" font-weight="600" fill="{INK}">{esc(repo)}</text>'
            f'<text x="{92+tag_w}" y="{y+15}" font-family="{SANS}" font-size="11.5" fill="#aab3c6">'
            f'{esc(_fit(e.text, 64 - len(e.kind)))}</text></g>')
    cy = y0 + len(events) * row_h - 6
    cursor = (f'<g class="in" style="animation-delay:{.2+len(events)*.28:.2f}s"><text x="30" y="{cy}" font-family="{SANS}" '
              f'font-size="11" letter-spacing="1" fill="{CYAN}">END OF TRANSMISSION</text>'
              f'<rect class="cursor" x="186" y="{cy-10}" width="7" height="12" fill="{CYAN}"/></g>')
    body = _frame("log", "TRANSMISSION LOG", "LATEST PUBLIC ACTIVITY") + "".join(rows) + cursor
    return svg_doc(W, H, body, BASE_CSS, DEFS, "Latest public GitHub activity", FONTS, RADIUS)

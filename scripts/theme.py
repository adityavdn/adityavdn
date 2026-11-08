"""Shared SVG plumbing: document wrapper, embedded fonts, escaping."""
import base64
from functools import lru_cache
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"
SANS = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif"
DISPLAY = "Orbitron, 'Arial Black', Inter, sans-serif"
MONO = "'SF Mono', ui-monospace, Menlo, Consolas, monospace"
INK = "#f3f5fb"
MUTED = "#a9b2c7"
AMBER = "#f5b544"
RADIUS = 28

FONT_FILES = {
    ("Inter", 400): "inter-latin-400-normal.woff2",
    ("Inter", 600): "inter-latin-600-normal.woff2",
    ("Inter", 800): "inter-latin-800-normal.woff2",
    ("Orbitron", 700): "orbitron-latin-700-normal.woff2",
    ("Orbitron", 900): "orbitron-latin-900-normal.woff2",
}

BASE_CSS = """
.tw{animation:tw 5s ease-in-out infinite both}
@keyframes tw{0%,100%{opacity:.2}50%{opacity:1}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}
"""


def esc(text):
    return escape(str(text), quote=True)


@lru_cache(maxsize=None)
def font_face(family, weight):
    path = FONT_DIR / FONT_FILES[(family, weight)]
    if not path.exists():
        print(f"Font missing, using system fallback: {path.name}")
        return ""
    b64 = base64.b64encode(path.read_bytes()).decode()
    return (f"@font-face{{font-family:{family};font-weight:{weight};font-style:normal;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")


def svg_doc(w, h, body, css="", defs="", title="", fonts=(), radius=RADIUS, border=True):
    faces = "".join(font_face(f, wt) for f, wt in fonts)
    edge = (f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="{radius}" fill="none" '
            f'stroke="#ffffff" stroke-opacity=".12"/>') if border else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">'
        f"<title>{esc(title)}</title><style>{faces}{BASE_CSS}{css}</style>"
        f'<defs><clipPath id="card"><rect width="{w}" height="{h}" rx="{radius}"/></clipPath>{defs}</defs>'
        f'<g clip-path="url(#card)">{body}</g>{edge}</svg>'
    )


def twinkles(rng, w, top, bottom, n, avoid=None):
    out = []
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(top, bottom)
        if avoid and (x - avoid[0]) ** 2 + (y - avoid[1]) ** 2 < avoid[2] ** 2:
            continue
        out.append(f'<circle class="tw" style="animation-delay:-{rng.uniform(0, 5):.2f}s" '
                   f'cx="{x:.1f}" cy="{y:.1f}" r="{rng.choice((.6, .8, 1.1))}" fill="#fff"/>')
    return "".join(out)

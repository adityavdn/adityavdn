"""Paint deep-space backdrops as rasters (nebula and planet glow need real blur)."""
import base64
import io
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 2  # paint at 2x, then downsample


def _blobs(size, pts, color, alpha, blur):
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    for x, y, r, a in pts:
        d.ellipse([x - r, y - r, x + r, y + r], fill=int(255 * a))
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    layer = Image.new("RGBA", size, color + (0,))
    layer.putalpha(mask.point(lambda v: int(v * alpha)))
    return layer


def _nebula(rng, size, cx, cy, spread, color, alpha, n=60):
    pts = [(cx + rng.gauss(0, spread[0]), cy + rng.gauss(0, spread[1]), rng.uniform(20, 90) * S, rng.uniform(.3, 1))
           for _ in range(n)]
    return _blobs(size, pts, color, alpha, 38 * S)


def _stars(img, rng, n, w, h):
    d = ImageDraw.Draw(img)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for _ in range(n):
        x, y = rng.uniform(0, w) * S, rng.uniform(0, h) * S
        v = rng.randint(110, 255)
        tint = rng.choice(((0, 0, 0), (0, 10, 30), (30, 10, 0), (0, 0, 20)))
        col = (min(255, v + tint[0]), min(255, v + tint[1]), min(255, v + tint[2]), 255)
        r = rng.choice((.5, .6, .7, .9, 1.2)) * S
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
        if r > 1.0 * S and rng.random() < .35:
            gd.ellipse([x - 5 * S, y - 5 * S, x + 5 * S, y + 5 * S], fill=(170, 200, 255, 90))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(3 * S)))


def _planet(img, cx, cy, r, base, light_dir=(.78, -.5, -.18)):
    """Banded planet lit from one side, with an atmosphere rim."""
    w, h = img.size
    cx, cy, r = cx * S, cy * S, r * S
    x0, y0 = int(max(cx - r * 1.2, 0)), int(max(cy - r * 1.2, 0))
    x1, y1 = int(min(cx + r * 1.2, w)), int(min(cy + r * 1.2, h))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    nx, ny = (xx - cx) / r, (yy - cy) / r
    d2 = nx ** 2 + ny ** 2
    inside = d2 <= 1
    nz = np.sqrt(np.clip(1 - d2, 0, 1))
    norm = math.sqrt(sum(v * v for v in light_dir))
    lx, ly, lz = (v / norm for v in light_dir)
    lam = np.clip(nx * lx + ny * ly + nz * lz, 0, 1)
    bands = (.78 + .14 * np.sin(ny * 19 + np.sin(nx * 4 + ny * 3) * 1.6) + .08 * np.sin(ny * 57 + nx * 2)
             + .05 * np.sin(ny * 131 + np.sin(nx * 9) * 2))
    col = np.zeros(nx.shape + (4,), np.float32)
    for c in range(3):
        col[..., c] = base[c] * bands * (.035 + 1.25 * lam ** 1.1)
    col[..., 3] = np.where(inside, 255, 0)
    planet = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGBA")
    rim = np.exp(-((np.sqrt(d2) - 1) / .03) ** 2) * (.08 + 1.1 * np.clip(nx * lx + ny * ly + .1, 0, 1))
    atm = np.zeros(nx.shape + (4,), np.float32)
    atm[..., 0], atm[..., 1], atm[..., 2] = 255, 170, 120
    atm[..., 3] = np.clip(rim * 255, 0, 255)
    atm_img = Image.fromarray(atm.astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(4 * S))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    layer.alpha_composite(planet, (x0, y0))
    layer.alpha_composite(atm_img, (x0, y0))
    img.alpha_composite(layer)


def paint_space(w, h, seed, planet=None, nebulae=None, stars=900):
    """planet: (cx, cy, r, rgb) in card units; nebulae: [(cx, cy, sx, sy, rgb, alpha)]."""
    rng = random.Random(seed)
    size = (w * S, h * S)
    ys = np.linspace(0, 1, size[1])[:, None, None]
    top, bot = np.array([3, 5, 14]), np.array([7, 10, 24])
    sky = np.repeat(top + (bot - top) * ys, size[0], axis=1)
    img = Image.fromarray(sky.astype(np.uint8), "RGB").convert("RGBA")
    for cx, cy, sx, sy, rgb, a in nebulae or ():
        img.alpha_composite(_nebula(rng, size, cx * S, cy * S, (sx * S, sy * S), rgb, a))
    _stars(img, rng, stars, w, h)
    if planet:
        _planet(img, *planet)
    out = img.convert("RGB")
    target = 1600 if w >= 1000 else w * 2
    return out.resize((target, round(target * h / w)), Image.LANCZOS)


def to_data_uri(img, fmt="JPEG", quality=82):
    buf = io.BytesIO()
    kwargs = {"quality": quality}
    if fmt == "JPEG":
        kwargs.update(optimize=True, progressive=True)
    img.save(buf, fmt, **kwargs)
    mime = {"JPEG": "image/jpeg", "WEBP": "image/webp", "PNG": "image/png"}[fmt]
    return f"data:{mime};base64,{base64.b64encode(buf.getvalue()).decode()}"


CITY_SPACE = dict(
    planet=(150, 900, 380, (190, 110, 80)),
    nebulae=[(260, 120, 220, 70, (110, 50, 160), .38), (1000, 330, 160, 110, (30, 110, 150), .3),
             (700, 60, 200, 40, (150, 40, 70), .22)],
)

if __name__ == "__main__":
    paint_space(1200, 800, "city", **CITY_SPACE).save("space-preview.jpg", quality=88)

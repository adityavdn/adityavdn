"""Paint the moonlit mountain backdrop for the city card as a raster (soft mist needs blur)."""
import base64
import io
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1200, 652          # card units
S = 2                     # paint at 2x, then downsample
OUT_W = 1600
MOON = (1065, 105, 44)    # x, y, r in card units


def _gradient(stops, h, w):
    ys = np.linspace(0, 1, h)
    cols = np.zeros((h, 3))
    for c in range(3):
        cols[:, c] = np.interp(ys, [s for s, _ in stops], [rgb[c] for _, rgb in stops])
    return np.repeat(cols[:, None, :], w, axis=1)


def _ridge(rng, base, amp, rough=0.55, n=8, start=7):
    """Midpoint-displacement profile over the card width, in card units."""
    pts = [base + rng.uniform(-amp, amp) for _ in range(start)]
    spread = amp * .5
    for _ in range(n):
        nxt = []
        for a, b in zip(pts, pts[1:]):
            nxt += [a, (a + b) / 2 + rng.uniform(-spread, spread)]
        pts = nxt + [pts[-1]]
        spread *= rough
    xs = np.linspace(0, W, len(pts))
    return xs, np.array(pts)


def _layer(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _fill_ridge(img, xs, ys, top_rgb, bot_rgb, rim_rgb=None):
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    poly = [(x * S, y * S) for x, y in zip(xs, ys)] + [(w, h), (0, h)]
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    top = int(min(ys) * S)
    grad = _gradient([(0, top_rgb), (1, bot_rgb)], h - top, w).astype(np.uint8)
    body = np.zeros((h, w, 3), np.uint8)
    body[top:] = grad
    layer = Image.fromarray(body, "RGB").convert("RGBA")
    layer.putalpha(mask)
    img.alpha_composite(layer)
    if rim_rgb:
        rim = _layer((w, h))
        ImageDraw.Draw(rim).line([(x * S, y * S) for x, y in zip(xs, ys)], fill=rim_rgb + (110,), width=3)
        img.alpha_composite(rim.filter(ImageFilter.GaussianBlur(2)))


def _soft_blobs(size, blobs, color, alpha, blur):
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    for x, y, rx, ry, a in blobs:
        d.ellipse([(x - rx) * S, (y - ry) * S, (x + rx) * S, (y + ry) * S], fill=int(255 * a))
    mask = mask.filter(ImageFilter.GaussianBlur(blur * S))
    layer = Image.new("RGBA", size, color + (0,))
    layer.putalpha(mask.point(lambda v: int(v * alpha)))
    return layer


def _clouds(rng, size):
    blobs = []
    for cx, cy, spread, n in ((930, 150, 150, 26), (1150, 205, 70, 12), (380, 70, 170, 14), (700, 120, 90, 8)):
        for _ in range(n):
            blobs.append((cx + rng.uniform(-spread, spread), cy + rng.uniform(-14, 14),
                          rng.uniform(22, 60), rng.uniform(6, 14), rng.uniform(.5, 1)))
    return _soft_blobs(size, blobs, (112, 130, 172), .42, 9)


def _moon(img):
    x, y, r = (v * S for v in MOON)
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.hypot(xx - x, yy - y)
    halo = .5 * np.exp(-(dist / (r * 2.6)) ** 2) + .22 * np.exp(-(dist / (r * 8)) ** 2)
    glow = np.zeros((h, w, 4), np.uint8)
    glow[..., :3] = (200, 212, 255)
    glow[..., 3] = np.clip(halo * 255, 0, 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(glow, "RGBA"))
    rng = random.Random(7)
    size = int(r * 2) + 2
    disk = np.zeros((size, size, 4), np.uint8)
    dy, dx = np.mgrid[0:size, 0:size]
    rr = np.hypot(dx - size / 2, dy - size / 2) / r
    shade = 1 - .28 * rr ** 2
    disk[..., 0] = np.clip(240 * shade, 0, 255)
    disk[..., 1] = np.clip(234 * shade, 0, 255)
    disk[..., 2] = np.clip(212 * shade, 0, 255)
    disk[..., 3] = np.clip((1 - rr) * r * 1.5, 0, 1) * 255
    moon = Image.fromarray(disk, "RGBA")
    maria = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(maria)
    for _ in range(16):
        cx, cy, cr = rng.uniform(.2, .8) * size, rng.uniform(.2, .8) * size, rng.uniform(.04, .16) * size
        md.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=rng.randint(40, 90))
    maria = maria.filter(ImageFilter.GaussianBlur(3))
    dark = Image.new("RGBA", (size, size), (120, 116, 104, 0))
    dark.putalpha(Image.fromarray(np.minimum(np.asarray(maria), np.asarray(moon.getchannel("A")))))
    moon.alpha_composite(dark)
    img.alpha_composite(moon, (int(x - size / 2), int(y - size / 2)))


def _pine(d, x, base, h, color):
    w = h * .42
    for i in range(4):
        t = i / 4
        top = base - h * (1 - t * .55)
        half = w * (.45 + t * .55) / 2
        d.polygon([(x * S, top * S), ((x + half) * S, (top + h * .36) * S), ((x - half) * S, (top + h * .36) * S)],
                  fill=color)
    d.rectangle([(x - h * .03) * S, (base - h * .08) * S, (x + h * .03) * S, base * S], fill=color)


def _forest(img, rng, xs, ys, count, hmin, hmax, color, drop=4):
    d = ImageDraw.Draw(img)
    for _ in range(count):
        x = rng.uniform(0, W)
        y = float(np.interp(x, xs, ys)) + rng.uniform(0, drop)
        _pine(d, x, y + hmax * .25, rng.uniform(hmin, hmax), color)


def _castle(img, x, base, scale, rng):
    d = ImageDraw.Draw(img)
    body = (24, 31, 52, 255)
    towers = [(-34, 40, 9), (-18, 62, 11), (0, 92, 13), (18, 58, 11), (34, 44, 9), (-48, 30, 7), (48, 34, 7)]
    lights = []
    for dx, th, tw in towers:
        cx, top = x + dx * scale, base - th * scale
        d.rectangle([(cx - tw * scale / 2) * S, top * S, (cx + tw * scale / 2) * S, base * S], fill=body)
        d.polygon([((cx - tw * scale * .62) * S, top * S), (cx * S, (top - tw * scale * 1.5) * S),
                   ((cx + tw * scale * .62) * S, top * S)], fill=body)
        for _ in range(int(th / 22)):
            lights.append((cx + rng.uniform(-tw, tw) * scale * .3, rng.uniform(top + 4, base - 4)))
    d.rectangle([(x - 50 * scale) * S, (base - 22 * scale) * S, (x + 50 * scale) * S, base * S], fill=body)
    for _ in range(6):
        lights.append((x + rng.uniform(-46, 46) * scale, base - rng.uniform(4, 18) * scale))
    _lamps(img, lights, (255, 178, 84), .55 * scale + .35)


def _lamps(img, pts, color, r):
    glow = _layer(img.size)
    gd = ImageDraw.Draw(glow)
    for x, y in pts:
        gd.ellipse([(x - r * 4) * S, (y - r * 4) * S, (x + r * 4) * S, (y + r * 4) * S], fill=color + (70,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(4 * S)))
    d = ImageDraw.Draw(img)
    for x, y in pts:
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(255, 214, 140, 255))


def _aqueduct(img):
    d = ImageDraw.Draw(img)
    x0, x1, y0 = 960, 1210, 330
    col = (12, 20, 38, 255)
    d.polygon([(x0 * S, y0 * S), (x1 * S, (y0 + 16) * S), (x1 * S, (y0 + 52) * S), (x0 * S, (y0 + 44) * S)], fill=col)
    span = 26
    x = x0 + 6
    while x < x1:
        top = y0 + 14 + (x - x0) / (x1 - x0) * 16
        d.ellipse([(x + 3) * S, top * S, (x + span - 3) * S, (top + 26) * S], fill=(26, 36, 62, 255))
        d.rectangle([(x + 3) * S, (top + 13) * S, (x + span - 3) * S, (top + 38) * S], fill=(22, 31, 55, 255))
        x += span
    _lamps(img, [(x0 + i * 13, y0 - 1 + i * 13 * 16 / (x1 - x0)) for i in range(20)], (255, 170, 80), 1.3)


def _rocks(img, rng):
    d = ImageDraw.Draw(img)
    for cx, cy, rw, rh in ((60, 610, 120, 70), (190, 640, 140, 60), (330, 655, 110, 40), (10, 560, 70, 60)):
        pts = []
        for i in range(9):
            a = math.pi + i / 8 * math.pi
            pts.append(((cx + math.cos(a) * rw * rng.uniform(.8, 1.1)) * S,
                        (cy + math.sin(a) * rh * rng.uniform(.75, 1.1)) * S))
        d.polygon(pts + [((cx + rw) * S, H * S), ((cx - rw) * S, H * S)], fill=(20, 24, 33, 255))
        d.line(pts[4:8], fill=(70, 78, 96, 255), width=2 * S)


def paint_backdrop(seed="moonlit-city"):
    rng = random.Random(seed)
    size = (W * S, H * S)
    sky = _gradient([(0, (4, 8, 20)), (.35, (9, 18, 44)), (.6, (17, 32, 66)), (1, (10, 18, 38))], size[1], size[0])
    img = Image.fromarray(sky.astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(img)
    for _ in range(260):
        x, y = rng.uniform(0, W), rng.uniform(0, H * .5)
        if math.hypot(x - MOON[0], y - MOON[1]) < 90:
            continue
        v = rng.randint(120, 255)
        r = rng.choice((.5, .6, .8, 1.0))
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(v, v, min(255, v + 20), 255))
    _moon(img)
    img.alpha_composite(_clouds(rng, size))

    peaks = _ridge(rng, 215, 85, .58, 8, 9)
    _fill_ridge(img, peaks[0], peaks[1], (44, 58, 96), (24, 34, 62), (140, 160, 205))
    img.alpha_composite(_soft_blobs(size, [(x, 262 + rng.uniform(-8, 8), 140, 12, .8)
                                           for x in range(0, W + 140, 120)], (150, 170, 210), .16, 12))
    far = _ridge(rng, 272, 40)
    fy = far[1].copy()
    fy -= 75 * np.exp(-((far[0] - 990) / 105) ** 2)         # the castle hill
    _fill_ridge(img, far[0], fy, (34, 47, 82), (18, 28, 52), (110, 130, 175))
    _castle(img, 990, float(fy[np.abs(far[0] - 990) < 45].max()) + 2, .8, rng)
    img.alpha_composite(_soft_blobs(size, [(x, 300 + rng.uniform(-8, 8), 140, 14, .8)
                                           for x in range(0, W + 140, 120)], (150, 170, 210), .2, 14))
    mid = _ridge(rng, 318, 44)
    my = mid[1] - 40 * np.exp(-((mid[0] - 1135) / 75) ** 2)
    _fill_ridge(img, mid[0], my, (24, 36, 64), (13, 21, 40), (80, 98, 140))
    _castle(img, 1135, float(my[np.abs(mid[0] - 1135) < 26].max()) + 2, .5, rng)
    _forest(img, rng, mid[0], my, 120, 8, 16, (12, 20, 37, 255))
    _aqueduct(img)
    img.alpha_composite(_soft_blobs(size, [(x, 372 + rng.uniform(-10, 10), 160, 18, .9)
                                           for x in range(0, W + 160, 130)], (150, 170, 210), .22, 16))
    near = _ridge(rng, 400, 26)
    _fill_ridge(img, near[0], near[1], (14, 22, 40), (8, 12, 24), (60, 75, 110))
    _forest(img, rng, near[0], near[1], 170, 14, 30, (8, 13, 26, 255), 30)
    img.alpha_composite(_soft_blobs(size, [(x, 520 + rng.uniform(-14, 14), 180, 30, 1)
                                           for x in range(0, W + 180, 140)], (120, 140, 185), .2, 20))
    dfg = ImageDraw.Draw(img)
    for x, hgt in ((450, 230), (520, 180), (585, 150), (400, 120), (640, 110)):
        _pine(dfg, x, H + 8, hgt, (5, 9, 18, 255))
    _rocks(img, rng)

    arr = np.asarray(img.convert("RGB")).astype(float)
    yy, xx = np.mgrid[0:size[1], 0:size[0]]
    vig = 1 - .45 * (((xx / size[0] - .55) ** 2) * 1.2 + ((yy / size[1] - .45) ** 2) * 1.6)
    arr *= np.clip(vig, .45, 1)[..., None]
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    return out.resize((OUT_W, round(OUT_W * H / W)), Image.LANCZOS)


def mist_strip(seed="mist", w=1500, h=150):
    """Soft transparent wisps that drift across the valley."""
    rng = random.Random(seed)
    blobs = [(x, h / 2 + rng.uniform(-20, 20), rng.uniform(60, 140), rng.uniform(10, 22), rng.uniform(.4, 1))
             for x in range(0, w, 60)]
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    for x, y, rx, ry, a in blobs:
        d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=int(255 * a))
    layer = Image.new("RGBA", (w, h), (170, 188, 225, 0))
    layer.putalpha(mask.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * .32)))
    return layer


def to_data_uri(img, fmt="JPEG", quality=82):
    buf = io.BytesIO()
    kwargs = {"quality": quality}
    if fmt == "JPEG":
        kwargs.update(optimize=True, progressive=True)
    img.save(buf, fmt, **kwargs)
    mime = {"JPEG": "image/jpeg", "WEBP": "image/webp", "PNG": "image/png"}[fmt]
    return f"data:{mime};base64,{base64.b64encode(buf.getvalue()).decode()}"


if __name__ == "__main__":
    paint_backdrop().save("backdrop-preview.jpg", quality=88)

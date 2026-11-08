"""One-off: cut the building images into small transparent WebP sprites."""
import sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

SRC = Path(sys.argv[1]); OUT = Path(sys.argv[2])
SPRITE_H = 300  # px; displayed at most ~170px, so ~1.8x for retina

def strip_dark_bg(im):
    a = np.asarray(im.convert("RGB")).astype(int)
    h, w, _ = a.shape
    lum = a.mean(axis=2); sat = a.max(axis=2) - a.min(axis=2)
    bgish = (lum < 78) & (sat < 34)
    seen = np.zeros((h, w), bool); q = deque()
    for x in range(w):
        for y in (0, h - 1): q.append((y, x))
    for y in range(h):
        for x in (0, w - 1): q.append((y, x))
    while q:
        y, x = q.popleft()
        if seen[y, x] or not bgish[y, x]: continue
        seen[y, x] = True
        for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ny, nx = y+dy, x+dx
            if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx]: q.append((ny, nx))
    alpha = np.where(seen, 0, 255).astype(np.uint8)
    rgba = np.dstack([a.astype(np.uint8), alpha])
    return Image.fromarray(rgba, "RGBA")

OUT.mkdir(parents=True, exist_ok=True)
for i, n in enumerate(range(4, 11), start=1):
    im = Image.open(SRC / f"{n}.webp").convert("RGBA")
    if n == 10:
        im = strip_dark_bg(im)
        # drop the floor reflection under the plinth
        im = im.crop((0, 0, im.width, int(im.height * 0.955)))
    bbox = im.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    im = im.crop(bbox)
    im = im.resize((round(im.width * SPRITE_H / im.height), SPRITE_H), Image.LANCZOS)
    path = OUT / f"b{i}.webp"
    im.save(path, "WEBP", quality=82, method=6)
    print(path.name, im.size, path.stat().st_size, "bytes")

"""One-off: cut the sci-fi building strip into transparent WebP sprites (sprites/b1..b8)."""
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

SPRITE_H = 360
THRESH = 232


def columns(white):
    col = (~white).sum(axis=0)
    runs, start = [], None
    for x, v in enumerate(col):
        if v > 3 and start is None:
            start = x
        elif v <= 3 and start is not None:
            runs.append((start, x))
            start = None
    if start is not None:
        runs.append((start, len(col)))
    # the last two towers touch; split the widest run at its thinnest column
    out = []
    widths = [b - a for a, b in runs]
    median = sorted(widths)[len(widths) // 2]
    for a, b in runs:
        if b - a > median * 1.6:
            mid = a + (b - a) // 2
            lo, hi = mid - (b - a) // 6, mid + (b - a) // 6
            cut = lo + int(np.argmin(col[lo:hi]))
            out += [(a, cut), (cut, b)]
        else:
            out.append((a, b))
    return out


def cut_out(rgb):
    a = np.asarray(rgb).astype(int)
    h, w, _ = a.shape
    bg = a.min(axis=2) > THRESH
    seen = np.zeros((h, w), bool)
    q = deque([(y, x) for x in range(w) for y in (0, h - 1)] + [(y, x) for y in range(h) for x in (0, w - 1)])
    while q:
        y, x = q.popleft()
        if not (0 <= y < h and 0 <= x < w) or seen[y, x] or not bg[y, x]:
            continue
        seen[y, x] = True
        q.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    alpha = Image.fromarray(np.where(seen, 0, 255).astype(np.uint8), "L")
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(.8))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def main(src, out_dir):
    im = Image.open(src).convert("RGB")
    white = np.asarray(im).min(axis=2) > THRESH
    out_dir = Path(out_dir)
    for old in out_dir.glob("b*.webp"):
        old.unlink()
    for i, (a, b) in enumerate(columns(white), start=1):
        piece = cut_out(im.crop((max(a - 4, 0), 0, min(b + 4, im.width), im.height)))
        piece = piece.crop(piece.getchannel("A").point(lambda v: 255 if v > 30 else 0).getbbox())
        piece = piece.resize((round(piece.width * SPRITE_H / piece.height), SPRITE_H), Image.LANCZOS)
        path = out_dir / f"b{i}.webp"
        piece.save(path, "WEBP", quality=84, method=6)
        print(path.name, piece.size, path.stat().st_size)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

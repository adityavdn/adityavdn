"""One-off: cut the city sheet into tower sprites, the platform and the space backdrop.

python scripts/prep_city.py sheet.webp
Writes sprites/b*.webp (towers at their true relative size), assets/platform.webp, assets/space.jpg.
"""
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
THRESH = 238      # studio background is 243-255; stricter keeps bright metal highlights
TOWER_ROWS = (0, 402)
PLATFORM_ROWS = (406, None)
PHOTO = (1374, 69, 1991, 621)          # the space photo on the right of the sheet
ROCK = (0, 420, 270, 552)              # asteroid corner inside the photo, re-used bottom-left
BG_W, BG_H = 1200, 643


def _blobs(mask):
    """4-connected components of a boolean mask, as lists of (y, x)."""
    h, w = mask.shape
    todo = mask.copy()
    for y0, x0 in zip(*np.nonzero(mask)):
        if not todo[y0, x0]:
            continue
        blob, q = [], deque([(y0, x0)])
        todo[y0, x0] = False
        while q:
            y, x = q.popleft()
            blob.append((y, x))
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and todo[ny, nx]:
                    todo[ny, nx] = False
                    q.append((ny, nx))
        yield blob


def cut_out(rgb):
    """Make the white studio background transparent by flood-filling from the edges."""
    a = np.asarray(rgb).astype(int)
    h, w, _ = a.shape
    bg = a.min(axis=2) > THRESH
    lum = a.sum(axis=2) / 3
    seen = np.zeros((h, w), bool)
    q = deque([(y, x) for x in range(w) for y in (0, h - 1)] + [(y, x) for y in range(h) for x in (0, w - 1)])
    while q:
        y, x = q.popleft()
        if not (0 <= y < h and 0 <= x < w) or seen[y, x] or not bg[y, x]:
            continue
        seen[y, x] = True
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and abs(lum[ny, nx] - lum[y, x]) <= 4:   # backdrop is smooth
                q.append((ny, nx))
    holes = bg & ~seen                    # white gaps enclosed by pipes and struts
    for blob in _blobs(holes):
        ys_, xs_ = zip(*blob)
        box = (max(ys_) - min(ys_) + 1) * (max(xs_) - min(xs_) + 1)
        if len(blob) > 40 and len(blob) > .55 * box and max(ys_) - min(ys_) > 12:  # flat background gap, not a curved highlight
            ys, xs = zip(*blob)
            seen[list(ys), list(xs)] = True
    alpha = Image.fromarray(np.where(seen, 0, 255).astype(np.uint8), "L")
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(.8))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out.crop(alpha.point(lambda v: 255 if v > 30 else 0).getbbox())


def runs(mask_cols):
    out, start = [], None
    for x, v in enumerate(mask_cols):
        if v > 3 and start is None:
            start = x
        elif v <= 3 and start is not None:
            out.append((start, x))
            start = None
    if start is not None:
        out.append((start, len(mask_cols)))
    out = [(a, b) for a, b in out if b - a > 20]
    median = sorted(b - a for a, b in out)[len(out) // 2]
    split = []
    for a, b in out:                      # neighbours that touch: cut at the thinnest column
        if b - a > median * 1.6:
            lo, hi = a + (b - a) // 3, b - (b - a) // 3
            cut = lo + int(np.argmin(mask_cols[lo:hi]))
            split += [(a, cut), (cut, b)]
        else:
            split.append((a, b))
    return split


def towers(sheet):
    strip = sheet.crop((0, TOWER_ROWS[0], PHOTO[0] - 4, TOWER_ROWS[1]))
    white = np.asarray(strip).min(axis=2) > THRESH
    for old in (ROOT / "sprites").glob("b*.webp"):
        old.unlink()
    for i, (a, b) in enumerate(runs((~white).sum(axis=0)), start=1):
        piece = cut_out(strip.crop((max(a - 4, 0), 0, min(b + 4, strip.width), strip.height)))
        path = ROOT / "sprites" / f"b{i}.webp"
        piece.save(path, "WEBP", quality=86, method=6)
        print(path.name, piece.size)


def platform(sheet):
    piece = cut_out(sheet.crop((0, PLATFORM_ROWS[0], PHOTO[0] - 4, sheet.height)))
    piece.save(ROOT / "assets" / "platform.webp", "WEBP", quality=90, method=6)
    print("platform", piece.size)


def space(sheet):
    photo = sheet.crop(PHOTO)
    scale = BG_W / photo.width
    big = photo.resize((BG_W, round(photo.height * scale)), Image.LANCZOS)
    canvas = big.crop((0, 0, BG_W, BG_H))
    rock = photo.crop(ROCK)
    rock = rock.resize((round(rock.width * scale), round(rock.height * scale)), Image.LANCZOS)
    yy, xx = np.mgrid[0:rock.height, 0:rock.width]
    fade = np.clip(np.minimum(yy / (rock.height * .35), (rock.width - xx) / (rock.width * .3)), 0, 1)
    canvas.paste(rock, (0, BG_H - rock.height), Image.fromarray((fade * 255).astype(np.uint8), "L"))
    canvas = canvas.filter(ImageFilter.UnsharpMask(1.2, 60, 2))
    canvas.save(ROOT / "assets" / "space.jpg", quality=88, optimize=True, progressive=True)
    print("space", canvas.size)


if __name__ == "__main__":
    sheet = Image.open(sys.argv[1]).convert("RGB")
    towers(sheet)
    platform(sheet)
    space(sheet)

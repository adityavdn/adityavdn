"""Build every profile SVG and refresh the README's pinned-repo block.

python scripts/build.py --config profile.json --sprites sprites --out dist --readme README.md
"""
import argparse
import html
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cards import build_section  # noqa: E402
from city import TIE, build_city  # noqa: E402
from extras import build_crawl, build_footer, build_saber  # noqa: E402
from data import fetch_calendar, fetch_pinned, fetch_repos, token_from_env  # noqa: E402
from hero import build_hero  # noqa: E402
from stats import build_stats  # noqa: E402

RAW = "https://raw.githubusercontent.com/{user}/{user}/output"
START, END = "<!-- PINNED:START -->", "<!-- PINNED:END -->"


def pinned_block(user, repos, stamp):
    base = RAW.format(user=user)
    links = "\n".join(
        f'<a href="{r.url}"><img src="{base}/repo-{r.name}.svg?v={stamp}" width="49%" alt="{html.escape(r.name + ': ' + r.description, quote=True)}" /></a>'
        for r in repos)
    return f"{START}\n{links}\n{END}"


def bust_cache(text, user, stamp):
    """GitHub's image proxy caches by URL, so stamp every image with the build date."""
    base = re.escape(RAW.format(user=user))
    return re.sub(base + r'(/[^"?\s]+\.svg)(\?v=\d+)?', lambda m: f"{RAW.format(user=user)}{m.group(1)}?v={stamp}", text)


def update_readme(path, user, repos, stamp):
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print(f"{path} has no pinned markers; leaving it alone")
        return False
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: pinned_block(user, repos, stamp), text, flags=re.S)
    new = bust_cache(new, user, stamp)
    if new == text:
        return False
    path.write_text(new, encoding="utf-8")
    print(f"updated pinned block in {path}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="profile.json")
    ap.add_argument("--sprites", default="sprites")
    ap.add_argument("--out", default="dist")
    ap.add_argument("--readme", default=None)
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    user, token, today = cfg["user"], token_from_env(), date.today()
    seed = f"{user}-{today.isoformat()}"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    total, days = fetch_calendar(user, token)
    if not days:
        sys.exit("No contribution days returned; refusing to write an empty city")
    repos = fetch_pinned(user, token) or fetch_repos(user, cfg["fallback_repos"], token)
    if not repos:
        sys.exit("No repos found (pinned or fallback)")

    files = {
        "hero.svg": build_hero(cfg["name"], cfg["role"], cfg["tagline"], seed),
        "city.svg": build_city(user, total, days, args.sprites, seed, today),
        "stats.svg": build_stats(user, total, days, seed),
        "crawl.svg": build_crawl([tuple(l) for l in cfg["crawl"]]),
        "saber-blue.svg": build_saber("blue"),
        "saber-red.svg": build_saber("red", flip=True),
        "saber-green.svg": build_saber("green"),
        "footer.svg": build_footer(user, TIE),
        **build_section({k: [tuple(i) for i in v] for k, v in cfg["skills"].items()}, repos),
    }
    for name, svg in files.items():
        (out / name).write_text(svg, encoding="utf-8")
        print(f"wrote {name:48s} {len(svg)/1024:7.1f} KB")
    print(f"{total} contributions, {sum(d.count > 0 for d in days)} active days, "
          f"{len(repos)} repos: {', '.join(r.name for r in repos)}")
    if args.readme:
        update_readme(Path(args.readme), user, repos, datetime.now(timezone.utc).strftime("%Y%m%d%H%M"))


if __name__ == "__main__":
    main()

"""Build every profile SVG and refresh the README's pinned-repo block.

python scripts/build.py --config profile.json --sprites sprites --out dist --readme README.md
"""
import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cards import build_section  # noqa: E402
from city import build_city  # noqa: E402
from data import fetch_calendar, fetch_pinned, fetch_repos, token_from_env  # noqa: E402
from hero import build_hero  # noqa: E402

RAW = "https://raw.githubusercontent.com/{user}/{user}/output"
START, END = "<!-- PINNED:START -->", "<!-- PINNED:END -->"


def pinned_block(user, repos):
    base = RAW.format(user=user)
    links = "\n".join(
        f'<a href="{r.url}"><img src="{base}/repo-{r.name}.svg" width="49%" alt="{html.escape(r.name + ': ' + r.description, quote=True)}" /></a>'
        for r in repos)
    return f"{START}\n{links}\n{END}"


def update_readme(path, user, repos):
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print(f"{path} has no pinned markers; leaving it alone")
        return False
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: pinned_block(user, repos), text, flags=re.S)
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
        **build_section({k: [tuple(i) for i in v] for k, v in cfg["skills"].items()}, repos),
    }
    for name, svg in files.items():
        (out / name).write_text(svg, encoding="utf-8")
        print(f"wrote {name:48s} {len(svg)/1024:7.1f} KB")
    print(f"{total} contributions, {sum(d.count > 0 for d in days)} active days, "
          f"{len(repos)} repos: {', '.join(r.name for r in repos)}")
    if args.readme:
        update_readme(Path(args.readme), user, repos)


if __name__ == "__main__":
    main()

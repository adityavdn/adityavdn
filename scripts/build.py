"""Build every profile SVG: python scripts/build.py --config profile.json --out dist"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cards import build_repo, build_skills  # noqa: E402
from city import build_city  # noqa: E402
from data import fetch_calendar, fetch_repos, token_from_env  # noqa: E402
from hero import build_hero  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="profile.json")
    ap.add_argument("--sprites", default="sprites")
    ap.add_argument("--out", default="dist")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    user, token, today = cfg["user"], token_from_env(), date.today()
    seed = f"{user}-{today.isoformat()}"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    total, days = fetch_calendar(user, token)
    if not days:
        sys.exit("No contribution days returned; refusing to write an empty city")
    files = {
        "hero.svg": build_hero(cfg["name"], cfg["role"], cfg["tagline"], seed),
        "city.svg": build_city(user, total, days, args.sprites, seed, today),
        "skills.svg": build_skills(cfg["skills"], cfg["now"], seed),
    }
    for repo in fetch_repos(user, cfg["repos"], token):
        files[f"repo-{repo.name}.svg"] = build_repo(repo, seed + repo.name)

    for name, svg in files.items():
        (out / name).write_text(svg, encoding="utf-8")
        print(f"wrote {name:40s} {len(svg)/1024:7.1f} KB")
    print(f"{total} contributions, {sum(d.count > 0 for d in days)} active days")


if __name__ == "__main__":
    main()

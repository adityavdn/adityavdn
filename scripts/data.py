"""Fetch contribution calendar and repo details from GitHub."""
import json
import os
import re
import urllib.request
from dataclasses import dataclass

API = "https://api.github.com"
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
USER_AGENT = "profile-city-builder"


@dataclass(frozen=True)
class Day:
    date: str
    count: int
    level: int
    week: int
    weekday: int


@dataclass(frozen=True)
class Repo:
    name: str
    description: str
    language: str
    stars: int
    forks: int
    url: str


def _request(url, token=None, body=None, accept="application/json"):
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode()


def _calendar_graphql(user, token):
    query = """query($u:String!){user(login:$u){contributionsCollection{
      contributionCalendar{totalContributions weeks{contributionDays{
      date contributionCount contributionLevel weekday}}}}}}"""
    raw = json.loads(_request(f"{API}/graphql", token,
                              {"query": query, "variables": {"u": user}}))
    if raw.get("errors"):
        raise RuntimeError(f"GraphQL error: {raw['errors']}")
    cal = raw["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [
        Day(d["date"], d["contributionCount"], LEVELS[d["contributionLevel"]], w, d["weekday"])
        for w, week in enumerate(cal["weeks"])
        for d in week["contributionDays"]
    ]
    return cal["totalContributions"], days


def _calendar_scrape(user):
    """Public fallback that needs no token: the profile calendar fragment."""
    html = _request(f"https://github.com/users/{user}/contributions", accept="text/html")
    cells = re.findall(r'data-date="([\d-]+)"[^>]*?id="([^"]+)"[^>]*?data-level="(\d)"', html)
    counts = dict(re.findall(r'for="([^"]+)"[^>]*>(\d+|No) contribution', html))
    from datetime import date
    if not cells:
        raise RuntimeError("Could not parse the contribution calendar")
    cells.sort()
    first = date.fromisoformat(cells[0][0])
    start_offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    days = []
    for i, (d, cid, lvl) in enumerate(cells):
        n = counts.get(cid, "No")
        idx = i + start_offset
        days.append(Day(d, 0 if n == "No" else int(n), int(lvl), idx // 7, idx % 7))
    return sum(d.count for d in days), days


def fetch_calendar(user, token=None):
    if token:
        try:
            return _calendar_graphql(user, token)
        except Exception as err:  # fall through to the public page
            print(f"GraphQL failed ({err}); falling back to public calendar")
    return _calendar_scrape(user)


def fetch_repos(user, names, token=None):
    repos = []
    for name in names:
        try:
            r = json.loads(_request(f"{API}/repos/{user}/{name}", token))
        except Exception as err:
            print(f"Skipping repo {name}: {err}")
            continue
        repos.append(Repo(r["name"], r.get("description") or "", r.get("language") or "",
                          r.get("stargazers_count", 0), r.get("forks_count", 0), r["html_url"]))
    return repos


def fetch_text(url):
    try:
        return _request(url, accept="*/*")
    except Exception as err:
        print(f"Fetch failed for {url}: {err}")
        return None


def token_from_env():
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

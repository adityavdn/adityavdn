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
    color: str = ""


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


def fetch_pinned(user, token):
    """Pinned repositories in profile order (needs any token; returns [] on failure)."""
    if not token:
        return []
    query = """query($u:String!){user(login:$u){pinnedItems(first:6,types:REPOSITORY){nodes{
      ... on Repository{name description url stargazerCount forkCount primaryLanguage{name color}}}}}}"""
    try:
        raw = json.loads(_request(f"{API}/graphql", token, {"query": query, "variables": {"u": user}}))
        nodes = raw["data"]["user"]["pinnedItems"]["nodes"]
    except Exception as err:
        print(f"Pinned repos fetch failed: {err}")
        return []
    return [Repo(n["name"], n.get("description") or "",
                 (n.get("primaryLanguage") or {}).get("name", ""), n["stargazerCount"], n["forkCount"],
                 n["url"], (n.get("primaryLanguage") or {}).get("color") or "")
            for n in nodes if n]


def fetch_text(url):
    try:
        return _request(url, accept="*/*")
    except Exception as err:
        print(f"Fetch failed for {url}: {err}")
        return None


def token_from_env():
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


@dataclass(frozen=True)
class Language:
    name: str
    repos: int          # public repos that contain any of this language
    share: float        # fraction of all public code bytes
    color: str


@dataclass(frozen=True)
class Event:
    kind: str           # PUSH, NEW REPO, PR, RELEASE, STARRED, FORK, ISSUE
    repo: str
    text: str
    when: str           # ISO timestamp


def fetch_languages(user, token, limit=6):
    """Languages across the user's public, non-fork repos (needs a token; [] on failure)."""
    if not token:
        return []
    query = """query($u:String!){user(login:$u){repositories(ownerAffiliations:OWNER,isFork:false,
      privacy:PUBLIC,first:100){nodes{languages(first:10,orderBy:{field:SIZE,direction:DESC}){
      edges{size node{name color}}}}}}}"""
    try:
        raw = json.loads(_request(f"{API}/graphql", token, {"query": query, "variables": {"u": user}}))
        nodes = raw["data"]["user"]["repositories"]["nodes"]
    except Exception as err:
        print(f"Languages fetch failed: {err}")
        return []
    repos, size, color = {}, {}, {}
    for node in nodes:
        for edge in node["languages"]["edges"]:
            name = edge["node"]["name"]
            repos[name] = repos.get(name, 0) + 1
            size[name] = size.get(name, 0) + edge["size"]
            color[name] = edge["node"].get("color") or "#8b949e"
    total = sum(size.values()) or 1
    ranked = sorted(repos, key=lambda n: (-repos[n], -size[n]))[:limit]
    return [Language(n, repos[n], size[n] / total, color[n]) for n in ranked]


def _commit_message(repo, sha, token):
    try:
        c = json.loads(_request(f"{API}/repos/{repo}/commits/{sha}", token))
        return c["commit"]["message"].splitlines()[0]
    except Exception:
        return ""


def _describe(e, user, token):
    p, repo, kind = e.get("payload") or {}, e["repo"]["name"], e["type"]
    if kind == "PushEvent":
        branch = (p.get("ref") or "").replace("refs/heads/", "")
        commits = p.get("commits") or []
        msg = commits[-1]["message"].splitlines()[0] if commits else _commit_message(repo, p.get("head"), token)
        return "PUSH", msg or f"pushed to {branch}"
    if kind == "CreateEvent":
        first_branch = p.get("ref_type") == "branch" and p.get("ref") == p.get("master_branch")
        if p.get("ref_type") == "repository" or first_branch:
            return "NEW REPO", p.get("description") or "new repository launched"
        return None                          # feature branches and tags are noise here
    if kind == "PullRequestEvent":
        pr = p.get("pull_request") or {}
        action = "merged" if pr.get("merged") else p.get("action", "")
        return "PR", f"{action} #{pr.get('number', '')} {pr.get('title') or ''}".strip()
    if kind == "ReleaseEvent":
        return "RELEASE", (p.get("release") or {}).get("name") or "new release"
    if kind == "IssuesEvent":
        return "ISSUE", f"{p.get('action', '')} {(p.get('issue') or {}).get('title', '')}".strip()
    if kind == "ForkEvent":
        return "FORK", "forked for study"
    return None


def fetch_activity(user, token=None, limit=6, skip_repos=()):
    """Latest public activity, newest first. Stars are rolled into one summary line."""
    try:
        events = json.loads(_request(f"{API}/users/{user}/events/public?per_page=100", token))
    except Exception as err:
        print(f"Activity fetch failed: {err}")
        return []
    out, stars, seen = [], [], set()
    for e in events:
        repo = e["repo"]["name"]
        if e["type"] == "WatchEvent":
            stars.append(e)
            continue
        if repo in skip_repos or e["type"] == "DeleteEvent" or len(out) >= limit:
            continue
        key = (e["type"], repo)
        if key in seen:                      # one line per repo and kind keeps the log varied
            continue
        desc = _describe(e, user, token)
        if desc:
            seen.add(key)
            out.append(Event(desc[0], repo.split("/")[-1], desc[1], e["created_at"]))
    if stars:
        latest = stars[0]
        out.append(Event("STARRED", f"{len(stars)} repos", f"latest: {latest['repo']['name']}", latest["created_at"]))
    return sorted(out, key=lambda e: e.when, reverse=True)[:limit]

#!/usr/bin/env python3
"""Collect commit history for every repo of OWNER into data/activity.json.

Only commit timestamps are read (bare, blob-less clones): no file contents,
no commit messages. Private repo names are never written to the output.

env: GH_TOKEN (fine-grained PAT, Contents: read on all repos). Without it only
public repos are collected.
"""
import collections, datetime as dt, json, os, subprocess, sys, tempfile, urllib.request

OWNER = os.environ.get("PROFILE_OWNER", "Albis0")
EMAILS = {e.strip().lower() for e in os.environ.get(
    "PROFILE_EMAILS", "abdurrahman.aksakal09@gmail.com,abdurrahman.aksakal@gmail.com").split(",")}
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "activity.json")


def api(url, token):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def list_repos(token):
    repos, page = [], 1
    while True:
        url = (f"https://api.github.com/user/repos?per_page=100&page={page}&affiliation=owner" if token
               else f"https://api.github.com/users/{OWNER}/repos?per_page=100&page={page}")
        chunk = api(url, token)
        repos += [r for r in chunk if r["owner"]["login"].lower() == OWNER.lower()]
        if len(chunk) < 100:
            return repos
        page += 1


def commit_rows(full_name, token, tmp):
    """(iso_date, email) for every commit reachable from any ref."""
    url = f"https://x-access-token:{token}@github.com/{full_name}" if token else f"https://github.com/{full_name}"
    dest = os.path.join(tmp, full_name.replace("/", "_") + ".git")
    r = subprocess.run(["git", "clone", "--bare", "--filter=blob:none", "--no-tags", "-q", url, dest],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:                      # empty repo etc.
        return []
    out = subprocess.run(["git", "-C", dest, "log", "--all", "--format=%aI%x09%ae"],
                         capture_output=True, text=True).stdout
    return [tuple(l.split("\t")) for l in out.splitlines() if "\t" in l]


def aggregate(per_repo):
    """per_repo: list of (meta, rows). Returns the json-ready dict."""
    days, repos, seen = collections.Counter(), [], set()
    for meta, rows in per_repo:
        n = 0
        for iso, email in rows:
            if email.lower() not in EMAILS:
                continue
            key = (meta["id"], iso)
            if key in seen:
                continue
            seen.add(key)
            days[iso[:10]] += 1
            n += 1
        if n:
            repos.append({"name": meta["name"] if meta["public"] else None,
                          "public": meta["public"], "fork": meta["fork"], "commits": n})
    repos.sort(key=lambda r: -r["commits"])
    return {"generated": dt.date.today().isoformat(), "owner": OWNER,
            "days": dict(sorted(days.items())), "repos": repos}


def main():
    token = os.environ.get("GH_TOKEN") or None
    per_repo = []
    with tempfile.TemporaryDirectory() as tmp:
        for r in list_repos(token):
            if r.get("size", 1) == 0:
                continue
            meta = {"id": r["full_name"], "name": r["name"], "public": not r["private"], "fork": r["fork"]}
            per_repo.append((meta, commit_rows(r["full_name"], token, tmp)))
            print(f'{r["full_name"]}: {len(per_repo[-1][1])}', file=sys.stderr)
    data = aggregate(per_repo)
    new_total = sum(data["days"].values())
    try:                                        # never shrink the picture silently (expired or missing token)
        old_total = sum(json.load(open(OUT, encoding="utf-8"))["days"].values())
    except (OSError, ValueError, KeyError):
        old_total = 0
    if old_total and new_total < old_total * 0.9:
        sys.exit(f"refusing to overwrite: {new_total} commits now vs {old_total} before (token without access?)")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=False)
    print(f'{sum(data["days"].values())} commits, {len(data["days"])} days, {len(data["repos"])} repos', file=sys.stderr)


if __name__ == "__main__":
    main()

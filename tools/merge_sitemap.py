#!/usr/bin/env python3
"""
merge_sitemap.py — keep sitemap.xml limited to human-facing search pages and
refuse to advertise a file that does not exist.

Machine-readable resources remain published through llms.txt and the agent card;
putting JSON, JSONL, Markdown, Python, schemas, signatures, or other machine-only
artifacts in the search sitemap creates crawl noise rather than human results.

It also enforces the rule the sitemap defect taught in the first place. Every
<loc> must resolve to a file in the working tree. A dead link inside a sitemap
is the first thing a crawler resolves, and it discounts every sibling URL — so
this script will not add one, and it reports any that are already there.

    python3 merge_sitemap.py path/to/repo
    python3 merge_sitemap.py path/to/repo --dry-run

Sitemap directives in robots.txt and any sitemap index are left alone. They
belong to whoever maintains them.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

BASE = "https://wulfkaal.github.io/"
SITEMAP_LOC = re.compile(r"<sitemap><loc>(.*?)</loc>")
URL_ROW = re.compile(r"<url>(.*?)</url>")
URL_LOC = re.compile(r"<loc>(.*?)</loc>")
LASTMOD = re.compile(r"<lastmod>(.*?)</lastmod>")

# These are the URL rows that previously had no content date. Claim records already
# carry their source publication date, so only the claim and failure hubs in that
# sitemap belong to this normalizer.
FULL_LASTMOD_SITEMAPS = (
    "sitemap.xml",
    "sitemap-colloquium.xml",
    "sitemap-entities.xml",
)

# Human-facing hubs that are worth advertising.
WANT = [
    ("claims/by-topic/index.html", "0.9",
     "the human entry point to the topic layer; links all 29 topic pages, which is "
     "how a crawler reaches them without the sitemap listing each leaf"),
]


def eligible_row(sitemap_name: str, body: str) -> bool:
    if sitemap_name in FULL_LASTMOD_SITEMAPS:
        return True
    # Claim records have source publication dates and no priority element. The
    # explicitly ranked root, claim-index, and failure-hub rows need Git history.
    return sitemap_name == "sitemap-claims.xml" and "<priority>" in body


def source_path(repo: Path, url: str) -> Path:
    """Resolve a served URL to the tracked path whose content the URL exposes."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "wulfkaal.github.io":
        raise ValueError(f"not a repository URL: {url}")
    rel = unquote(parsed.path.lstrip("/"))
    candidates = []
    if not rel:
        candidates.append(Path("index.html"))
    elif rel.endswith("/"):
        candidates.append(Path(rel) / "index.html")
    else:
        candidates.append(Path(rel))
        if "." not in Path(rel).name:
            candidates.extend((Path(rel + ".html"), Path(rel) / "index.html"))
    for candidate in candidates:
        if (repo / candidate).is_file():
            return candidate
    raise ValueError(f"no source path for {url}")


def _git(repo: Path, args: list[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update({"LC_ALL": "C", "LANG": "C", "TZ": "UTC"})
    return subprocess.run(
        ["git", *args], cwd=repo, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )


def git_content_dates(repo: Path, paths: set[Path]) -> dict[Path, str]:
    """Return each path's latest committed content-history date.

    Git's strict ISO short date is locale independent. Dirty and untracked sources
    are rejected because their current bytes have no committed content date yet.
    Filesystem timestamps are never consulted.
    """
    wanted = {path.as_posix() for path in paths}
    tracked_result = _git(repo, ["ls-files", "-z"])
    if tracked_result.returncode:
        raise ValueError(tracked_result.stderr.strip() or "git ls-files failed")
    tracked = set(tracked_result.stdout.rstrip("\0").split("\0"))
    untracked = sorted(wanted - tracked)
    if untracked:
        raise ValueError("untracked source path: " + ", ".join(untracked[:5]))

    dirty_result = _git(repo, ["diff", "--name-only", "-z", "HEAD", "--"])
    if dirty_result.returncode:
        raise ValueError(dirty_result.stderr.strip() or "git diff failed")
    dirty = set(dirty_result.stdout.rstrip("\0").split("\0")) & wanted
    if dirty:
        raise ValueError("uncommitted content for source path: " + ", ".join(sorted(dirty)[:5]))

    roots = sorted({name.split("/", 1)[0] for name in wanted})
    history = _git(
        repo,
        ["-c", "core.quotePath=false", "log", "--format=@@LASTMOD@@%cs",
         "--name-only", "--diff-filter=AM", "--", *roots],
    )
    if history.returncode:
        raise ValueError(history.stderr.strip() or "git log failed")
    dates: dict[str, str] = {}
    current_date = ""
    for line in history.stdout.splitlines():
        if line.startswith("@@LASTMOD@@"):
            current_date = line.removeprefix("@@LASTMOD@@")
        elif line in wanted and line not in dates:
            dates[line] = current_date
    missing = sorted(wanted - set(dates))
    if missing:
        raise ValueError("no content-changing commit for source path: " + ", ".join(missing[:5]))
    return {path: dates[path.as_posix()] for path in paths}


def git_content_date(repo: Path, path: Path) -> str:
    """Single-path entry point used by tests and other generators."""
    return git_content_dates(repo, {path})[path]


def expected_lastmods(repo: Path) -> dict[tuple[str, str], str]:
    sources: dict[tuple[str, str], Path] = {}
    for sitemap_name in (*FULL_LASTMOD_SITEMAPS, "sitemap-claims.xml"):
        text = (repo / sitemap_name).read_text(encoding="utf-8")
        for body in URL_ROW.findall(text):
            loc = URL_LOC.search(body)
            if loc and eligible_row(sitemap_name, body):
                sources[(sitemap_name, loc.group(1))] = source_path(repo, loc.group(1))
    dates = git_content_dates(repo, set(sources.values()))
    return {key: dates[path] for key, path in sources.items()}


def rendered_lastmod_sitemaps(repo: Path) -> tuple[dict[str, str], int]:
    expected = expected_lastmods(repo)
    rendered = {}
    for sitemap_name in (*FULL_LASTMOD_SITEMAPS, "sitemap-claims.xml"):
        text = (repo / sitemap_name).read_text(encoding="utf-8")

        def update(match):
            body = match.group(1)
            loc = URL_LOC.search(body)
            if not loc or not eligible_row(sitemap_name, body):
                return match.group(0)
            date = expected[(sitemap_name, loc.group(1))]
            if LASTMOD.search(body):
                body = LASTMOD.sub(f"<lastmod>{date}</lastmod>", body, count=1)
            else:
                body = body.replace("</loc>", f"</loc><lastmod>{date}</lastmod>", 1)
            return f"<url>{body}</url>"

        rendered[sitemap_name] = URL_ROW.sub(update, text)
    return rendered, len(expected)


def check_lastmods(repo: Path) -> tuple[list[str], int]:
    rendered, count = rendered_lastmod_sitemaps(repo)
    problems = [
        f"{name} has missing or stale URL-level lastmod values"
        for name, expected in rendered.items()
        if (repo / name).read_text(encoding="utf-8") != expected
    ]
    return problems, count


def sync_lastmods(repo: Path, dry_run: bool = False) -> int:
    rendered, count = rendered_lastmod_sitemaps(repo)
    changed = 0
    for name, expected in rendered.items():
        path = repo / name
        if path.read_text(encoding="utf-8") == expected:
            continue
        changed += 1
        if not dry_run:
            path.write_text(expected, encoding="utf-8")
    print(f"  URL-level lastmod: {count} eligible URLs, {changed} sitemap(s) stale")
    return changed

def is_human_search_url(url: str) -> bool:
    """Keep directory, extensionless canonical, and HTML URLs only."""
    rel = url.removeprefix(BASE).split("?", 1)[0].split("#", 1)[0]
    name = rel.rstrip("/").rsplit("/", 1)[-1]
    return not rel or rel.endswith("/") or "." not in name or name.endswith(".html")


def sibling_sitemap_urls(repo: Path) -> set[str]:
    """Return URLs already advertised by another repository-local sitemap."""
    index = (repo / "sitemap-index.xml").read_text(encoding="utf-8")
    urls = set()
    for sitemap_url in SITEMAP_LOC.findall(index):
        rel = sitemap_url.removeprefix(BASE)
        if rel == "sitemap.xml":
            continue
        path = repo / rel
        if path.exists():
            urls.update(re.findall(r"<loc>(.*?)</loc>", path.read_text(encoding="utf-8")))
    return urls


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    repo = Path(a.repo)
    if a.check:
        try:
            problems, count = check_lastmods(repo)
        except ValueError as exc:
            print(f"lastmod check failed: {exc}", file=sys.stderr)
            return 1
        if problems:
            for problem in problems:
                print(f"  {problem}", file=sys.stderr)
            print("run tools/merge_sitemap.py .", file=sys.stderr)
            return 1
        print(f"URL-level lastmod values current ({count} eligible URLs)")
        return 0
    p = repo / "sitemap.xml"
    txt = p.read_text()
    advertised_elsewhere = sibling_sitemap_urls(repo)

    # One URL per line is the repository's stable sitemap format. Drop a directly
    # attached explanatory comment with a removed machine-only entry so reruns are
    # byte-stable and do not leave misleading orphan comments.
    row = re.compile(r'(?:  <!--[^\n]*-->\n)*  <url><loc>(.*?)</loc>.*?</url>\n')
    removed = []

    def keep_search_row(match):
        if (is_human_search_url(match.group(1))
                and match.group(1) not in advertised_elsewhere):
            return match.group(0)
        removed.append(match.group(1))
        return ""

    txt = row.sub(keep_search_row, txt)
    for url in removed:
        print(f"  - {url}")
    have = set(re.findall(r"<loc>(.*?)</loc>", txt))

    # 1. report anything already advertised that does not exist
    dead = []
    for u in sorted(have):
        rel = u.replace(BASE, "")
        if not rel or rel.endswith("/"):
            continue                      # directory index, or another repo
        if not (repo / rel).exists():
            dead.append(u)
    pruned_dead = bool(dead and not a.dry_run)
    if pruned_dead:
        dead_set = set(dead)

        def drop_dead_row(match):
            if match.group(1) in dead_set:
                print(f"  - {match.group(1)} (missing from tree)")
                return ""
            return match.group(0)

        txt = row.sub(drop_dead_row, txt)
        have -= dead_set
        dead = []
    else:
        for u in dead:
            print(f"  ! already advertised but missing from the tree: {u}")

    # 2. add what is missing and does exist
    add = []
    for rel, prio, why in WANT:
        u = BASE + rel
        if u in have or u in advertised_elsewhere:
            continue
        if not (repo / rel).exists():
            print(f"  · skipping {rel} — not in the tree, so advertising it would "
                  f"create the exact defect this pack fixes")
            continue
        add.append((u, prio, why))

    if not add:
        if (removed or pruned_dead) and not a.dry_run:
            p.write_text(txt)
        print("  sitemap already advertises every existing surface; nothing to add")
        try:
            sync_lastmods(repo, a.dry_run)
        except ValueError as exc:
            print(f"lastmod generation failed: {exc}", file=sys.stderr)
            return 1
        return 1 if dead else 0

    lines = []
    for u, prio, why in add:
        if why:
            lines.append(f"  <!-- {why} -->")
        lines.append(f"  <url><loc>{u}</loc><priority>{prio}</priority></url>")
        print(f"  + {u}")

    if a.dry_run:
        try:
            sync_lastmods(repo, True)
        except ValueError as exc:
            print(f"lastmod generation failed: {exc}", file=sys.stderr)
            return 1
        return 0

    out = txt.replace("</urlset>", "\n".join(lines) + "\n</urlset>")
    if out == txt:
        print("  could not find </urlset>; not writing", file=sys.stderr)
        return 1
    p.write_text(out)
    try:
        sync_lastmods(repo)
    except ValueError as exc:
        print(f"lastmod generation failed: {exc}", file=sys.stderr)
        return 1
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())

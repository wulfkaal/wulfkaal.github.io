#!/usr/bin/env python3
"""Deterministically validate discoverability of sitemap-backed HTML pages."""

import argparse
import collections
import hashlib
import html
import html.parser
import json
import pathlib
import posixpath
import sys
import urllib.parse
import xml.etree.ElementTree as ET


BASE = "https://wulfkaal.github.io/"
ORIGIN = urllib.parse.urlsplit(BASE).netloc
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
MAX_DEPTH = 4

# Each digest binds the complete sorted exception set for one diagnostic code.
# Adding or removing even one page invalidates the exception and fails closed.
ALLOWLISTS = {
    "CANONICAL_COUNT": {
        "9522fb86ddc0127ba1bd3d42e428e60dbb9d5f2551d4e17a13de115fd7bbe062":
            "legacy static families predate canonical projection; exact 62-page set",
    },
}


class PageParser(html.parser.HTMLParser):
    """Collect only the HTML fields needed by this offline check."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors = []
        self.canonicals = []
        self.descriptions = []
        self.json_ld = []
        self.resources = []
        self.titles = []
        self._title = None
        self._json = None

    @staticmethod
    def _attrs(attrs):
        return {key.lower(): (value or "") for key, value in attrs}

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        values = self._attrs(attrs)
        if tag == "a" and values.get("href"):
            self.anchors.append(values["href"])
        if tag == "title":
            self._title = []
        if tag == "meta" and values.get("name", "").casefold() == "description":
            self.descriptions.append(values.get("content", ""))
        if tag == "link":
            rel = {part.casefold() for part in values.get("rel", "").split()}
            if "canonical" in rel:
                self.canonicals.append(values.get("href", ""))
            if rel & {"stylesheet", "icon", "manifest", "preload", "prefetch", "modulepreload"}:
                if values.get("href"):
                    self.resources.append(("link", values["href"]))
        if tag == "script":
            if values.get("src"):
                self.resources.append(("script", values["src"]))
            if values.get("type", "").casefold() == "application/ld+json":
                self._json = []
        resource_attributes = {
            "audio": ("src",),
            "embed": ("src",),
            "iframe": ("src",),
            "img": ("src", "srcset"),
            "input": ("src",),
            "object": ("data",),
            "source": ("src", "srcset"),
            "track": ("src",),
            "video": ("src", "poster"),
        }
        for attribute in resource_attributes.get(tag, ()):
            if values.get(attribute):
                candidates = [values[attribute]]
                if attribute == "srcset":
                    candidates = [item.strip().split()[0] for item in values[attribute].split(",")]
                self.resources.extend((f"{tag}[{attribute}]", item) for item in candidates if item)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title" and self._title is not None:
            self.titles.append("".join(self._title))
            self._title = None
        if tag == "script" and self._json is not None:
            self.json_ld.append("".join(self._json))
            self._json = None

    def handle_data(self, data):
        if self._title is not None:
            self._title.append(data)
        if self._json is not None:
            self._json.append(data)


def normalized_text(value):
    return " ".join(html.unescape(value).split()).casefold()


def relative_path(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("", "https") or parsed.netloc not in ("", ORIGIN):
        return None
    if parsed.query or parsed.fragment:
        return None
    decoded = urllib.parse.unquote(parsed.path)
    normalized = posixpath.normpath("/" + decoded.lstrip("/"))
    if decoded.endswith("/") and not normalized.endswith("/"):
        normalized += "/"
    if normalized == "/../" or normalized.startswith("/../"):
        return None
    return normalized.lstrip("/")


def candidates_for(root, url, html_only=False):
    relative = relative_path(url)
    if relative is None:
        return []
    choices = []
    if not relative or relative.endswith("/"):
        choices.append(relative + "index.html")
    elif pathlib.PurePosixPath(relative).suffix:
        choices.append(relative)
    else:
        choices.extend((relative + ".html", relative + "/index.html", relative))
    paths = []
    for choice in choices:
        candidate = root / pathlib.PurePosixPath(choice)
        if (not html_only or candidate.suffix == ".html") and candidate.is_file():
            paths.append(candidate)
    return paths


def public_url(path, root):
    relative = path.relative_to(root).as_posix()
    if relative == "index.html":
        return BASE
    if relative.endswith("/index.html"):
        return BASE + relative[:-len("index.html")]
    return BASE + relative


def local_target(root, source, href):
    target = urllib.parse.urljoin(public_url(source, root), href)
    parsed = urllib.parse.urlsplit(target)
    if parsed.netloc != ORIGIN or parsed.scheme not in ("http", "https"):
        return None, False
    without_fragment = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))
    choices = candidates_for(root, without_fragment)
    return (choices[0] if choices else None), True


def parse_page(path, cache):
    if path not in cache:
        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
        cache[path] = parser
    return cache[path]


def exception_digest(details):
    return hashlib.sha256("\n".join(sorted(details)).encode("utf-8")).hexdigest()


def pending_is_allowed(code, details):
    return bool(details) and exception_digest(details) in ALLOWLISTS.get(code, {})


def check(root):
    root = pathlib.Path(root).resolve()
    problems = set()
    pending = collections.defaultdict(list)
    owners = collections.defaultdict(list)
    mapped = {}
    index_path = root / "sitemap-index.xml"
    try:
        sitemap_index = ET.parse(index_path).getroot()
    except (OSError, ET.ParseError) as exc:
        return [f"SITEMAP_INDEX {exc}"], {"sitemap_urls": 0, "html_pages": 0}

    for node in sitemap_index.findall("sm:sitemap", NS):
        sitemap_url = (node.findtext("sm:loc", namespaces=NS) or "").strip()
        relative = relative_path(sitemap_url)
        if relative is None or urllib.parse.urlsplit(sitemap_url).netloc != ORIGIN:
            problems.add(f"SITEMAP_ORIGIN {sitemap_url or '<empty>'}")
            continue
        sitemap_path = root / relative
        try:
            sitemap = ET.parse(sitemap_path).getroot()
        except (OSError, ET.ParseError) as exc:
            problems.add(f"SITEMAP_CHILD {relative}: {exc}")
            continue
        for loc in sitemap.findall("sm:url/sm:loc", NS):
            url = (loc.text or "").strip()
            owners[url].append(relative)

    physical_owners = collections.defaultdict(list)
    for url, sitemap_owners in sorted(owners.items()):
        if len(sitemap_owners) != 1:
            problems.add(f"SITEMAP_OWNER {url}: {', '.join(sorted(sitemap_owners))}")
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != ORIGIN or parsed.query or parsed.fragment:
            problems.add(f"SITEMAP_URL {url}")
            continue
        choices = candidates_for(root, url, html_only=True)
        if not choices:
            path = urllib.parse.urlsplit(url).path
            if path.endswith("/") or not pathlib.PurePosixPath(path).suffix or path.endswith(".html"):
                problems.add(f"HTML_MISSING {url}")
            continue
        if len(choices) != 1:
            detail = ", ".join(path.relative_to(root).as_posix() for path in choices)
            problems.add(f"HTML_AMBIGUOUS {url}: {detail}")
            continue
        mapped[url] = choices[0]
        physical_owners[choices[0]].append(url)
    for path, urls in sorted(physical_owners.items(), key=lambda item: item[0].as_posix()):
        if len(urls) > 1:
            problems.add(f"SITEMAP_ALIAS {path.relative_to(root).as_posix()}: {', '.join(sorted(urls))}")

    cache = {}
    depths = {root / "index.html": 0}
    queue = collections.deque(depths)
    while queue:
        page = queue.popleft()
        parser = parse_page(page, cache)
        if depths[page] > MAX_DEPTH:
            continue
        for href in parser.anchors:
            target, is_local = local_target(root, page, href)
            if is_local and target is None:
                problems.add(f"LOCAL_LINK {page.relative_to(root).as_posix()}: {href}")
            if target is not None and target.suffix == ".html" and target not in depths:
                depths[target] = depths[page] + 1
                queue.append(target)

    metadata = {"title": collections.defaultdict(list), "description": collections.defaultdict(list)}
    for url, page in sorted(mapped.items()):
        relative = page.relative_to(root).as_posix()
        parser = parse_page(page, cache)
        depth = depths.get(page)
        if depth is None:
            problems.add(f"UNREACHABLE {url}")
        elif depth > MAX_DEPTH:
            problems.add(f"DEPTH {url}: {depth} > {MAX_DEPTH}")

        if len(parser.canonicals) != 1:
            pending["CANONICAL_COUNT"].append(f"{relative}: {len(parser.canonicals)}")
        else:
            canonical_paths = candidates_for(root, parser.canonicals[0], html_only=True)
            if len(canonical_paths) != 1 or canonical_paths[0] != page:
                problems.add(f"CANONICAL_SELF {relative}: {parser.canonicals[0]}")

        fields = (("title", parser.titles), ("description", parser.descriptions))
        for field, values in fields:
            normalized = [normalized_text(value) for value in values]
            if len(normalized) != 1 or not normalized[0]:
                pending[f"METADATA_{field.upper()}"] .append(f"{relative}: count={len(values)}")
            else:
                key = values[0].strip() if field == "description" else normalized[0]
                metadata[field][key].append(url)

        if not parser.json_ld:
            problems.add(f"JSON_LD {relative}: missing")
        for number, document in enumerate(parser.json_ld, 1):
            try:
                json.loads(document)
            except json.JSONDecodeError as exc:
                problems.add(f"JSON_LD {relative}: block {number} invalid at {exc.pos}")

        for kind, resource in parser.resources:
            absolute = urllib.parse.urljoin(public_url(page, root), resource)
            parsed = urllib.parse.urlsplit(absolute)
            if parsed.scheme in ("data", "blob"):
                continue
            if parsed.scheme not in ("http", "https") or parsed.netloc != ORIGIN:
                problems.add(f"THIRD_PARTY {relative}: {kind} {resource}")

        for href in parser.anchors:
            target, is_local = local_target(root, page, href)
            if is_local and target is None:
                problems.add(f"LOCAL_LINK {relative}: {href}")

    for field, values in metadata.items():
        for urls in values.values():
            if len(urls) > 1:
                duplicates = ", ".join(sorted(urls))
                pending[f"METADATA_DUPLICATE_{field.upper()}"] .extend(
                    f"{url}: duplicates {duplicates}" for url in sorted(urls)
                )

    for code, details in sorted(pending.items()):
        if not pending_is_allowed(code, details):
            problems.update(f"{code} {detail}" for detail in details)
    for code, exceptions in ALLOWLISTS.items():
        for digest, reason in exceptions.items():
            if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
                problems.add(f"ALLOWLIST_DIGEST {code}: {digest or '<empty>'}")
            if not reason.strip():
                problems.add(f"ALLOWLIST_REASON {code}: {digest}")

    return sorted(problems), {"sitemap_urls": len(owners), "html_pages": len(mapped)}


def print_problems(problems):
    grouped = collections.defaultdict(list)
    for problem in problems:
        code, _, detail = problem.partition(" ")
        grouped[code].append(detail)
    for code in sorted(grouped):
        details = sorted(grouped[code])
        examples = " | ".join(details[:3])
        suffix = f" | +{len(details) - 3} more" if len(details) > 3 else ""
        print(f"{code} count={len(details)}: {examples}{suffix}", file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=pathlib.Path(__file__).resolve().parents[1], type=pathlib.Path)
    args = parser.parse_args(argv)
    problems, stats = check(args.root)
    if problems:
        print_problems(problems)
        return 1
    print(
        f"html discoverability exact: {stats['html_pages']} sitemap-backed HTML pages, "
        f"{stats['sitemap_urls']} unique URLs"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Publish an enumerable index of the claim topic slices.

WHY THIS EXISTS

`claims/by-topic/` holds 29 topic slices covering every one of the 5,288 claims, but
nothing lists them. `positions/by-topic/` has had a shard index all along; the claim
side never did. The practical effect measured on 2026-09-10: only 8 of the 29 slugs
appear in any agent entry point, so **67% of claim-topic tags (7,534 of 11,256) were
reachable only by guessing a URL** -- including 907 claims on economics and 879 on
institutional design. Published, correct, and invisible to enumeration.

This matters more than it looks. OpenAlex caps an author profile at five topics and
picks them by work count, so it describes Kaal as a banking-and-blockchain scholar and
has no room to say anything else. The claim corpus has no such cap -- but only if an
agent can discover the slices without knowing their names in advance.

DESIGN

The index is DERIVED, never typed, matching how every other published count in this
repo works: `--check` fails loudly in CI when it drifts, so the layer holds without
attention. It mirrors `kaal-position-shard-index-v1` exactly (same key order, same
shard shape, same two-space indent and trailing newline) so both dimensions parse
identically. Each shard advertises both its JSON membership and its bounded human
landing page.

The generator also VERIFIES rather than trusting: each shard's own `count` must equal
the length of its claim list, and the union of the shards must equal the topic tags in
claims/index.json. A shard index that agrees with a stale shard is worse than none.
"""

import argparse
import html
import html.parser
import json
import pathlib
import re
import sys

BASE = "https://wulfkaal.github.io"
SCHEMA = "kaal-claim-shard-index-v1"
ID_PREFIX = "kaal:claim:"
PAGE_SIZE = 200
BREADCRUMB_START = "<!-- claim-topic-breadcrumb:start -->"
BREADCRUMB_END = "<!-- claim-topic-breadcrumb:end -->"
OVERFLOW_START = "<!-- claim-topic-overflow:start -->"
OVERFLOW_END = "<!-- claim-topic-overflow:end -->"


SHARD_KEYS = {"topic", "count", "claims"}


def load_shards(topic_dir):
    """Every topic slice on disk, as {slug: (declared_count, actual_ids)}.

    Returns (shards, problems). The first version read only `count` and `claims` and
    substituted the filename for `topic`, so a shard whose declared topic contradicted
    its filename, or one carrying extra keys, passed unexamined -- a Codex audit
    renamed a shard's topic to "contradicts-filename", added an unexpected object, and
    got a clean --check. A file that lies about what it is cannot be trusted about
    what it contains.
    """
    shards, problems = {}, []
    for path in sorted(topic_dir.glob("*.json")):
        if path.name == "index.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"{path.name} is not readable JSON: {exc}")
            continue
        if not isinstance(data, dict):
            problems.append(f"{path.name} is not an object")
            continue
        extra = set(data) - SHARD_KEYS
        if extra:
            problems.append(f"{path.name} carries unexpected key(s): {sorted(extra)}")
        if data.get("topic") != path.stem:
            problems.append(
                f"{path.name} declares topic {data.get('topic')!r}, "
                f"which is not its filename {path.stem!r}")
        ids = data.get("claims")
        if not isinstance(ids, list):
            problems.append(f"{path.name} has no claims list")
            continue
        shards[path.stem] = (data.get("count"), ids)
    return shards, problems


def verify(shards, claims_index):
    """Return a list of problems. An empty list means the shards are trustworthy."""
    problems = []
    for slug, (declared, ids) in sorted(shards.items()):
        if declared != len(ids):
            problems.append(
                f"{slug}.json declares count {declared} but lists {len(ids)} claims")
        if len(set(ids)) != len(ids):
            problems.append(f"{slug}.json repeats a claim id")

    claims = claims_index["claims"] if isinstance(claims_index, dict) else claims_index
    # Compare MEMBERSHIP, not cardinality. Counting only was a P0 found by a Codex
    # audit on 2026-09-10: swapping one claim id in ai-and-agents.json for an
    # unrelated claim kept the length at 393 and passed every check, so a corrupted
    # shard could publish someone else's subject matter under a topic and the derived
    # HTML would render it. Equal counts are not equal sets.
    tagged = {}
    for claim in claims:
        for topic in (claim.get("topics") or []):
            tagged.setdefault(topic, set()).add(claim["id"])
    for slug, (_, ids) in sorted(shards.items()):
        expected = tagged.get(slug, set())
        actual = set(ids)
        if actual == expected:
            continue
        extra = sorted(actual - expected)
        missing = sorted(expected - actual)
        if extra:
            problems.append(
                f"{slug}: shard lists {len(extra)} claim(s) that claims/index.json does "
                f"not tag {slug}, e.g. {extra[0]}")
        if missing:
            problems.append(
                f"{slug}: claims/index.json tags {len(missing)} claim(s) the shard omits, "
                f"e.g. {missing[0]}")
    for topic in sorted(set(tagged) - set(shards)):
        problems.append(f"topic {topic!r} is tagged on claims but has no shard file")
    # An absent topic and an empty shard compare equal under set equality, so an empty
    # shard for a topic nothing is tagged with slipped through. A topic layer should
    # not advertise a topic the corpus does not have.
    for slug, (_, ids) in sorted(shards.items()):
        if not ids:
            problems.append(f"{slug}: shard is empty; no claim is tagged {slug}")
    return problems


def build(shards, sample_id):
    return {
        "schemaVersion": SCHEMA,
        "dimension": "topic",
        "count": len(shards),
        "totalClaimTopicTags": sum(len(ids) for _, ids in shards.values()),
        # A shard lists bare claim identifiers ("kaal:claim:1428387-021") while the
        # canonical URL drops the prefix ("/claims/1428387-021"). The positions shards
        # carry full URLs and need no such hint; these do, and without it the final hop
        # from an enumerated topic to an actual claim is a guess.
        "claimIdPrefix": ID_PREFIX,
        "claimUrlTemplate": f"{BASE}/claims/{{id_without_prefix}}",
        "claimJsonUrlTemplate": f"{BASE}/claims/{{id_without_prefix}}.json",
        "example": {
            "claimId": sample_id,
            "json": f"{BASE}/claims/{sample_id[len(ID_PREFIX):]}.json",
        },
        "shards": [
            {
                "topic": slug,
                "count": len(ids),
                "json": f"{BASE}/claims/by-topic/{slug}.json",
                "html": f"{BASE}/claims/by-topic/{slug}.html",
            }
            for slug, (_, ids) in sorted(shards.items())
        ],
    }


def topic_page_name(slug, page_number):
    return f"{slug}.html" if page_number == 1 else f"{slug}-{page_number}.html"


def render_pagination(slug, page_number, page_count):
    if page_count == 1:
        return ""
    links = []
    for number in range(1, page_count + 1):
        if number == page_number:
            links.append(f'<span aria-current="page">{number}</span>')
        else:
            links.append(
                f'<a href="./{topic_page_name(slug, number)}">{number}</a>')
    return '<nav aria-label="Topic pages">Pages: ' + " · ".join(links) + "</nav>"


def render_shard_html(slug, claims, page_number=1, page_count=1, total=None):
    """A human page for one topic. The JSON twin is for machines; a person
    clicking a topic previously got a wall of raw JSON, which is not reachable
    in any sense that matters."""
    items = "".join(
        f'<li><a href="{html.escape(c["url"])}">{html.escape(c["claim"])}</a>'
        f' <span class="meta">{html.escape(str(c.get("year") or ""))}</span></li>'
        for c in claims)
    total = len(claims) if total is None else total
    title = f"Kaal claims by topic: {slug}"
    page_title = title if page_number == 1 else f"{title}, page {page_number}"
    desc = (f"{total} atomic, individually citable claims from the published "
            f"work of Wulf A. Kaal tagged {slug}.")
    canonical = f"{BASE}/claims/by-topic/{topic_page_name(slug, page_number)}"
    breadcrumb = (
        '<nav aria-label="Breadcrumb"><a href="../index.html">All claims</a> · '
        '<a href="./index.html">Topics</a> · '
        f'<span>{html.escape(slug)}</span>'
        + (f' · <span>Page {page_number}</span>' if page_number > 1 else "")
        + '</nav>')
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{html.escape(page_title)} | Wulf A. Kaal Claims</title>'
        f'<meta name="description" content="{html.escape(desc)}">'
        f'<link rel="canonical" href="{canonical}">'
        '<link rel="stylesheet" href="../../style.css"></head><body><main>'
        f'{breadcrumb}<h1>{html.escape(page_title)}</h1>'
        f'<p class="claim">{html.escape(desc)}</p>{render_pagination(slug, page_number, page_count)}'
        f'<ol class="meta">{items}</ol>{render_pagination(slug, page_number, page_count)}<footer>'
        '<a href="./">All claim topics</a> · '
        f'<a href="./{html.escape(slug)}.json">This topic as JSON</a> · '
        '<a href="../">All claims</a>'
        '</footer></main></body></html>\n')


def add_claim_breadcrumb(source, record):
    topics = sorted(record.get("topics") or [])
    topic_links = ", ".join(
        f'<a href="./by-topic/{html.escape(topic)}.html">{html.escape(topic)}</a>'
        for topic in topics
    )
    body = (
        f'{BREADCRUMB_START}<nav aria-label="Breadcrumb">'
        '<a href="./index.html">All claims</a> · '
        f'<span>Topics: {topic_links}</span> · '
        f'<span>{html.escape(record["id"])}</span></nav>{BREADCRUMB_END}'
    )
    if BREADCRUMB_START in source or BREADCRUMB_END in source:
        pattern = re.compile(
            re.escape(BREADCRUMB_START) + r".*?" + re.escape(BREADCRUMB_END), re.S)
        if len(pattern.findall(source)) != 1:
            raise ValueError(f'{record["id"]} has malformed topic breadcrumbs')
        return pattern.sub(body, source, count=1)
    marker = "<body><main>"
    if marker not in source:
        raise ValueError(f'{record["id"]} has no breadcrumb insertion point')
    return source.replace(marker, marker + body, 1)


def render_index_html(rows, total):
    """The human entry point to the topic layer."""
    items = "".join(
        f'<li><a href="./{html.escape(slug)}.html">{html.escape(slug)}</a>'
        f' <span class="meta">{n} claims</span></li>'
        for slug, n in rows)
    desc = (f"Every topic in the Kaal claim corpus, with its claim count. "
            f"{len(rows)} topics covering {total} topic-tagged claims.")
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Kaal claims by topic | Wulf A. Kaal Claims</title>'
        f'<meta name="description" content="{html.escape(desc)}">'
        '<link rel="stylesheet" href="../../style.css"></head><body><main>'
        '<h1>Kaal claims by topic</h1>'
        f'<p class="claim">{html.escape(desc)}</p>'
        f'<ol class="meta">{items}</ol><footer>'
        '<a href="./index.json">This index as JSON</a> · '
        '<a href="../">All claims</a> · '
        '<a href="../../">Wulf A. Kaal</a>'
        '</footer></main></body></html>\n')


class _TopicTable(html.parser.HTMLParser):
    """Extract the Topics table semantically.

    Two regexes used to do this: one to rewrite counts, one to check completeness.
    They recognised different narrow byte patterns, and a Codex audit defeated both at
    once with markup that renders identically -- `<td class="unused">` on the third
    cell. The rewrite skipped the row, the completeness check still listed the slug,
    and --check exited 0 with a visibly wrong count on the page. A parser reads the
    table the way a browser does, so formatting cannot hide a row from it.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_table = self.in_row = False
        self.cells = None
        self.buf = []
        self.href = None
        self.rows = []          # (slug, count_text, href)
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "table" and not self.in_table:
            self.in_table = True
        elif self.in_table and tag == "tr":
            self.in_row, self.cells = True, []
        elif self.in_row and tag in ("td", "th"):
            self.buf, self.href = [], None
        elif self.in_row and tag == "a":
            self.href = dict(attrs).get("href")

    def handle_endtag(self, tag):
        if tag == "table" and self.in_table:
            self.in_table = False
        elif self.in_row and tag == "tr":
            if self.cells and len(self.cells) >= 3:
                slug, count, _ = self.cells[0], self.cells[1], self.cells[2]
                self.rows.append((slug.strip(), count.strip(), self.href))
            self.in_row, self.cells = False, None
        elif self.in_row and tag in ("td", "th") and self.cells is not None:
            self.cells.append("".join(self.buf))

    def handle_data(self, data):
        if self.in_row:
            self.buf.append(data)


def parse_topic_table(html_text):
    """-> (start, end, [(slug, count_text, href)]) for the Topics table, or None."""
    marker = html_text.find('<div class="k">Topics</div>')
    if marker == -1:
        return None
    start = html_text.find("<table", marker)
    end = html_text.find("</table>", start)
    if start == -1 or end == -1:
        return None
    parser = _TopicTable()
    parser.feed(html_text[start:end + len("</table>")])
    return start, end + len("</table>"), parser.rows


def retopic_claims_index_html(html_text, shard_counts):
    """Correct the Topics table in claims/index.html from the shards.

    That page is generated upstream and its table had drifted: 24 of 29 counts were
    low, understating the corpus by 508 claim-tags on its primary human page, while
    the shards it links were right. The numbers are derivable, so they are derived
    here and --check fails when they drift again.
    """
    parsed = parse_topic_table(html_text)
    if parsed is None:
        return html_text, [("(no Topics table found)", 0, 0)]
    start, end, rows = parsed
    wrong = []
    seen = set()
    table = html_text[start:end]

    for slug, count_text, href in rows:
        if not slug or slug == "Topic":
            continue
        if slug in seen:
            wrong.append((f"{slug} (duplicate row)", 0, 0))
            continue
        seen.add(slug)
        real = shard_counts.get(slug)
        if real is None:
            wrong.append((f"{slug} (row for a topic with no shard)", 0, 0))
            continue
        want_href = f"./by-topic/{slug}.json"
        if href != want_href:
            wrong.append((f"{slug} (link is {href!r}, expected {want_href!r})", 0, real))
            continue
        try:
            shown = int(count_text)
        except ValueError:
            wrong.append((f"{slug} (count {count_text!r} is not a number)", 0, real))
            continue
        if shown != real:
            wrong.append((slug, shown, real))
            # Rewrite this row's count wherever it sits, matching the cell that
            # precedes this slug's own link rather than a fixed byte pattern.
            pattern = re.compile(
                r"(<td[^>]*>\s*" + re.escape(slug) + r"\s*</td>\s*<td[^>]*>\s*)"
                + re.escape(count_text) + r"(\s*</td>)")
            table, n = pattern.subn(rf"\g<1>{real}\g<2>", table, count=1)
            if n != 1:
                wrong.append((f"{slug} (count cell could not be rewritten)", shown, real))

        topic_link = f'<a href="./by-topic/{slug}.html">{slug}</a>'
        if topic_link not in table:
            pattern = re.compile(
                r"(<td[^>]*>\s*)" + re.escape(slug) + r"(\s*</td>)")
            table, n = pattern.subn(rf"\g<1>{topic_link}\g<2>", table, count=1)
            wrong.append((f"{slug} (HTML topic link missing)", 0, real))
            if n != 1:
                wrong.append((f"{slug} (topic cell could not be linked)", 0, real))

    for slug in sorted(set(shard_counts) - seen):
        wrong.append((f"{slug} (missing row)", 0, shard_counts[slug]))

    return html_text[:start] + table + html_text[end:], wrong


def expose_entity_hub(html_text):
    """Expose the generated entity hub from the already linked claim layer."""
    href = "../entities/index.html"
    if html_text.count(href) == 1:
        return html_text, False
    if href in html_text:
        raise ValueError("claims/index.html contains duplicate entity hub links")
    marker = '</ul><div class="k">Topics</div>'
    if marker not in html_text:
        raise ValueError("claims/index.html has no Machine access list before Topics")
    link = ('<li><a href="../entities/index.html">Entity index</a>, concept nodes '
            'over the claim layer</li>')
    return html_text.replace(marker, link + marker, 1), True


def expose_overflow_topic_pages(html_text, page_counts):
    """Link every paginated topic page from the primary claim discovery hub."""
    links = []
    for slug, page_count in sorted(page_counts.items()):
        for page_number in range(2, page_count + 1):
            name = topic_page_name(slug, page_number)
            links.append(
                f'<li><a href="./by-topic/{html.escape(name)}">'
                f'{html.escape(slug)}, page {page_number}</a></li>')
    body = (
        f'{OVERFLOW_START}<nav aria-label="Additional claim topic pages">'
        '<div class="k">Additional topic pages</div><ul class="meta">'
        + "".join(links) + f'</ul></nav>{OVERFLOW_END}'
    )
    pattern = re.compile(
        re.escape(OVERFLOW_START) + r".*?" + re.escape(OVERFLOW_END), re.S)
    matches = pattern.findall(html_text)
    if len(matches) > 1:
        raise ValueError("claims/index.html contains duplicate overflow topic hubs")
    if matches:
        updated = pattern.sub(body, html_text, count=1)
        return updated, updated != html_text
    marker = "<footer>"
    if marker not in html_text:
        raise ValueError("claims/index.html has no footer before which to add topic pages")
    return html_text.replace(marker, body + marker, 1), True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if the published index is missing or stale")
    parser.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parent.parent))
    args = parser.parse_args()

    repo = pathlib.Path(args.repo)
    topic_dir = repo / "claims" / "by-topic"
    index_path = topic_dir / "index.json"

    shards, shard_problems = load_shards(topic_dir)
    if shard_problems:
        for problem in shard_problems:
            print(f"  {problem}", file=sys.stderr)
        print("refusing to trust shards that misdescribe themselves", file=sys.stderr)
        return 1
    if not shards:
        print(f"no topic shards found under {topic_dir}", file=sys.stderr)
        return 1

    claims_index = json.loads((repo / "claims" / "index.json").read_text(encoding="utf-8"))
    records = claims_index["claims"] if isinstance(claims_index, dict) else claims_index
    by_id = {c["id"]: c for c in records}
    problems = verify(shards, claims_index)
    if problems:
        print("the topic shards do not agree with claims/index.json:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        print("refusing to publish an index over shards that are already wrong",
              file=sys.stderr)
        return 1

    # Derive the example from real data, and verify the prefix actually holds across
    # every shard rather than asserting a convention that may not be universal.
    all_ids = [i for _, ids in shards.values() for i in ids]
    stray = [i for i in all_ids if not i.startswith(ID_PREFIX)]
    if stray:
        print(f"{len(stray)} claim id(s) do not start with {ID_PREFIX!r}, "
              f"e.g. {stray[0]!r}; the url template would be wrong", file=sys.stderr)
        return 1
    sample_id = sorted(all_ids)[0]

    wanted = json.dumps(build(shards, sample_id), ensure_ascii=False, indent=2) + "\n"

    # The human twins. Rendered from the same shards the JSON index describes, so the
    # two can never disagree: one generator, one source, both outputs.
    rows = [(slug, len(ids)) for slug, (_, ids) in sorted(shards.items())]
    html_pages = {"index.html": render_index_html(rows, sum(n for _, n in rows))}
    for slug, (_, ids) in sorted(shards.items()):
        missing = [i for i in ids if i not in by_id]
        if missing:
            print(f"{slug}: {len(missing)} claim id(s) are not in claims/index.json, "
                  f"e.g. {missing[0]!r}; refusing to render a page with dead entries",
                  file=sys.stderr)
            return 1
        claim_rows = [by_id[i] for i in ids]
        page_count = (len(claim_rows) + PAGE_SIZE - 1) // PAGE_SIZE
        for page_number in range(1, page_count + 1):
            start = (page_number - 1) * PAGE_SIZE
            page_claims = claim_rows[start:start + PAGE_SIZE]
            html_pages[topic_page_name(slug, page_number)] = render_shard_html(
                slug, page_claims, page_number, page_count, len(claim_rows))

    claim_pages = {}
    try:
        for record in records:
            short = record["id"].removeprefix(ID_PREFIX)
            path = repo / "claims" / f"{short}.html"
            claim_pages[path] = add_claim_breadcrumb(
                path.read_text(encoding="utf-8"), record)
    except (OSError, ValueError) as exc:
        print(f"cannot generate claim breadcrumbs: {exc}", file=sys.stderr)
        return 1

    claims_html_path = repo / "claims" / "index.html"
    claims_html = claims_html_path.read_text(encoding="utf-8")
    fixed_html, wrong_counts = retopic_claims_index_html(
        claims_html, {slug: len(ids) for slug, (_, ids) in shards.items()})
    page_counts = {
        slug: (len(ids) + PAGE_SIZE - 1) // PAGE_SIZE
        for slug, (_, ids) in shards.items()
    }
    try:
        fixed_html, entity_hub_changed = expose_entity_hub(fixed_html)
        fixed_html, overflow_hub_changed = expose_overflow_topic_pages(
            fixed_html, page_counts)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.check:
        if not index_path.exists():
            print(f"{index_path} is missing; run tools/build_claim_topic_index.py",
                  file=sys.stderr)
            return 1
        if index_path.read_text(encoding="utf-8") != wanted:
            print(f"{index_path} is stale; run tools/build_claim_topic_index.py",
                  file=sys.stderr)
            return 1
        stale = [name for name, body in html_pages.items()
                 if not (topic_dir / name).exists()
                 or (topic_dir / name).read_text(encoding="utf-8") != body]
        if stale:
            print(f"{len(stale)} human page(s) missing or stale, e.g. {stale[0]}; "
                  f"run tools/build_claim_topic_index.py", file=sys.stderr)
            return 1
        unexpected = sorted(
            path.name for path in topic_dir.glob("*.html")
            if path.name not in html_pages)
        if unexpected:
            print(f"{len(unexpected)} obsolete human page(s), e.g. {unexpected[0]}; "
                  f"run tools/build_claim_topic_index.py", file=sys.stderr)
            return 1
        stale_claims = [path for path, body in claim_pages.items()
                        if path.read_text(encoding="utf-8") != body]
        if stale_claims:
            print(f"{len(stale_claims)} claim breadcrumb(s) missing or stale, e.g. "
                  f"{stale_claims[0].name}; run tools/build_claim_topic_index.py",
                  file=sys.stderr)
            return 1
        if wrong_counts:
            for slug, shown, real in wrong_counts[:10]:
                print(f"  claims/index.html says {slug} has {shown} claims; "
                      f"the shard has {real}", file=sys.stderr)
            print(f"{len(wrong_counts)} topic count(s) in claims/index.html disagree "
                  f"with the shards; run tools/build_claim_topic_index.py",
                  file=sys.stderr)
            return 1
        if entity_hub_changed:
            print("claims/index.html does not link the entity hub; "
                  "run tools/build_claim_topic_index.py", file=sys.stderr)
            return 1
        if overflow_hub_changed:
            print("claims/index.html does not expose every overflow topic page; "
                  "run tools/build_claim_topic_index.py", file=sys.stderr)
            return 1
        print(f"claim topic index current: {len(shards)} shards, "
              f"{sum(len(i) for _, i in shards.values())} tags, "
              f"{len(html_pages)} human pages, {len(claim_pages)} claim breadcrumbs, "
              "claims/index.html counts and links agree")
        return 0

    for path in topic_dir.glob("*.html"):
        if path.name not in html_pages:
            path.unlink()
    for name, body in html_pages.items():
        (topic_dir / name).write_text(body, encoding="utf-8")
    for path, body in claim_pages.items():
        if path.read_text(encoding="utf-8") != body:
            path.write_text(body, encoding="utf-8")
    index_path.write_text(wanted, encoding="utf-8")
    if wrong_counts or entity_hub_changed or overflow_hub_changed:
        claims_html_path.write_text(fixed_html, encoding="utf-8")
        for slug, shown, real in wrong_counts:
            print(f"  claims/index.html {slug}: {shown} -> {real}")
    print(f"wrote {index_path.relative_to(repo)}: {len(shards)} shards, "
          f"{sum(len(i) for _, i in shards.values())} claim-topic tags, "
          f"{len(html_pages)} human pages, and {len(claim_pages)} claim breadcrumbs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
build_claim_about.py: check the claim keyword layer, and record about slugs.

Each claim record carries an about array of concept slugs. The markdown
renders that array as a Keywords line. Nothing in this repository used to
check the two against each other, and nothing assigns the array: it is a
judgement, not a computation, so it arrives in a file and lives on the record.

The vocabulary is whatever the about arrays already use. --assign refuses a
slug that is not in that set. An empty about array is unassigned. A list
that merely repeats the stored assignment is a no-op. A list that differs
from a stored non-empty assignment is an error and writes nothing.

Usage
  python3 tools/build_claim_about.py                 # same as --check
  python3 tools/build_claim_about.py --check
  python3 tools/build_claim_about.py --assign FILE   # JSON list of {id, about:[slugs]}
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ID_PREFIX = "kaal:claim:"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KEYWORDS_RE = re.compile(r"^\*\*Keywords\.\*\* (.+)\n", re.M)
TOPICS_RE = re.compile(r"^\*\*Topics\.\*\* .+\n", re.M)
CANON = "**Canonical form.**"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def claim_paths(repo):
    claims = repo / "claims"
    paths = []
    for path in sorted(claims.glob("*.json")):
        if path.name in ("index.json", "graph.jsonld"):
            continue
        paths.append(path)
    return paths


def stem_of(claim_id):
    if claim_id.startswith(ID_PREFIX):
        return claim_id[len(ID_PREFIX):]
    return claim_id


def full_id(claim_id):
    if claim_id.startswith(ID_PREFIX):
        return claim_id
    return ID_PREFIX + claim_id


def rendered_line(about):
    return "**Keywords.** " + ", ".join(about) + "\n"


def parse_keywords(md):
    """Return the slug list, or None when the section is absent.

    A malformed section returns the string 'malformed' so the caller can
    report it instead of treating it as an empty assignment.
    """
    found = list(KEYWORDS_RE.finditer(md))
    if "**Keywords.**" in md and not found:
        return "malformed"
    if len(found) > 1:
        return "malformed"
    if not found:
        return None
    body = found[0].group(1)
    # A single slug has no comma. A comma without the following space is not the
    # rendered form, and neither is a trailing comma.
    if body.endswith(",") or ",," in body or ("," in body and ", " not in body):
        return "malformed"
    slugs = body.split(", ") if body else []
    if [slug for slug in slugs if not slug or slug != slug.strip()]:
        return "malformed"
    if ", ".join(slugs) != body:
        return "malformed"
    return slugs


def keywords_in_place(md, about):
    """Keywords sits on its own line between Topics and the next section."""
    if not about:
        return "**Keywords.**" not in md
    needle = "\n\n" + rendered_line(about) + "\n"
    match = TOPICS_RE.search(md)
    if not match:
        return False
    return md[match.end():].startswith("\n" + rendered_line(about) + "\n")


def upsert_keywords(md, about):
    line = rendered_line(about) if about else ""
    existing = list(KEYWORDS_RE.finditer(md))
    if line:
        if len(existing) > 1 or ("**Keywords.**" in md and not existing):
            raise ValueError("Keywords section is malformed")
        if existing:
            if not keywords_in_place(md, about) and existing[0].group(0) != line:
                raise ValueError("Keywords section is not directly after Topics")
            return md[:existing[0].start()] + line + md[existing[0].end():]
        match = TOPICS_RE.search(md)
        if not match or not md[match.end():].startswith("\n**"):
            raise ValueError("Topics is not directly before the next section")
        # Keep the blank line that already separates Topics from what follows.
        return md[:match.end()] + "\n" + line + md[match.end():]
    if existing or "**Keywords.**" in md:
        raise ValueError("markdown has a Keywords section the record does not render")
    return md


def content_hashes(doc):
    found = []
    for prop in doc.get("additionalProperty") or []:
        if prop.get("name") == "content_sha256":
            found.append(prop.get("value"))
    if "sha256" in doc:
        found.append(doc["sha256"])
    return found


def vocabulary_of(records):
    vocab = set()
    for record in records:
        for slug in record["about"]:
            vocab.add(slug)
    return vocab


def load_layer(repo):
    records = []
    by_id = {}
    for path in claim_paths(repo):
        doc = load_json(path)
        if doc.get("@type") != "Claim":
            continue
        claim_id = doc.get("identifier") or full_id(path.stem)
        about = doc.get("about")
        if about is None:
            about = []
        if not isinstance(about, list):
            raise SystemExit(f"FAIL: {claim_id} about is not a list")
        md_path = path.with_suffix(".md")
        md = md_path.read_text(encoding="utf-8") if md_path.exists() else None
        records.append({
            "id": claim_id,
            "stem": path.stem,
            "about": list(about),
            "json_path": path,
            "md": md,
        })
        by_id[claim_id] = records[-1]
    return records, by_id


def load_jsonl(repo):
    path = repo / "claims" / "all.jsonl"
    text = path.read_text(encoding="utf-8")
    newline = text.endswith("\n")
    lines = text.splitlines()
    rows = [json.loads(line) for line in lines]
    return path, lines, rows, newline


def check(repo):
    records, by_id = load_layer(repo)
    vocab = vocabulary_of(records)
    problems = []
    assigned = 0
    uses = 0
    for record in records:
        about = record["about"]
        uses += len(about)
        if about:
            assigned += 1
        for slug in about:
            if slug not in vocab or not SLUG_RE.fullmatch(slug):
                problems.append(f"{record['id']}: slug {slug!r} is not in the vocabulary")
        md = record["md"]
        if md is None:
            problems.append(f"{record['id']}: missing markdown")
            continue
        rendered = parse_keywords(md)
        if rendered == "malformed":
            problems.append(f"{record['id']}: Keywords section is malformed")
            continue
        shown = rendered or []
        if shown != about:
            problems.append(
                f"{record['id']}: Keywords {shown} disagrees with about {about}"
            )
        elif not keywords_in_place(md, about):
            problems.append(f"{record['id']}: Keywords is not directly after Topics")
        for slug in shown:
            if slug not in vocab:
                problems.append(f"{record['id']}: rendered slug {slug!r} is not in the vocabulary")

    print(f"claims                         {len(records)}")
    print(f"vocabulary                     {len(vocab)}")
    print(f"slug assignments               {uses}")
    print(f"claims with about              {assigned}")
    print(f"claims without about           {len(records) - assigned}")
    if problems:
        print(f"FAIL {len(problems)} disagreement(s) (showing up to 12):", file=sys.stderr)
        for problem in problems[:12]:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print("keyword layer agrees: Keywords sections, about arrays, vocabulary")
    return 0


def attested(row):
    value = row.get("attestations")
    if value is None or value == "" or value == []:
        return False
    return True


def replace_hash(line, old, new):
    if old == new:
        return line
    count = line.count(old)
    if count != 2:
        raise ValueError(f"hash occurs {count} times on the jsonl line, expected 2")
    return line.replace(old, new)


def write_claim_json(path, about, content_hash):
    raw = path.read_text(encoding="utf-8")
    doc = json.loads(raw)
    dumped = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    if dumped != raw:
        raise ValueError(f"{path.name} does not round-trip; refusing to reformat it")
    doc["about"] = list(about)
    found = False
    for prop in doc.get("additionalProperty") or []:
        if prop.get("name") == "content_sha256":
            prop["value"] = content_hash
            found = True
    if "sha256" in doc:
        doc["sha256"] = content_hash
        found = True
    if not found:
        raise ValueError(f"{path.name} has no content hash field")
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def sync_html(text, old_hash, new_hash, about):
    if text.count(old_hash) != 2:
        raise ValueError(f"html content hash occurs {text.count(old_hash)} times, expected 2")
    if old_hash != new_hash:
        text = text.replace(old_hash, new_hash)
    body = json.dumps(list(about), ensure_ascii=False, separators=(",", ":"))
    text, count = re.subn(r'"about":\[[^\]]*\]', '"about":' + body, text, count=1)
    if count != 1:
        raise ValueError("html json-ld has no single about array")
    return text


def update_index(repo, hashes):
    """Rewrite a hash only when claims/index.json already carries one."""
    path = repo / "claims" / "index.json"
    text = path.read_text(encoding="utf-8")
    index = json.loads(text)
    claims = index.get("claims") or []
    if not claims:
        return False
    sample = claims[0]
    keys = [key for key in ("content_sha256", "sha256") if key in sample]
    if not keys:
        return False
    changed = False
    by_id = {row["id"]: row for row in claims}
    for claim_id, digest in hashes.items():
        row = by_id.get(claim_id)
        if row is None:
            raise ValueError(f"{claim_id} is missing from claims/index.json")
        for key in keys:
            if row.get(key) != digest:
                needle = f'"{key}": "{row[key]}"'
                # The hash is unique. Replace the one occurrence on this claim
                # by rewriting the parsed object back only if a surgical replace
                # would be ambiguous. Index entries do not repeat a hash today.
                if text.count(row[key]) != 1:
                    raise ValueError(f"index hash for {claim_id} is not unique")
                text = text.replace(row[key], digest, 1)
                changed = True
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def assign(repo, file_path):
    extra = load_json(pathlib.Path(file_path))
    if not isinstance(extra, list):
        print("FAIL: assignment file must be a JSON list", file=sys.stderr)
        return 1
    records, by_id = load_layer(repo)
    vocab = vocabulary_of(records)
    jsonl_path, lines, rows, newline = load_jsonl(repo)
    jsonl_by_id = {}
    line_at = {}
    for index, row in enumerate(rows):
        jsonl_by_id[row["id"]] = row
        line_at[row["id"]] = index

    seen = set()
    changes = {}
    for row in extra:
        if not isinstance(row, dict) or "id" not in row or "about" not in row:
            print("FAIL: each assignment needs id and about", file=sys.stderr)
            return 1
        claim_id = full_id(row["id"]) if row["id"] not in by_id else row["id"]
        if claim_id not in by_id and full_id(row["id"]) in by_id:
            claim_id = full_id(row["id"])
        if claim_id not in by_id:
            print(f"FAIL: {row['id']} is not a claim", file=sys.stderr)
            return 1
        if claim_id in seen:
            print(f"FAIL: {claim_id} is assigned twice", file=sys.stderr)
            return 1
        seen.add(claim_id)
        about = row["about"]
        if not isinstance(about, list) or any(not isinstance(slug, str) for slug in about):
            print(f"FAIL: {claim_id} about must be a list of slugs", file=sys.stderr)
            return 1
        if len(about) != len(set(about)):
            print(f"FAIL: {claim_id} repeats a slug", file=sys.stderr)
            return 1
        for slug in about:
            if slug not in vocab or not SLUG_RE.fullmatch(slug):
                print(f"FAIL: {claim_id} slug {slug!r} is not in the vocabulary", file=sys.stderr)
                return 1
        current = by_id[claim_id]["about"]
        if current == about:
            continue
        if current:
            print(
                f"FAIL: {claim_id} is already assigned {current}, not {about}",
                file=sys.stderr,
            )
            return 1
        source = jsonl_by_id.get(claim_id)
        if source is None:
            print(f"FAIL: {claim_id} is missing from claims/all.jsonl", file=sys.stderr)
            return 1
        if attested(source):
            print(
                f"FAIL: {claim_id} has an attestation; refusing to change its hash",
                file=sys.stderr,
            )
            return 1
        changes[claim_id] = about

    if not changes:
        print(f"assignments                    {len(extra)}")
        print("changed                        0")
        print("no-op")
        return 0

    prepared = {}
    new_lines = list(lines)
    for claim_id, about in changes.items():
        record = by_id[claim_id]
        source = jsonl_by_id[claim_id]
        try:
            md = upsert_keywords(record["md"], about)
        except ValueError as exc:
            print(f"FAIL: {claim_id}: {exc}", file=sys.stderr)
            return 1
        digest = hashlib.sha256(md.encode("utf-8")).hexdigest()
        old = source["content_sha256"]
        if digest == old and about != record["about"]:
            print(f"FAIL: {claim_id} markdown hash did not change", file=sys.stderr)
            return 1
        html_path = repo / "claims" / f"{record['stem']}.html"
        if not html_path.exists():
            print(f"FAIL: {claim_id} has no html page", file=sys.stderr)
            return 1
        try:
            html_text = sync_html(html_path.read_text(encoding="utf-8"), old, digest, about)
            new_line = replace_hash(lines[line_at[claim_id]], old, digest)
        except ValueError as exc:
            print(f"FAIL: {claim_id}: {exc}", file=sys.stderr)
            return 1
        parsed = json.loads(new_line)
        if parsed["content_sha256"] != digest or digest not in parsed["attest_command"]:
            print(f"FAIL: {claim_id} jsonl hash edit did not land", file=sys.stderr)
            return 1
        # The line may change only in the two hash slots.
        parsed["content_sha256"] = old
        parsed["attest_command"] = parsed["attest_command"].replace(digest, old)
        if parsed != source:
            print(f"FAIL: {claim_id} jsonl edit changed more than the hash", file=sys.stderr)
            return 1
        prepared[claim_id] = (md, digest, html_text, about)
        new_lines[line_at[claim_id]] = new_line

    # No byte of an unassigned claim is written.
    for claim_id, (md, digest, html_text, about) in prepared.items():
        record = by_id[claim_id]
        (repo / "claims" / f"{record['stem']}.md").write_text(md, encoding="utf-8")
        write_claim_json(record["json_path"], about, digest)
        (repo / "claims" / f"{record['stem']}.html").write_text(html_text, encoding="utf-8")
    jsonl_path.write_text("\n".join(new_lines) + ("\n" if newline else ""), encoding="utf-8")
    try:
        indexed = update_index(repo, {claim_id: item[1] for claim_id, item in prepared.items()})
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"vocabulary                     {len(vocab)}")
    print(f"assignments in file            {len(extra)}")
    print(f"changed                        {len(prepared)}")
    print(f"unchanged                      {len(extra) - len(prepared)}")
    print(f"claims/index.json hash updated {indexed}")
    for claim_id in sorted(prepared):
        print(f"  {claim_id}  {prepared[claim_id][3]}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify Keywords against about; the default")
    parser.add_argument("--assign", metavar="FILE", help="JSON list of {id, about:[slugs]} to merge")
    parser.add_argument("--repo", default=str(ROOT))
    args = parser.parse_args()
    repo = pathlib.Path(args.repo)
    if args.assign:
        status = assign(repo, args.assign)
        if status != 0:
            return status
        return check(repo)
    return check(repo)


if __name__ == "__main__":
    raise SystemExit(main())

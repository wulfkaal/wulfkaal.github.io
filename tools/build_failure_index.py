#!/usr/bin/env python3
"""
build_failure_index.py — regenerate the failure layer from the claim layer.

The failure layer (failures/index.json, failures/by-name/*.json and one HTML page
per family) was written once on 2026-07-28 and never again. By 2026-09-05 it
covered 2,037 of the 2,080 failure-mode claims; the 43 it missed came from four
papers ingested after that date. No generator for it existed in any repository,
so this is that generator, written to reproduce the existing files exactly before
adding anything.

Family and specific-name assignment is a judgement, not a computation. Existing
assignments are read back out of failures/index.json, which is their only home.
New ones arrive through --classify, a JSON list of {id, family, specific_name}.

Everything else is derived: claim text, conditions, topics, year, quote and
citation come from claims/index.json, and the source title from papers.json by
content hash.

Fidelity check: run with no --classify and the working tree must stay clean.
"""
import argparse
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://wulfkaal.github.io"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


# The 2026-07-28 files carry no trailing newline. Match them: a whole-layer diff
# is the only evidence this generator is faithful, and a newline would mask it.
def dump(path, data):
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def build(extra):
    claims = load(ROOT / "claims" / "index.json")["claims"]
    by_id = {c["id"]: c for c in claims}
    order = {c["id"]: i for i, c in enumerate(claims)}
    titles = {w["sha256"]: w["title"] for w in load(ROOT / "papers.json")["works"] if w.get("sha256")}
    current = load(ROOT / "failures" / "index.json")

    # Assignments: existing ones live only in the file we are replacing.
    assign = {f["id"]: (f["family"], f["name"]) for f in current["failures"]}
    for row in extra:
        # Re-running with the same classification file must be a no-op: the tool merges
        # into the file it is replacing, so refusing every known id would make it
        # single-use. Only a genuine disagreement is an error.
        if row["id"] in assign:
            if assign[row["id"]] == (row["family"], row["specific_name"]):
                continue
            was = assign[row["id"]]
            print(f"FAIL: {row['id']} is already classified as {was}, "
                  f"not ({row['family']!r}, {row['specific_name']!r})", file=sys.stderr)
            raise SystemExit(1)
        if row["id"] not in by_id:
            print(f"FAIL: {row['id']} is not a claim", file=sys.stderr)
            raise SystemExit(1)
        if not by_id[row["id"]].get("is_failure_mode"):
            print(f"FAIL: {row['id']} is not a failure-mode claim", file=sys.stderr)
            raise SystemExit(1)
        assign[row["id"]] = (row["family"], row["specific_name"])

    unknown = set(assign) - set(by_id)
    if unknown:
        print(f"FAIL: {len(unknown)} classified ids are not claims, e.g. {sorted(unknown)[:3]}",
              file=sys.stderr)
        raise SystemExit(1)

    rows = sorted(assign, key=lambda i: order[i])
    failures = []
    for cid in rows:
        c, (family, name) = by_id[cid], assign[cid]
        failures.append({"id": cid, "url": c["url"], "family": family, "name": name,
                         "claim": c["claim"], "conditions": c.get("scope_conditions") or [],
                         "topics": c.get("topics") or []})

    counts, first, members = {}, {}, {}
    for i, f in enumerate(failures):
        counts[f["family"]] = counts.get(f["family"], 0) + 1
        first.setdefault(f["family"], i)
        members.setdefault(f["family"], []).append(f)
    families = sorted(counts, key=lambda f: (-counts[f], first[f]))

    modes = [{"failure_family": fam, "count": counts[fam],
              "url": f"{BASE}/failures/by-name/{fam}.json",
              # The index lists at most twelve names per family; by-name carries all.
              "specific_names": sorted({f["name"] for f in members[fam]})[:12],
              "example": members[fam][0]["claim"]} for fam in families]

    index = {"name": current["name"], "description": current["description"],
             "count": len(failures), "families": len(families),
             "distinct_specific_names": len({f["name"] for f in failures}),
             "bulk": current["bulk"], "modes": modes, "failures": failures}

    by_name = {}
    for fam in families:
        entries = []
        for f in members[fam]:
            c = by_id[f["id"]]
            entries.append({"id": f["id"], "url": f["url"], "claim": f["claim"],
                            "specific_name": f["name"], "conditions": f["conditions"],
                            "source": titles.get(c["source_sha256"], ""), "year": c["year"],
                            "quote": c["supporting_quote"], "citation": c["citation"]})
        by_name[fam] = {"failure_mode": fam,
                        "specific_names": sorted({f["name"] for f in members[fam]}),
                        "count": counts[fam], "claims": entries}
    return index, by_name, members, counts, families


def esc(text):
    return html.escape(text, quote=True)


def family_page(fam, entries, works):
    items = "".join(
        f'<li><a href="../claims/{f["id"].split(":")[-1]}.html">{esc(f["name"])}</a>: '
        f'{esc(f["claim"][:150])}</li>' for f in entries)
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>Failure mode: {esc(fam)}</title>'
        f'<meta name="description" content="{len(entries)} claims on {esc(fam)} from the '
        'published works of Wulf A. Kaal">'
        '<link rel="stylesheet" href="../style.css"></head><body><main>'
        '<h1>failure family</h1>'
        f'<p class="claim">{esc(fam.replace("-", " "))}</p>'
        # Both 2026-09-06 families draw on a single paper; no earlier family did, so the
        # plural rule changes nothing for the 55 that already existed.
        f'<p class="meta">{len(entries)} claims across {works} work{"" if works == 1 else "s"}.</p>'
        f'<ul>{items}</ul>'
        "<footer><a href='./index.html'>All failure families</a> &middot; "
        "<a href='../claims/index.html'>All claims</a></footer></main></body></html>")


def index_page(total, families, counts):
    rows = "".join(
        f'<tr><td><a href="./{fam}.html">{esc(fam.replace("-", " "))}</a></td>'
        f'<td>{counts[fam]}</td></tr>' for fam in families)
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Failure Mode Index, Kaal Corpus</title>'
        '<meta name="description" content="Structured index of failure modes in decentralized '
        'governance, DAOs, reputation systems, and regulation, from the published works of '
        'Wulf A. Kaal."><link rel="stylesheet" href="../style.css"></head><body><main>'
        '<h1>failure mode index</h1>'
        '<p class="claim">How these systems break, and under what conditions.</p>'
        f'<p class="meta">{total} claims in {len(families)} families, drawn from the published '
        'works of Wulf A. Kaal. Machine readable: <a href="./index.json">index.json</a>.</p>'
        f'<table><tr><th>Family</th><th>Claims</th></tr>{rows}</table>'
        '<footer><a href="../claims/index.html">All claims</a> &middot; '
        '<a href="https://wulfkaal.com/agents/">Wulf A. Kaal</a></footer></main></body></html>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classify", help="JSON list of {id, family, specific_name} to add")
    ap.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = ap.parse_args()
    extra = load(pathlib.Path(args.classify)) if args.classify else []

    index, by_name, members, counts, families = build(extra)
    claims = {c["id"]: c for c in load(ROOT / "claims" / "index.json")["claims"]}
    uncovered = {c for c, v in claims.items() if v.get("is_failure_mode")} - {f["id"] for f in index["failures"]}

    print(f"  failure-mode claims covered : {index['count']}")
    print(f"  families                    : {index['families']}")
    print(f"  distinct specific names     : {index['distinct_specific_names']}")
    print(f"  still unclassified          : {len(uncovered)}")
    if args.dry_run:
        return

    out = ROOT / "failures"
    dump(out / "index.json", index)
    for fam, doc in by_name.items():
        dump(out / "by-name" / f"{fam}.json", doc)
    for fam in families:
        works = len({claims[f["id"]]["source_sha256"] for f in members[fam]})
        (out / f"{fam}.html").write_text(family_page(fam, members[fam], works), encoding="utf-8")
    (out / "index.html").write_text(index_page(index["count"], families, counts), encoding="utf-8")


if __name__ == "__main__":
    main()

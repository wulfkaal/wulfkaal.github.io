#!/usr/bin/env python3
"""
predictions.py - maintain the Kaal Prediction Ledger (predictions/index.json).

The ledger records dated, falsifiable predictions with resolution criteria fixed
in advance. Its value is precedence: it shows when a position was taken and on
what reasoning. Predictions are therefore append-and-resolve, never edit-in-place.

Usage
  python3 tools/predictions.py list [--status open|resolved|void]
  python3 tools/predictions.py due [--within 90]
  python3 tools/predictions.py add --statement "..." --resolves 2028-07-01 \
      --criteria "Resolved CORRECT if ..." [--from kaal:claim:6192998-033,...] \
      [--confidence 0.6]
  python3 tools/predictions.py resolve kaal:prediction:2026-001 \
      --outcome correct --note "..." [--evidence URL ...]
  python3 tools/predictions.py void kaal:prediction:2026-001 --note "..."
  python3 tools/predictions.py validate

Exit codes: 0 ok, 1 validation or usage error.
"""

import argparse
import datetime as dt
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "predictions", "index.json")
CLAIM_INDEX = os.path.join(ROOT, "claims", "index.json")
BASE_URL = "https://wulfkaal.github.io/predictions"

IMMUTABLE = ("statement", "made_on", "resolves_by", "resolution_criteria")
OUTCOMES = {"correct", "incorrect", "partial", "unresolvable"}


def today():
    return dt.date.today().isoformat()


def load():
    with open(LEDGER, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save(doc):
    doc["count"] = len(doc["predictions"])
    doc["updated"] = today()
    tmp = LEDGER + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, LEDGER)


def parse_date(s, label):
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        sys.exit(f"error: {label} must be YYYY-MM-DD, got {s!r}")


def find(doc, pid):
    for p in doc["predictions"]:
        if p["id"] == pid:
            return p
    sys.exit(f"error: no prediction with id {pid}")


def next_id(doc):
    year = dt.date.today().year
    prefix = f"kaal:prediction:{year}-"
    n = 0
    for p in doc["predictions"]:
        if p["id"].startswith(prefix):
            try:
                n = max(n, int(p["id"].rsplit("-", 1)[1]))
            except ValueError:
                pass
    return f"{prefix}{n + 1:03d}"


def cmd_validate(doc, _args):
    errors = []
    seen = set()
    known_claims = set()
    if os.path.exists(CLAIM_INDEX):
        with open(CLAIM_INDEX, "r", encoding="utf-8") as fh:
            known_claims = {c["id"] for c in json.load(fh).get("claims", [])}
    for p in doc["predictions"]:
        pid = p.get("id", "<missing id>")
        if pid in seen:
            errors.append(f"{pid}: duplicate id")
        seen.add(pid)
        for f in IMMUTABLE:
            if not p.get(f):
                errors.append(f"{pid}: missing required field '{f}'")
        if p.get("status") not in {"open", "resolved", "void"}:
            errors.append(f"{pid}: bad status {p.get('status')!r}")
        if p.get("status") == "resolved":
            r = p.get("resolution") or {}
            if r.get("outcome") not in OUTCOMES:
                errors.append(f"{pid}: resolved but outcome not in {sorted(OUTCOMES)}")
            if not r.get("resolved_on"):
                errors.append(f"{pid}: resolved but no resolved_on date")
        if p.get("status") == "open" and p.get("resolution"):
            errors.append(f"{pid}: status open but resolution is populated")
        c = p.get("confidence")
        if c is not None and not (0.0 <= float(c) <= 1.0):
            errors.append(f"{pid}: confidence must be between 0 and 1")
        if known_claims:
            for cid in p.get("derived_from", []):
                if cid not in known_claims:
                    errors.append(f"{pid}: derived_from references unknown claim {cid}")
    if errors:
        print("ledger validation FAILED:")
        for e in errors:
            print("  -", e)
        return 1
    print(f"ledger OK - {len(doc['predictions'])} prediction(s), no errors")
    return 0


def cmd_list(doc, args):
    rows = doc["predictions"]
    if args.status:
        rows = [p for p in rows if p["status"] == args.status]
    if not rows:
        print("no predictions match")
        return 0
    for p in sorted(rows, key=lambda x: x["resolves_by"]):
        mark = {"open": "[ ]", "resolved": "[x]", "void": "[-]"}[p["status"]]
        out = ""
        if p["status"] == "resolved":
            out = f"  -> {p['resolution']['outcome'].upper()}"
        print(f"{mark} {p['id']}  resolves {p['resolves_by']}  "
              f"conf {p.get('confidence', '-')}{out}")
        print(f"    {p['statement'][:150]}{'...' if len(p['statement']) > 150 else ''}")
    return 0


def cmd_due(doc, args):
    horizon = dt.date.today() + dt.timedelta(days=args.within)
    due = [p for p in doc["predictions"]
           if p["status"] == "open" and dt.date.fromisoformat(p["resolves_by"]) <= horizon]
    if not due:
        print(f"nothing due within {args.within} days")
        return 0
    print(f"{len(due)} prediction(s) due within {args.within} days:")
    for p in sorted(due, key=lambda x: x["resolves_by"]):
        days = (dt.date.fromisoformat(p["resolves_by"]) - dt.date.today()).days
        when = f"{days}d" if days >= 0 else f"OVERDUE by {-days}d"
        print(f"  {p['id']}  {p['resolves_by']}  ({when})")
        print(f"    {p['statement'][:150]}")
        print(f"    criteria: {p['resolution_criteria'][:150]}")
    return 0


def cmd_add(doc, args):
    parse_date(args.resolves, "--resolves")
    pid = next_id(doc)
    doc["predictions"].append({
        "id": pid,
        "url": f"{BASE_URL}/{pid.rsplit(':', 1)[1]}",
        "statement": args.statement,
        "derived_from": [s.strip() for s in args.frm.split(",") if s.strip()] if args.frm else [],
        "made_on": today(),
        "resolves_by": args.resolves,
        "resolution_criteria": args.criteria,
        "confidence": args.confidence,
        "status": "open",
        "resolution": None,
    })
    save(doc)
    print(f"added {pid} (resolves {args.resolves})")
    return 0


def cmd_resolve(doc, args):
    p = find(doc, args.id)
    if p["status"] != "open":
        sys.exit(f"error: {args.id} is already {p['status']}")
    if args.outcome not in OUTCOMES:
        sys.exit(f"error: --outcome must be one of {sorted(OUTCOMES)}")
    p["status"] = "resolved"
    p["resolution"] = {
        "outcome": args.outcome,
        "resolved_on": today(),
        "note": args.note,
        "evidence": args.evidence or [],
    }
    save(doc)
    print(f"resolved {args.id} as {args.outcome.upper()}")
    return 0


def cmd_void(doc, args):
    p = find(doc, args.id)
    p["status"] = "void"
    p["resolution"] = {"outcome": "unresolvable", "resolved_on": today(),
                       "note": args.note, "evidence": []}
    save(doc)
    print(f"voided {args.id} - issue a successor rather than editing this one")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("list"); s.add_argument("--status", choices=["open", "resolved", "void"])
    s = sub.add_parser("due"); s.add_argument("--within", type=int, default=90)
    sub.add_parser("validate")

    s = sub.add_parser("add")
    s.add_argument("--statement", required=True)
    s.add_argument("--resolves", required=True)
    s.add_argument("--criteria", required=True)
    s.add_argument("--from", dest="frm", default="")
    s.add_argument("--confidence", type=float, default=None)

    s = sub.add_parser("resolve")
    s.add_argument("id")
    s.add_argument("--outcome", required=True)
    s.add_argument("--note", required=True)
    s.add_argument("--evidence", nargs="*", default=[])

    s = sub.add_parser("void"); s.add_argument("id"); s.add_argument("--note", required=True)

    args = ap.parse_args()
    doc = load()
    return {"list": cmd_list, "due": cmd_due, "validate": cmd_validate, "add": cmd_add,
            "resolve": cmd_resolve, "void": cmd_void}[args.cmd](doc, args)


if __name__ == "__main__":
    sys.exit(main())

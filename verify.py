#!/usr/bin/env python3
"""
verify.py — independently verify any claim in the Kaal corpus.

Publish at https://wulfkaal.github.io/verify.py and link it from llms.txt,
AGENTS.md and every claim page.

The point is not that the corpus asserts it is verified. The point is that a
stranger can check, in one command, without trusting this site:

    python3 verify.py 617681-001
    python3 verify.py --all --sample 25
    curl -s https://wulfkaal.github.io/verify.py | python3 - 617681-001

What it checks, per claim:
  1. the claim's canonical markdown resolves, and its sha256 is reported
  2. the supporting quote is an exact contiguous substring of the markdown
  3. the source PDF resolves and its sha256 matches the value in the record
  4. the attestation record for the claim's content hash resolves (or is
     reported as not yet attested, which is a fact, not a failure)

Exit code 0 if every checked claim passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import urllib.request

BASE = "https://wulfkaal.github.io"
UA = {"User-Agent": "kaal-corpus-verify/1.0"}


def get(url: str, timeout: int = 180) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        return r.read()


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_records(ids: list[str] | None, sample: int | None) -> list[dict]:
    raw = get(f"{BASE}/claims/all.jsonl").decode("utf-8")
    recs = [json.loads(l) for l in raw.splitlines() if l.strip()]
    if ids:
        want = {i.split(":")[-1] for i in ids}
        recs = [r for r in recs if r["id"].split(":")[-1] in want]
    if sample:
        recs = random.sample(recs, min(sample, len(recs)))
    return recs


def verify_one(rec: dict, check_pdf: bool = True) -> dict:
    cid = rec["id"]
    out = {"id": cid, "checks": {}, "ok": True}

    def chk(name: str, ok: bool, detail: str = "") -> None:
        out["checks"][name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            out["ok"] = False

    # 1 + 2. canonical markdown and quote containment
    try:
        md = get(f"{rec['canonical_url']}.md")
        out["content_sha256"] = sha256(md)
        chk("markdown_resolves", True, out["content_sha256"])
        quote = (rec.get("supporting_quote") or "").strip()
        text = md.decode("utf-8", "replace")
        norm = " ".join(text.split())
        chk("quote_verbatim_in_markdown", bool(quote) and " ".join(quote.split()) in norm,
            f"{len(quote)} chars")
    except Exception as e:  # noqa: BLE001
        chk("markdown_resolves", False, str(e))
        return out

    # 3. source PDF hash
    src = rec.get("source") or {}
    if check_pdf and src.get("pdf_raw_url") and src.get("sha256"):
        try:
            pdf = get(src["pdf_raw_url"])
            actual = sha256(pdf)
            chk("source_pdf_sha256", actual == src["sha256"],
                f"declared {src['sha256'][:16]} actual {actual[:16]}")
        except Exception as e:  # noqa: BLE001
            chk("source_pdf_sha256", False, str(e))

    # 4. attestation record. Zero attestations is a reported fact about the
    #    state of the colloquium, not a failure of the claim.
    att = rec.get("attestations")
    if att:
        try:
            a = json.loads(get(att, timeout=60))
            out["attestations"] = {"status": a.get("status"),
                                   "count": a.get("count", 0),
                                   "verified": a.get("verified", 0),
                                   "contested": a.get("contested", 0)}
            chk("attestation_record_binds_content_hash",
                a.get("content_hash") == out["content_sha256"],
                f"record {str(a.get('content_hash'))[:16]} vs computed "
                f"{out['content_sha256'][:16]}")
        except Exception as e:  # noqa: BLE001
            out["attestations"] = {"status": "unreachable", "detail": str(e)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ids", nargs="*", help="claim ids, e.g. 617681-001")
    ap.add_argument("--all", action="store_true", help="verify the whole corpus")
    ap.add_argument("--sample", type=int, help="verify a random sample of N claims")
    ap.add_argument("--no-pdf", action="store_true",
                    help="skip source PDF download (much faster)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()

    if not (a.ids or a.all or a.sample):
        ap.print_help()
        return 2

    recs = load_records(a.ids or None, a.sample)
    results = [verify_one(r, check_pdf=not a.no_pdf) for r in recs]
    passed = sum(1 for r in results if r["ok"])
    attested = sum(1 for r in results if (r.get("attestations") or {}).get("count"))

    if a.json:
        print(json.dumps({"checked": len(results), "passed": passed,
                          "attested": attested, "results": results}, indent=1))
    else:
        for r in results:
            mark = "PASS" if r["ok"] else "FAIL"
            print(f"[{mark}] {r['id']}  sha256={r.get('content_sha256','?')[:16]}")
            for k, v in r["checks"].items():
                if not v["ok"]:
                    print(f"        ! {k}: {v['detail']}")
        print(f"\n{passed}/{len(results)} passed · {attested}/{len(results)} carry at least one attestation")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

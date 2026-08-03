#!/usr/bin/env python3
"""
verify_graph_release.py

Verify the Agentic Claim Graph release chain end to end:

    graph.jsonld  ->  manifest.json  ->  updates.json  ->  signing-keys.json

Exit 0 if every check passes, 1 otherwise. Safe to run in CI.

    python3 verify_graph_release.py                      # the live published surfaces
    python3 verify_graph_release.py agentic-claim-graph/v1   # a local directory

WHAT IS CHECKED
---------------
1. sha256(graph.jsonld) equals manifest.graph_sha256.
2. The current update record attests to that same digest.
   Superseded records legitimately describe earlier builds and are exempt: that
   is what makes the feed a history rather than a single mutable statement.
3. Every record, current and superseded, still verifies against its own
   signature. A superseded record whose signature broke means someone edited a
   signed object in place.
4. If signing-keys.json exists, the current record is signed by the key that
   file marks current, and no retired key is presented as current.

CANONICALISATION
----------------
    body = {k: v for k, v in record.items() if k not in SIG_FIELDS}
    payload = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()

Recovered from the original release record and confirmed by reproducing its
signed_payload_sha256 and validating its Ed25519 signature.
"""

import hashlib
import json
import sys
import urllib.request

BASE = "https://wulfkaal.github.io/agentic-claim-graph/v1"

SIG_FIELDS = {
    "signature",
    "signature_algorithm",
    "signing_public_key_pem",
    "signing_key_id",
    "signed_payload_sha256",
    "signature_status",
}

OK, NO = "PASS", "FAIL"


def canonical_payload(record: dict) -> bytes:
    body = {k: v for k, v in record.items() if k not in SIG_FIELDS}
    return json.dumps(body, separators=(",", ":"), sort_keys=True).encode()


def fetch(where: str, name: str, required: bool = True):
    try:
        if where.startswith("http"):
            req = urllib.request.Request(
                "%s/%s" % (where, name), headers={"User-Agent": "kaal-verify/1.1"}
            )
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        with open("%s/%s" % (where, name), "rb") as fh:
            return fh.read()
    except Exception:
        if required:
            raise
        return None


def main() -> int:
    where = sys.argv[1] if len(sys.argv) > 1 else BASE
    print("source: %s\n" % where)

    graph_bytes = fetch(where, "graph.jsonld")
    manifest = json.loads(fetch(where, "manifest.json"))
    feed = json.loads(fetch(where, "updates.json"))
    raw_keys = fetch(where, "signing-keys.json", required=False)
    keyhist = json.loads(raw_keys) if raw_keys else None

    failures = 0

    actual = hashlib.sha256(graph_bytes).hexdigest()
    declared = manifest.get("graph_sha256")
    good = actual == declared
    failures += 0 if good else 1
    print("[%s] graph.jsonld digest matches manifest.graph_sha256" % (OK if good else NO))
    print("        computed %s" % actual)
    print("        manifest %s\n" % declared)

    records = feed.get("updates", [])
    superseded = {r.get("supersedes") for r in records if r.get("supersedes")}
    declared_current = feed.get("current_update_id")

    current_seen = 0
    current_pub = None

    for i, upd in enumerate(records):
        uid = upd.get("update_id", "index %d" % i)
        is_current = (uid == declared_current) if declared_current else (uid not in superseded)
        if is_current:
            current_seen += 1
            current_pub = upd.get("signing_public_key_pem")
        print("  update %s%s" % (uid, "" if is_current else "  (superseded)"))

        u_graph = upd.get("graph_sha256")
        if is_current:
            good = u_graph == actual
            failures += 0 if good else 1
            print("  [%s] graph_sha256 matches the published graph" % (OK if good else NO))
            if not good:
                print("          published %s" % actual)
                print("          attested  %s" % u_graph)
                print("          a valid signature over a statement about a different artifact")
                print("          is worse than no signature: the chain does not close")
        else:
            print("  [INFO] attests to an earlier graph %s..., exempt" % str(u_graph)[:16])

        payload = canonical_payload(upd)
        p_actual = hashlib.sha256(payload).hexdigest()
        good = p_actual == upd.get("signed_payload_sha256")
        failures += 0 if good else 1
        print("  [%s] canonical payload digest matches signed_payload_sha256" % (OK if good else NO))
        if not good:
            print("          computed %s" % p_actual)
            print("          declared %s" % upd.get("signed_payload_sha256"))

        try:
            import base64

            from cryptography.hazmat.primitives.serialization import load_pem_public_key

            pub = load_pem_public_key(upd["signing_public_key_pem"].encode())
            pub.verify(base64.b64decode(upd["signature"]), payload)
            print("  [%s] Ed25519 signature verifies" % OK)
        except ImportError:
            print("  [SKIP] install 'cryptography' to check the signature")
        except Exception as exc:
            failures += 1
            print("  [%s] Ed25519 signature does not verify: %s" % (NO, type(exc).__name__))
            if not (uid == declared_current or uid not in superseded):
                print("          this record is superseded, so a broken signature means it was")
                print("          edited in place after signing rather than left immutable")
        print()

    good = current_seen == 1
    failures += 0 if good else 1
    print("[%s] exactly one current record (found %d)" % (OK if good else NO, current_seen))

    if keyhist:
        keys = keyhist.get("keys", [])
        cur = [k for k in keys if k.get("status") == "current"]
        good = len(cur) == 1
        failures += 0 if good else 1
        print("[%s] signing-keys.json names exactly one current key (found %d)"
              % (OK if good else NO, len(cur)))
        if cur and current_pub:
            good = cur[0].get("public_key_pem") == current_pub
            failures += 0 if good else 1
            print("[%s] current record is signed by the current key" % (OK if good else NO))
            if cur[0].get("succession_proof") == "none":
                print("      NOTE: this key claims succession without proof from the previous")
                print("      key. It is authenticated by control of the publishing origin.")
    else:
        print("[INFO] no signing-keys.json; key history not published")

    print("\n" + "=" * 66)
    if failures:
        print("%d check(s) FAILED" % failures)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

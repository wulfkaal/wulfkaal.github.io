#!/usr/bin/env python3
"""
graph_sign.py

Issue a signed release record for the Agentic Claim Graph, and manage the
signing key history that makes the record checkable.

Three situations, one command:

  1. Nothing to do. The current record already attests to the published graph.
  2. Normal re-sign. You hold the key that signed the last record.
  3. Rotation. The previous signing key is unavailable and a new one takes over.

Situation 3 is not a cleanup, it is an identity event, so it requires an explicit
--rotate flag and it records the reason in a public key history.

    # first time, generate a key and issue the first record under it
    python3 tools/graph_sign.py --dir agentic-claim-graph/v1 \
        --key ~/.kaal-tools/graph-signing-key.pem --new-key --rotate \
        --reason "Prior key was generated in an ephemeral build worktree and not persisted."

    # afterwards, ordinary re-signing needs no flags beyond the key
    python3 tools/graph_sign.py --dir agentic-claim-graph/v1 \
        --key ~/.kaal-tools/graph-signing-key.pem

    # preview anything without writing
    python3 tools/graph_sign.py ... --dry-run

WHAT A ROTATION CAN AND CANNOT PROVE
------------------------------------
When the old private key still exists, a rotation can be signed by the outgoing
key, which cryptographically binds old identity to new. When the old key is
lost, that link cannot be made. Anyone can generate a key and assert succession.

So a lost-key rotation is authenticated by control of the publishing origin
(the repository and the domain serving these files), not by the old key. That is
a weaker claim and this script writes it down as such in signing-keys.json,
rather than presenting the new key as if the succession were proven. A reader
who is told the truth can weigh it. A reader who is not will over-trust it.

CANONICALISATION
----------------
The signed payload is, and must remain:

    body = {k: v for k, v in record.items() if k not in SIG_FIELDS}
    payload = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()

This matches the original release record, verified by reproducing its
signed_payload_sha256 and validating its Ed25519 signature.
"""

import argparse
import base64
import hashlib
import json
import os
import stat
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
    load_pem_public_key,
)

SIG_FIELDS = {
    "signature",
    "signature_algorithm",
    "signing_public_key_pem",
    "signing_key_id",
    "signed_payload_sha256",
    "signature_status",
}


def canonical_payload(record: dict) -> bytes:
    body = {k: v for k, v in record.items() if k not in SIG_FIELDS}
    return json.dumps(body, separators=(",", ":"), sort_keys=True).encode()


def raw_pub(pem: str) -> bytes:
    return load_pem_public_key(pem.encode()).public_bytes(Encoding.Raw, PublicFormat.Raw)


def current_record(feed: dict):
    """The record nothing else supersedes."""
    records = feed.get("updates", [])
    if not records:
        return None
    superseded = {r.get("supersedes") for r in records if r.get("supersedes")}
    live = [r for r in records if r.get("update_id") not in superseded]
    return live[-1] if live else records[-1]


def load_or_create_key(path: str, allow_create: bool, dry_run: bool):
    path = os.path.expanduser(path)
    if os.path.exists(path):
        key = load_pem_private_key(open(path, "rb").read(), password=None)
        if not isinstance(key, Ed25519PrivateKey):
            sys.exit("ABORT: key at %s is not an Ed25519 key." % path)
        return key, False
    if not allow_create:
        sys.exit(
            "ABORT: no key at %s.\n"
            "Pass --new-key to generate one. Generating a key is only correct when\n"
            "you are deliberately rotating, so --new-key also requires --rotate." % path
        )
    key = Ed25519PrivateKey.generate()
    if dry_run:
        print("would generate a new Ed25519 key at %s" % path)
        return key, True
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    print("generated a new Ed25519 signing key at %s (mode 0600)" % path)
    return key, True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="agentic-claim-graph/v1 directory")
    ap.add_argument("--key", required=True, help="PEM Ed25519 private key path")
    ap.add_argument("--new-key", action="store_true", help="generate the key if absent")
    ap.add_argument("--rotate", action="store_true", help="acknowledge a signing identity change")
    ap.add_argument("--reason", default="", help="why the previous key is unavailable")
    ap.add_argument("--key-id", default=None, help="identifier for the new key")
    ap.add_argument("--as-of", default=None, help="ISO date for the key history, e.g. 2026-08-03")
    ap.add_argument("--change-type", default=None,
                    help="what this record attests, e.g. eligible_set_expansion; "
                         "defaults to digest_correction, which is only right when the "
                         "graph bytes changed without a change in scope")
    ap.add_argument("--supersedes-reason", default=None,
                    help="why the prior record is superseded, stated accurately")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    d = args.dir.rstrip("/")
    graph_bytes = open("%s/graph.jsonld" % d, "rb").read()
    manifest = json.load(open("%s/manifest.json" % d))
    feed = json.load(open("%s/updates.json" % d))

    digest = hashlib.sha256(graph_bytes).hexdigest()
    print("graph.jsonld sha256   %s" % digest)
    print("manifest.graph_sha256 %s" % manifest.get("graph_sha256"))

    if digest != manifest.get("graph_sha256"):
        print("\nABORT: manifest.json does not describe graph.jsonld.")
        print("Rebuild the manifest first. Signing against a stale manifest moves the")
        print("inconsistency instead of removing it.")
        return 1

    prior = current_record(feed)
    if prior and prior.get("graph_sha256") == digest:
        print("\nNothing to do: the current record already attests to the published graph.")
        return 0

    if args.new_key and not args.rotate:
        print("\nABORT: --new-key without --rotate.")
        print("A new key changes who vouches for this graph. Say so explicitly.")
        return 1

    key, created = load_or_create_key(args.key, args.new_key, args.dry_run)
    pub_pem = key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode()

    prior_pub = (prior or {}).get("signing_public_key_pem", "")
    rotating = bool(prior_pub) and raw_pub(prior_pub) != key.public_key().public_bytes(
        Encoding.Raw, PublicFormat.Raw
    )

    if rotating and not args.rotate:
        print("\nABORT: this key differs from the one that signed the current record.")
        print("Signing anyway would silently rotate the graph's identity.")
        print("If the rotation is intended, pass --rotate and --reason.")
        return 1
    if rotating and not args.reason:
        print("\nABORT: --rotate needs --reason. An unexplained key change is indistinguishable")
        print("from a compromise, and a reader has no way to tell them apart.")
        return 1

    as_of = args.as_of or "unspecified-date"
    key_id = args.key_id or "kaal:graph-signing-key:%s" % as_of

    body = {
        "update_version": "1.0.1",
        "update_id": "kaal:update:%s" % hashlib.sha256(
            (digest + (prior or {}).get("graph_id", "") + key_id).encode()
        ).hexdigest()[:24],
        "graph_id": manifest.get("graph_id") or (prior or {}).get("graph_id"),
        "graph_sha256": digest,
        "claim_count": manifest.get("claim_count"),
        "change_type": args.change_type
        or ("digest_correction_under_rotated_key" if rotating else "digest_correction"),
        "lifecycle_status": "current",
    }
    if prior:
        body["supersedes"] = prior["update_id"]
        body["supersedes_reason"] = args.supersedes_reason or (
            "The superseded record attested to a graph build that was never published. "
            "Its signature is valid; its subject was not the served artifact."
        )
    if rotating:
        body["key_rotation"] = {
            "previous_key_status": "unavailable",
            "reason": args.reason,
            "succession_proof": "none",
            "authenticated_by": "control of the publishing origin, not by the previous key",
        }

    payload = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
    record = dict(body)
    record["signature_status"] = "signed"
    record["signature"] = base64.b64encode(key.sign(payload)).decode()
    record["signature_algorithm"] = "Ed25519"
    record["signing_key_id"] = key_id
    record["signing_public_key_pem"] = pub_pem
    record["signed_payload_sha256"] = hashlib.sha256(payload).hexdigest()

    # self check
    load_pem_public_key(pub_pem.encode()).verify(base64.b64decode(record["signature"]), payload)
    assert hashlib.sha256(canonical_payload(record)).hexdigest() == record["signed_payload_sha256"]
    print("self check            new record verifies against its own signature")

    # The prior record is never modified. Editing a signed record invalidates its
    # signature, which is the defect this tooling exists to repair.
    feed_out = {
        "feed_version": "1.1.0",
        "current_update_id": record["update_id"],
        "signing_keys": "https://wulfkaal.github.io/agentic-claim-graph/v1/signing-keys.json",
        "updates": (feed.get("updates", []) + [record]),
    }

    keys_path = "%s/signing-keys.json" % d
    try:
        history = json.load(open(keys_path))
    except Exception:
        history = {"history_version": "1.0.0", "keys": []}
    known = {k.get("public_key_pem") for k in history["keys"]}
    if prior_pub and prior_pub not in known:
        history["keys"].append(
            {
                "key_id": (prior or {}).get("signing_key_id", "kaal:graph-signing-key:original"),
                "public_key_pem": prior_pub,
                "status": "retired" if rotating else "current",
                "retired_reason": args.reason if rotating else None,
                "note": "Signed the initial release record. Signature remains verifiable.",
            }
        )
    if pub_pem not in known:
        history["keys"].append(
            {
                "key_id": key_id,
                "public_key_pem": pub_pem,
                "status": "current",
                "created": as_of,
                "succession_proof": "none" if rotating else "same key as previous",
                "authenticated_by": (
                    "control of the publishing origin, not by the previous key"
                    if rotating
                    else "continuity of the signing key"
                ),
            }
        )
    for k in history["keys"]:
        if k.get("public_key_pem") != pub_pem and k.get("status") == "current":
            k["status"] = "retired"

    feed_json = json.dumps(feed_out, indent=2) + "\n"
    keys_json = json.dumps(history, indent=2) + "\n"

    if args.dry_run:
        print("\n--- updates.json (dry run) ---\n" + feed_json)
        print("--- signing-keys.json (dry run) ---\n" + keys_json)
        return 0

    open("%s/updates.json" % d, "w").write(feed_json)
    open(keys_path, "w").write(keys_json)
    print("\nwrote %s/updates.json" % d)
    print("wrote %s" % keys_path)
    if created:
        print("\nBack up the private key now. If it is lost again, the next rotation has the")
        print("same unprovable succession problem as this one:")
        print("    security add-generic-password -s kaal-graph-signing -a wulf \\")
        print("      -w \"$(cat %s)\" -U" % os.path.expanduser(args.key))
    print("\nNow run: python3 tools/verify_graph_release.py %s" % d)
    return 0


if __name__ == "__main__":
    sys.exit(main())

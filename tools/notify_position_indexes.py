#!/usr/bin/env python3
"""Notify IndexNow only from a complete, live-verified position receipt.

The command is intentionally separate from publication. Missing credentials
produce a receipt that says no notification occurred; they never weaken the
live-verification gate or make publication fail.
"""

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


BASE = "https://wulfkaal.github.io"
INDEXNOW = "https://api.indexnow.org/indexnow"
UA = "kaal-position-index-notifier/1.0"
DEFAULT_KEY_FILE = Path(__file__).resolve().parents[1] / "indexnow-key.txt"


def fetch(url, method="GET", payload=None, headers=None, attempts=6):
    error = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                data=payload,
                method=method,
                headers={"User-Agent": UA, **(headers or {})},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            error = exc
            if attempt + 1 < attempts:
                time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"live request failed after {attempts} attempts: {url}: {error}")


def write_receipt(path, receipt):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publication-receipt", type=Path, required=True)
    parser.add_argument("--output-receipt", type=Path, required=True)
    args = parser.parse_args()

    source_bytes = args.publication_receipt.read_bytes()
    source = json.loads(source_bytes)
    live = source.get("liveVerification") or {}
    protected = source.get("protectedInvariant") or {}
    published = source.get("publishedIds") or []
    commit = source.get("commit") or ""
    gates = {
        "status": source.get("status") == "live-verified-publication-complete",
        "commit": bool(re.fullmatch(r"[a-f0-9]{40}", commit)),
        "published_ids": bool(published),
        "all_http_200": live.get("allHttp200") is True,
        "byte_identical_to_commit": live.get("allByteIdenticalToCanonicalCommit") is True,
        "sitemaps_verified": live.get("sitemapsVerified") is True,
        "protected_count": isinstance(protected.get("count"), int) and protected.get("count") > 0,
        "protected_length": protected.get("length") == protected.get("count"),
        "protected_sha256": bool(re.fullmatch(r"[a-f0-9]{64}", protected.get("sha256") or "")),
        "protected_live_identical": protected.get("localLiveByteIdentical") is True,
    }
    if not all(gates.values()):
        raise SystemExit(f"FAIL CLOSED: publication receipt gates failed: {gates}")

    urls = [
        f"{BASE}/positions/{identifier.replace('kaal:position:', '')}"
        for identifier in published
    ] + [
        f"{BASE}/positions/",
        f"{BASE}/positions/index.json",
        f"{BASE}/positions/graph.jsonld",
        f"{BASE}/positions/recent.json",
        f"{BASE}/positions/by-date/index.json",
        f"{BASE}/positions/by-topic/index.json",
        f"{BASE}/sitemap-positions.xml",
    ]

    live_index_status, live_index_bytes = fetch(f"{BASE}/positions/index.json")
    live_index = json.loads(live_index_bytes)
    if live_index_status != 200 or live_index.get("numberOfItems") != source.get("after"):
        raise SystemExit("FAIL CLOSED: live position count does not match publication receipt")
    live_claims_status, live_claims_bytes = fetch(f"{BASE}/claims/index.json")
    live_claims = json.loads(live_claims_bytes)
    if (
        live_claims_status != 200
        or live_claims.get("count") != protected.get("count")
        or len(live_claims.get("claims") or []) != protected.get("length")
        or hashlib.sha256(live_claims_bytes).hexdigest() != protected.get("sha256")
    ):
        raise SystemExit("FAIL CLOSED: live protected claims do not match publication receipt")
    for url in urls:
        status, _ = fetch(url)
        if status != 200:
            raise SystemExit(f"FAIL CLOSED: URL is not live: HTTP {status} {url}")

    base_receipt = {
        "schemaVersion": "kaal-search-index-notification-receipt-v1",
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "publicationReceipt": str(args.publication_receipt),
        "publicationReceiptSha256": hashlib.sha256(source_bytes).hexdigest(),
        "commit": commit,
        "batchId": source.get("batchId"),
        "verifiedUrlCount": len(urls),
        "liveIndexSha256": hashlib.sha256(live_index_bytes).hexdigest(),
        "protectedInvariant": protected,
    }

    key_file = Path(os.environ.get("INDEXNOW_KEY_FILE", str(DEFAULT_KEY_FILE)))
    key = os.environ.get("INDEXNOW_KEY", "").strip()
    if not key and key_file.is_file():
        key = key_file.read_text(encoding="utf-8").strip()
    if not key:
        write_receipt(args.output_receipt, {
            **base_receipt,
            "status": "not-notified-missing-indexnow-key",
            "notificationSent": False,
            "blocker": "IndexNow key is absent from INDEXNOW_KEY and INDEXNOW_KEY_FILE",
        })
        print(json.dumps({
            "notificationSent": False,
            "blocker": "IndexNow key is absent from INDEXNOW_KEY and INDEXNOW_KEY_FILE",
        }))
        return
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", key):
        raise SystemExit("FAIL CLOSED: INDEXNOW_KEY has an invalid format")

    key_location = os.environ.get("INDEXNOW_KEY_LOCATION", f"{BASE}/indexnow-key.txt")
    key_status, key_bytes = fetch(key_location)
    if key_status != 200 or key_bytes.decode("utf-8").strip() != key:
        write_receipt(args.output_receipt, {
            **base_receipt,
            "status": "not-notified-key-location-unverified",
            "notificationSent": False,
            "blocker": "IndexNow key location is not live or does not match",
            "keyLocation": key_location,
        })
        raise SystemExit("FAIL CLOSED: IndexNow key location could not be verified")

    body = json.dumps({
        "host": "wulfkaal.github.io",
        "key": key,
        "keyLocation": key_location,
        "urlList": urls,
    }).encode("utf-8")
    try:
        status, response = fetch(
            INDEXNOW,
            method="POST",
            payload=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            attempts=3,
        )
    except Exception as exc:
        write_receipt(args.output_receipt, {
            **base_receipt,
            "status": "notification-failed",
            "notificationSent": False,
            "blocker": str(exc),
            "keyLocation": key_location,
        })
        raise
    accepted = status in (200, 202)
    write_receipt(args.output_receipt, {
        **base_receipt,
        "status": "notified" if accepted else "notification-failed",
        "notificationSent": accepted,
        "endpoint": INDEXNOW,
        "httpStatus": status,
        "responseSha256": hashlib.sha256(response).hexdigest(),
        "keyLocation": key_location,
        "urls": urls,
    })
    if not accepted:
        raise SystemExit(f"IndexNow returned HTTP {status}")
    print(json.dumps({"notificationSent": True, "httpStatus": status, "urls": len(urls)}))


if __name__ == "__main__":
    main()

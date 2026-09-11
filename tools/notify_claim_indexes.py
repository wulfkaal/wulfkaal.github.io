#!/usr/bin/env python3
"""Tell IndexNow the claim layer exists.

WHY

Common Crawl has never captured wulfkaal.github.io -- zero rows across seven indexes
from 2025-51 to 2026-34, while microsoft.github.io and google.github.io show 60 each in
the same crawl. Crawl discovery follows the link graph, and until 2026-09-10 no
high-authority record pointed at the corpus. Waiting to be found has not worked.

IndexNow is a push: Bing and Yandex accept a signed list of URLs directly, without
waiting for a crawler to arrive. The key is already published and live at
/indexnow-key.txt, and tools/notify_position_indexes.py has been doing this for the
positions layer. Nothing has ever submitted the claim layer.

DISCIPLINE

Modelled on the positions notifier and fail-closed in the same way: every URL is
fetched and must return 200 before anything is submitted, the published key must match
the key file byte for byte, and a receipt records what was sent. Announcing a URL that
404s is worse than announcing nothing -- a dead link in a submission is the first thing
a search engine resolves, and it discounts the siblings.

This tool submits ENTRY POINTS, not leaves. IndexNow rate-limits large batches, and the
indexes enumerate the rest.

LIVE RECEIPTS

A live run requires ``--receipt``. The tool writes the immutable intent before the
external request, then writes ``<receipt>.result.json`` with the response. If transport
fails after the request begins, the result is ``unknown-outcome`` and must not be retried
blindly. A dry run sends nothing and may write a single ``dry-run-verified`` receipt.
"""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://wulfkaal.github.io"
INDEXNOW = "https://api.indexnow.org/indexnow"
DEFAULT_KEY_FILE = pathlib.Path(__file__).resolve().parent.parent / "indexnow-key.txt"
UA = {"User-Agent": f"kaal-claim-index-notifier/1.0 (+{BASE}/)"}

URLS = [
    f"{BASE}/",
    f"{BASE}/claims/",
    f"{BASE}/claims/index.json",
    f"{BASE}/claims/by-topic/",
    f"{BASE}/claims/by-topic/index.json",
    f"{BASE}/failures/index.json",
    f"{BASE}/llms.txt",
    f"{BASE}/.well-known/agent-card.json",
    f"{BASE}/sitemap.xml",
    f"{BASE}/sitemap-index.xml",
]


def fetch(url, method="GET", payload=None, headers=None, attempts=4):
    error = None
    for attempt in range(attempts):
        request = urllib.request.Request(
            url, data=payload, method=method, headers={**UA, **(headers or {})})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            error = exc
            if attempt + 1 < attempts:
                time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"request failed after {attempts} attempts: {url}: {error}")


def write_once(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def result_path(receipt_path):
    return receipt_path.with_name(receipt_path.name + ".result.json")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="verify everything and print the payload; submit nothing")
    ap.add_argument("--receipt", type=pathlib.Path)
    a = ap.parse_args()

    if not a.dry_run and a.receipt is None:
        print("FAIL CLOSED: live notification requires --receipt", file=sys.stderr)
        return 1
    if a.receipt is not None:
        result = result_path(a.receipt)
        if a.receipt.exists() or result.exists():
            print("FAIL CLOSED: receipt or result path already exists", file=sys.stderr)
            return 1

    key = os.environ.get("INDEXNOW_KEY", "").strip()
    if not key and DEFAULT_KEY_FILE.is_file():
        key = DEFAULT_KEY_FILE.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", key or ""):
        print("FAIL CLOSED: no usable IndexNow key", file=sys.stderr)
        return 1

    print(f"verifying {len(URLS)} URLs before announcing any of them...")
    dead = []
    verified = []
    for url in URLS:
        status, body = fetch(url)
        print(f"  {status}  {url}")
        if status != 200:
            dead.append((url, status))
        else:
            verified.append({"url": url, "sha256": hashlib.sha256(body).hexdigest()})
    if dead:
        for url, status in dead:
            print(f"  DEAD {status} {url}", file=sys.stderr)
        print("FAIL CLOSED: refusing to announce a URL that does not resolve",
              file=sys.stderr)
        return 1

    key_location = f"{BASE}/indexnow-key.txt"
    status, body = fetch(key_location)
    if status != 200 or body.decode("utf-8").strip() != key:
        print(f"FAIL CLOSED: {key_location} is not live or does not match the key file",
              file=sys.stderr)
        return 1
    print(f"  key verified at {key_location}")

    payload = {"host": "wulfkaal.github.io", "key": key,
               "keyLocation": key_location, "urlList": URLS}
    payload_bytes = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    intent = {
        "schemaVersion": "kaal-claim-index-notification-intent-v1",
        "recordedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mode": "dry-run" if a.dry_run else "live",
        "verifiedUrlCount": len(URLS),
        "verifiedUrls": verified,
        "keyLocation": key_location,
        "payloadSha256": hashlib.sha256(payload_bytes).hexdigest(),
        "notificationSent": False,
    }

    if a.dry_run:
        if a.receipt is not None:
            write_once(a.receipt, {**intent, "status": "dry-run-verified"})
        print("\nDRY RUN — nothing submitted. Payload that WOULD be sent:")
        print(json.dumps({**payload, "key": "<withheld>"}, indent=2))
        return 0

    # Persist the exact intent before the external request. If the process dies or the
    # request has an ambiguous outcome, the durable intent prevents a blind retry.
    write_once(a.receipt, {**intent, "status": "intent-recorded"})

    try:
        status, response = fetch(
            INDEXNOW, method="POST", payload=payload_bytes,
            headers={"Content-Type": "application/json; charset=utf-8"}, attempts=1)
    except Exception as exc:
        write_once(result_path(a.receipt), {
            "schemaVersion": "kaal-claim-index-notification-result-v1",
            "recordedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "intentSha256": hashlib.sha256(a.receipt.read_bytes()).hexdigest(),
            "status": "unknown-outcome",
            "notificationSent": False,
            "blocker": str(exc),
        })
        print("UNKNOWN OUTCOME: request may have reached IndexNow; do not retry blindly",
              file=sys.stderr)
        return 1
    accepted = status in (200, 202)
    result = {
        "schemaVersion": "kaal-claim-index-notification-result-v1",
        "recordedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "intentSha256": hashlib.sha256(a.receipt.read_bytes()).hexdigest(),
        "status": "notified" if accepted else "notification-failed",
        "httpStatus": status,
        "notificationSent": accepted,
        "responseSha256": hashlib.sha256(response).hexdigest(),
    }
    write_once(result_path(a.receipt), result)
    print(f"\nIndexNow HTTP {status} — {'accepted' if accepted else 'NOT ACCEPTED'}")
    if not accepted:
        print(f"  response sha256: {result['responseSha256']}", file=sys.stderr)
    print(f"  intent: {a.receipt}")
    print(f"  result: {result_path(a.receipt)}")
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())

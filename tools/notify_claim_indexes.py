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
"""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import sys
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
    f"{BASE}/claims/by-topic/index.html",
    f"{BASE}/claims/by-topic/index.json",
    f"{BASE}/failures/index.json",
    f"{BASE}/llms.txt",
    f"{BASE}/.well-known/agent-card.json",
    f"{BASE}/sitemap.xml",
    f"{BASE}/sitemap-index.xml",
]


def fetch(url, method="GET", payload=None, headers=None):
    request = urllib.request.Request(
        url, data=payload, method=method, headers={**UA, **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="verify everything and print the payload; submit nothing")
    ap.add_argument("--receipt", default="")
    a = ap.parse_args()

    print(f"verifying {len(URLS)} URLs before announcing any of them...")
    dead = []
    for url in URLS:
        status, _ = fetch(url)
        print(f"  {status}  {url}")
        if status != 200:
            dead.append((url, status))
    if dead:
        for url, status in dead:
            print(f"  DEAD {status} {url}", file=sys.stderr)
        print("FAIL CLOSED: refusing to announce a URL that does not resolve",
              file=sys.stderr)
        return 1

    key = os.environ.get("INDEXNOW_KEY", "").strip()
    if not key and DEFAULT_KEY_FILE.is_file():
        key = DEFAULT_KEY_FILE.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", key or ""):
        print("FAIL CLOSED: no usable IndexNow key", file=sys.stderr)
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
    receipt = {
        "schemaVersion": "kaal-claim-index-notification-receipt-v1",
        "recordedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "verifiedUrlCount": len(URLS),
        "urls": URLS,
        "keyLocation": key_location,
    }

    if a.dry_run:
        print("\nDRY RUN — nothing submitted. Payload that WOULD be sent:")
        print(json.dumps({**payload, "key": "<withheld>"}, indent=2))
        return 0

    status, response = fetch(
        INDEXNOW, method="POST", payload=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"})
    accepted = status in (200, 202)
    receipt.update({"status": "notified" if accepted else "notification-failed",
                    "httpStatus": status, "notificationSent": accepted,
                    "response": response.decode("utf-8", "replace")[:400]})
    print(f"\nIndexNow HTTP {status} — {'accepted' if accepted else 'NOT ACCEPTED'}")
    if not accepted:
        print(f"  {receipt['response']}", file=sys.stderr)
    if a.receipt:
        pathlib.Path(a.receipt).write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(f"  receipt: {a.receipt}")
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())

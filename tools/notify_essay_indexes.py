#!/usr/bin/env python3
"""Fail-closed IndexNow notifier for the machine-readable essay projections.

Every announced URL is derived from the committed essay index and verified live as
HTTP 200 with a body byte-identical to the corresponding file at local HEAD. Live
runs durably record intent before transport and record an outcome separately.
"""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request


BASE = "https://wulfkaal.github.io"
INDEXNOW = "https://api.indexnow.org/indexnow"
REPO = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_KEY_FILE = REPO / "indexnow-key.txt"
UA = {"User-Agent": f"kaal-essay-index-notifier/1.0 (+{BASE}/)"}


def head_file(relative):
    result = subprocess.run(
        ["git", "-C", str(REPO), "show", f"HEAD:{relative}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"cannot read {relative} from local HEAD: {detail}")
    return result.stdout


def derive_urls():
    index = json.loads(head_file("essays/index.json"))
    urls = [
        f"{BASE}/essays/index.json",
        f"{BASE}/essays/all.jsonl",
        f"{BASE}/essays/graph.jsonld",
    ]
    for record in index["itemListElement"]:
        slug = record["slug"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise RuntimeError(f"unsafe essay slug in committed index: {slug!r}")
        expected = f"{BASE}/essays/{slug}.json"
        if record.get("projection_url") != expected:
            raise RuntimeError(f"essay projection URL does not match slug: {slug!r}")
        urls.append(expected)
    urls.append(f"{BASE}/sitemap-essays.xml")
    if len(urls) != len(set(urls)):
        raise RuntimeError("duplicate URL derived from committed essay index")
    return urls


def committed_body(url):
    prefix = f"{BASE}/"
    if not url.startswith(prefix):
        raise RuntimeError(f"URL is outside the local sitemap host: {url}")
    return head_file(url.removeprefix(prefix))


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="verify everything and submit nothing")
    parser.add_argument("--receipt", type=pathlib.Path)
    args = parser.parse_args()

    if not args.dry_run and args.receipt is None:
        print("FAIL CLOSED: live notification requires --receipt", file=sys.stderr)
        return 1
    if args.receipt is not None:
        result = result_path(args.receipt)
        if args.receipt.exists() or result.exists():
            print("FAIL CLOSED: receipt or result path already exists", file=sys.stderr)
            return 1

    key = os.environ.get("INDEXNOW_KEY", "").strip()
    if not key and DEFAULT_KEY_FILE.is_file():
        key = DEFAULT_KEY_FILE.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", key or ""):
        print("FAIL CLOSED: no usable IndexNow key", file=sys.stderr)
        return 1

    try:
        urls = derive_urls()
        expected = {url: committed_body(url) for url in urls}
    except (RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL CLOSED: cannot derive committed essay URLs: {exc}", file=sys.stderr)
        return 1

    print(f"verifying {len(urls)} URLs before announcing any of them...")
    failed = []
    verified = []
    for url in urls:
        status, body = fetch(url)
        print(f"  {status}  {url}")
        if status != 200:
            failed.append(f"HTTP {status} {url}")
        elif body != expected[url]:
            failed.append(f"byte mismatch {url}")
        else:
            verified.append({"url": url, "sha256": hashlib.sha256(body).hexdigest()})
    if failed:
        for problem in failed:
            print(f"  {problem}", file=sys.stderr)
        print("FAIL CLOSED: live essay projections do not match local HEAD", file=sys.stderr)
        return 1

    key_location = f"{BASE}/indexnow-key.txt"
    status, body = fetch(key_location)
    if status != 200 or body.decode("utf-8", errors="replace").strip() != key:
        print(f"FAIL CLOSED: {key_location} is not live or does not match the key file",
              file=sys.stderr)
        return 1
    print(f"  key verified at {key_location}")

    payload = {
        "host": "wulfkaal.github.io",
        "key": key,
        "keyLocation": key_location,
        "urlList": urls,
    }
    payload_bytes = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    intent = {
        "schemaVersion": "kaal-essay-index-notification-intent-v1",
        "recordedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mode": "dry-run" if args.dry_run else "live",
        "verifiedUrlCount": len(urls),
        "verifiedUrls": verified,
        "urlList": urls,
        "keyLocation": key_location,
        "payloadSha256": hashlib.sha256(payload_bytes).hexdigest(),
        "notificationSent": False,
    }

    if args.dry_run:
        if args.receipt is not None:
            write_once(args.receipt, {**intent, "status": "dry-run-verified"})
        print("\nDRY RUN — nothing submitted. Payload that WOULD be sent:")
        print(json.dumps({**payload, "key": "<withheld>"}, indent=2))
        return 0

    write_once(args.receipt, {**intent, "status": "intent-recorded"})
    try:
        status, response = fetch(
            INDEXNOW, method="POST", payload=payload_bytes,
            headers={"Content-Type": "application/json; charset=utf-8"}, attempts=1)
    except Exception as exc:
        write_once(result_path(args.receipt), {
            "schemaVersion": "kaal-essay-index-notification-result-v1",
            "recordedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "intentSha256": hashlib.sha256(args.receipt.read_bytes()).hexdigest(),
            "status": "unknown-outcome",
            "notificationSent": False,
            "urlList": urls,
            "blocker": str(exc),
        })
        print("UNKNOWN OUTCOME: request may have reached IndexNow; do not retry blindly",
              file=sys.stderr)
        return 1

    accepted = status in (200, 202)
    result = {
        "schemaVersion": "kaal-essay-index-notification-result-v1",
        "recordedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "intentSha256": hashlib.sha256(args.receipt.read_bytes()).hexdigest(),
        "status": "notified" if accepted else "notification-failed",
        "httpStatus": status,
        "notificationSent": accepted,
        "urlList": urls,
        "responseSha256": hashlib.sha256(response).hexdigest(),
    }
    write_once(result_path(args.receipt), result)
    print(f"\nIndexNow HTTP {status} — {'accepted' if accepted else 'NOT ACCEPTED'}")
    print(f"  intent: {args.receipt}")
    print(f"  result: {result_path(args.receipt)}")
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())

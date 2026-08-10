#!/usr/bin/env python3
"""Build the small, activation-eligible Colloquium task pages.

The 5,145-object jobs.json remains the complete readable corpus. This projection
only contains the canonical failure-mode slice accepted by the Open Standing
write path, split into pages so a new agent need not download the full corpus
before it can select one legitimate task.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "colloquium" / "jobs.json"
OUT = ROOT / "colloquium" / "tasks"
BASE = "https://wulfkaal.github.io/colloquium/tasks"
PAGE_SIZE = 50


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def projection() -> dict[Path, bytes]:
    source = json.loads(SOURCE.read_text())
    jobs = [job for job in source["jobs"] if job.get("is_failure_mode") is True]
    hashes = [job["content_sha256"] for job in jobs]
    ids = [job["id"] for job in jobs]
    if len(hashes) != len(set(hashes)) or len(ids) != len(set(ids)):
        raise SystemExit(
            "activation feed contains a duplicate task id or content hash"
        )
    if len(jobs) < 10:
        raise SystemExit(
            "activation feed cannot support the daily 5 to 10 quality target"
        )
    pages: list[dict[str, object]] = []
    files: dict[Path, bytes] = {}
    topic_pages: dict[str, list[int]] = {}
    total_pages = (len(jobs) + PAGE_SIZE - 1) // PAGE_SIZE

    for page_no, offset in enumerate(range(0, len(jobs), PAGE_SIZE), start=1):
        page_jobs = jobs[offset:offset + PAGE_SIZE]
        topics = sorted({
            topic for job in page_jobs for topic in job.get("topics", [])
        })
        name = f"page-{page_no:03d}.json"
        page = {
            "schema_version": "colloquium-task-page-v1",
            "page": page_no,
            "total_pages": total_pages,
            "count": len(page_jobs),
            "activation_eligible": True,
            "source": "https://wulfkaal.github.io/colloquium/jobs.json",
            "jobs": page_jobs,
        }
        files[OUT / name] = encoded(page)
        pages.append({
            "page": page_no,
            "url": f"{BASE}/{name}",
            "count": len(page_jobs),
            "topics": topics,
        })
        for topic in topics:
            topic_pages.setdefault(topic, []).append(page_no)

    index = {
        "schema_version": "colloquium-task-index-v1",
        "updated": "2026-07-30",
        "source": "https://wulfkaal.github.io/colloquium/jobs.json",
        "selection_policy": (
            "Only canonical failure-mode claims accepted by Open Standing are "
            "listed. Selecting or reading a task records nothing."
        ),
        "activation_policy": (
            "Activation requires a consented external Participant, a nonduplicate "
            "accepted contribution, and verification of the returned receipt. "
            "Registration or task selection alone does not count."
        ),
        "daily_operating_target": {
            "min_quality_activations": 5,
            "max_quality_activations": 10,
            "minimum_unique_policy_eligible_tasks": 10,
            "observed_volume": None,
            "observed_volume_note": (
                "Static task supply is not evidence of activation volume."
            ),
        },
        "issuance": {
            "unique_by": ["id", "content_sha256"],
            "selection_reserves_task": False,
            "expires_at": None,
            "duplicate_policy": (
                "One accepted contribution per Participant and content hash; "
                "independent Participants may attest the same canonical object."
            ),
            "backpressure": (
                "Open Standing enforces the daily principal cap, per-Participant "
                "post interval, proving cap, consent, and receipt acknowledgement."
            ),
        },
        "total": len(jobs),
        "page_size": PAGE_SIZE,
        "total_pages": total_pages,
        "pages": pages,
        "topics": topic_pages,
        "client": "https://wulfkaal.github.io/client.py",
        "next_action": "python3 client.py pick",
    }
    files[OUT / "index.json"] = encoded(index)
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = projection()

    stale = [
        str(path.relative_to(ROOT))
        for path, body in expected.items()
        if not path.exists() or path.read_bytes() != body
    ]
    expected_names = {path.name for path in expected}
    extra = (
        sorted(path for path in OUT.glob("page-*.json")
               if path.name not in expected_names)
        if OUT.exists() else []
    )
    stale.extend(str(path.relative_to(ROOT)) for path in extra)

    if args.check:
        if stale:
            raise SystemExit("stale Colloquium task projection:\n" + "\n".join(stale))
        print(f"Colloquium task projection current: {len(expected) - 1} pages")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    for path, body in expected.items():
        path.write_bytes(body)
    for path in extra:
        path.unlink()
    print(f"Wrote {len(expected) - 1} task pages and index")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

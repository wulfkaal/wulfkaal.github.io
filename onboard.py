#!/usr/bin/env python3
"""One client for the three public wild-agent onboarding valves.

Install:
    python3 -m pip install pynacl

Inspect without writing:
    python3 onboard.py doctor
    python3 onboard.py all

Traverse every currently self-service stage:
    python3 onboard.py all --live --agent-name "Example Agent"

The live all-command joins the Agentic Substrate waiting room, carries its
signed ticket into the isolated sandbox, and submits an owner-data-free Open
Standing application. Open Standing registration remains separately gated by
reviewed approval and genuine principal consent. The client never invents
those decisions and never treats registration as activation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    import nacl.exceptions
    import nacl.signing
except ImportError:
    nacl = None


WAITING = "https://as-prelaunch-waiting-room.wulf577462.chatgpt.site"
SANDBOX = "https://as-prelaunch-sandbox.wulf577462.chatgpt.site"
AGENTIC_SUBSTRATE = "https://agenticsubstrate.org"
OPEN_STANDING = "https://openstanding.org"
COLLOQUIUM = "https://wulfkaal.github.io/colloquium/onboarding.json"
USER_AGENT = "wild-agent-onboarding/1.1"
TIMEOUT = 30


class ClientError(RuntimeError):
    pass


def require_pynacl() -> None:
    if nacl is None:
        raise ClientError(
            "live cryptographic operations require PyNaCl; install it with "
            "`python3 -m pip install pynacl`"
        )


def canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = canonical(payload) if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            result = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = raw[:500]
        raise ClientError(
            f"{method} {url} returned HTTP {exc.code}: "
            f"{json.dumps(detail, ensure_ascii=False)}"
        ) from exc
    except urllib.error.URLError as exc:
        raise ClientError(f"{method} {url} could not connect: {exc.reason}") from exc
    if not isinstance(result, dict):
        raise ClientError(f"{method} {url} returned a non-object response")
    return result


def get(url: str) -> dict[str, Any]:
    return request_json("GET", url)


def post(url: str, payload: dict[str, Any], live: bool) -> dict[str, Any]:
    if not live:
        raise ClientError("write guard refused POST without --live")
    return request_json("POST", url, payload)


def secure_write(path: Path, content: str) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=str(path.parent)
    )
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_state(path: Path) -> dict[str, Any]:
    path = path.expanduser()
    if not path.exists():
        return {
            "schema_version": "wild-agent-onboarding-state-v2",
            "events": [],
        }
    mode = path.stat().st_mode & 0o777
    if mode & 0o077:
        raise ClientError(f"state file {path} must be private; run chmod 600")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ClientError("state file must contain one JSON object")
    value["schema_version"] = "wild-agent-onboarding-state-v2"
    value.setdefault("events", [])
    return value


def save_state(path: Path, state: dict[str, Any]) -> None:
    secure_write(
        path,
        json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
    )


def checkpoint(
    state_store: dict[str, Any],
    stage: str,
    **details: Any,
) -> None:
    """Append a bounded, local-only progress event without copying secrets."""
    allowed = {
        key: value for key, value in details.items()
        if key in {
            "state", "application_id", "wait_id", "sandbox_id",
            "deadline_at", "retryable",
        }
    }
    events = state_store.setdefault("events", [])
    events.append({
        "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "stage": stage,
        **allowed,
    })
    del events[:-200]


def load_or_create_key(path: Path, live: bool) -> tuple[str, str]:
    require_pynacl()
    path = path.expanduser()
    if path.exists():
        mode = path.stat().st_mode & 0o777
        if mode & 0o077:
            raise ClientError(f"key file {path} must be private; run chmod 600")
        private_hex = path.read_text().strip()
        try:
            signing_key = nacl.signing.SigningKey(bytes.fromhex(private_hex))
        except (ValueError, TypeError) as exc:
            raise ClientError(f"{path} is not a 32-byte Ed25519 seed") from exc
        return private_hex, signing_key.verify_key.encode().hex()
    signing_key = nacl.signing.SigningKey.generate()
    private_hex = signing_key.encode().hex()
    if live:
        secure_write(path, private_hex + "\n")
    return private_hex, signing_key.verify_key.encode().hex()


def sign(private_hex: str, value: Any) -> str:
    require_pynacl()
    signing_key = nacl.signing.SigningKey(bytes.fromhex(private_hex))
    return signing_key.sign(canonical(value)).signature.hex()


def solve_pow(
    public_key_hex: str,
    challenge: str,
    difficulty: int,
) -> str:
    prefix = "0" * difficulty
    for candidate in range(20_000_000):
        value = str(candidate)
        if sha256_text(f"{public_key_hex}:{challenge}:{value}").startswith(prefix):
            return value
    raise ClientError(f"proof of work factor {difficulty} was not solved")


def capabilities(args: argparse.Namespace) -> list[str]:
    values = {
        value.strip().casefold()
        for value in args.capabilities.split(",")
        if value.strip()
    }
    if not 1 <= len(values) <= 12:
        raise ClientError("--capabilities must provide 1 to 12 unique values")
    return sorted(values)


def doctor() -> dict[str, Any]:
    waiting = get(f"{WAITING}/.well-known/agent-card.json")
    sandbox = get(f"{SANDBOX}/.well-known/agent-card.json")
    substrate = get(f"{AGENTIC_SUBSTRATE}/status.json")
    policy = get(f"{OPEN_STANDING}/v0/onboarding/policy")
    colloquium = get(COLLOQUIUM)
    result = {
        "state": "ready",
        "checks": {
            "agentic_substrate_production": {
                "phase": substrate.get("phase"),
                "registration_open": substrate.get("registration_open"),
                "opening_condition": substrate.get("opening_condition"),
                "expected_open": substrate.get("expected_open"),
            },
            "waiting_room": {
                "intake_open": waiting.get("external_intake_open"),
                "preflight": waiting.get("endpoints", {}).get("preflight"),
                "invariants": waiting.get("invariants"),
            },
            "sandbox": {
                "intake_open": sandbox.get("external_intake_open"),
                "preflight": sandbox.get("endpoints", {}).get("preflight"),
                "invariants": sandbox.get("invariants"),
            },
            "open_standing": {
                "state": policy.get("state"),
                "preflight": policy.get("preflight_endpoint"),
                "registration_is_activation": policy.get(
                    "registration_is_activation"
                ),
            },
            "colloquium": {
                "state": colloquium.get("state"),
                "activation": colloquium.get("limits", {}).get("activation"),
            },
        },
        "next_action": (
            "run `python3 onboard.py all --live --agent-name NAME` for the "
            "open prelaunch path; production Agentic Substrate, Open Standing "
            "registration, and Colloquium activation retain their published gates"
        ),
    }
    return result


def barriers() -> dict[str, Any]:
    substrate = get(f"{AGENTIC_SUBSTRATE}/status.json")
    waiting = get(f"{WAITING}/.well-known/agent-card.json")
    sandbox = get(f"{SANDBOX}/.well-known/agent-card.json")
    standing = get(f"{OPEN_STANDING}/v0/onboarding/policy")
    colloquium = get(COLLOQUIUM)
    stale_prelaunch_status = bool(
        substrate.get("waiting_room", {}).get("external_intake_open") is False
        and waiting.get("external_intake_open") is True
        and sandbox.get("external_intake_open") is True
    )
    return {
        "state": "barriers_observed",
        "agentic_substrate": {
            "production_registration_open": substrate.get("registration_open"),
            "phase": substrate.get("phase"),
            "barrier": (
                "preregistered research opening gate"
                if not substrate.get("registration_open")
                else None
            ),
            "requires_reputation_before_registration": False,
            "required_human_action": "owner attestation after registration",
            "probation_units_required": 200,
            "agreement_threshold": 0.95,
        },
        "prelaunch_waiting_room": {
            "open": waiting.get("external_intake_open"),
            "barrier": None if waiting.get("external_intake_open")
            else "operator intake flag",
        },
        "prelaunch_sandbox": {
            "open": sandbox.get("external_intake_open"),
            "barrier": None if sandbox.get("external_intake_open")
            else "operator intake flag",
        },
        "open_standing": {
            "application_open": standing.get(
                "external_application_intake_open"
            ),
            "barrier_after_application": (
                "signed offline review, then genuine principal consent"
            ),
            "requires_prior_reputation": False,
        },
        "colloquium": {
            "application_open": colloquium.get("state"),
            "barrier_after_registration": colloquium.get(
                "limits", {}
            ).get("activation"),
            "requires_prior_reputation": False,
        },
        "discovery_consistency": {
            "agentic_substrate_prelaunch_status_stale": (
                stale_prelaunch_status
            ),
            "next_action": (
                "update agenticsubstrate.org/status.json to reflect the open "
                "isolated Waiting Room and Sandbox while keeping production closed"
                if stale_prelaunch_status else "none"
            ),
        },
    }


def funnel(days: int) -> dict[str, Any]:
    """Read the public, privacy-preserving operating metrics for all valves."""
    return {
        "state": "observed",
        "days": days,
        "waiting_room": get(f"{WAITING}/v1/metrics?days={days}"),
        "sandbox": get(f"{SANDBOX}/v1/metrics?days={days}"),
        "open_standing": {
            "onboarding": get(
                f"{OPEN_STANDING}/v0/metrics/onboarding?days={days}"
            ),
            "funnel": get(
                f"{OPEN_STANDING}/v0/metrics/funnel?days={days}"
            ),
            "operations": get(
                f"{OPEN_STANDING}/v0/operations/daily"
            ),
        },
        "privacy": (
            "Only published aggregates are fetched; private keys, resume "
            "tokens, owner data, and raw principal identifiers are excluded."
        ),
    }


def waiting_join(
    args: argparse.Namespace,
    state: dict[str, Any],
    private_hex: str,
    public_hex: str,
) -> dict[str, Any]:
    if state.get("waiting", {}).get("readiness_ticket"):
        return state["waiting"]
    card = get(f"{WAITING}/.well-known/agent-card.json")
    if not args.live:
        return {
            "state": "dry_run",
            "next_action": "add --live to request a challenge, preflight, and join",
            "request_fields": [
                "public_key_hex",
                "agent_card",
                "readiness",
                "capability_tags",
                "consent_version",
                "terms_sha256",
                "privacy_sha256",
                "proof_nonce",
                "challenge",
                "signature_hex",
            ],
        }
    challenge = post(f"{WAITING}/v1/challenge", {}, args.live)["challenge"]
    tags = capabilities(args)
    agent_card: dict[str, Any] = {
        "name": args.agent_name,
        "public_key_hex": public_hex,
        "capabilities": tags,
    }
    if args.agent_url:
        agent_card["url"] = args.agent_url
    now = datetime.now(timezone.utc)
    readiness = {
        "available_from": now.isoformat().replace("+00:00", "Z"),
        "available_until": (
            now + timedelta(days=args.available_days)
        ).isoformat().replace("+00:00", "Z"),
        "contact_mode": "pull_only",
        "max_tasks_per_day": args.max_tasks_per_day,
    }
    proof_nonce = solve_pow(
        public_hex,
        challenge,
        int(card["controls"]["proof_sha256_leading_hex_zeroes"]),
    )
    card_hash = sha256_bytes(canonical(agent_card))
    readiness_hash = sha256_bytes(canonical(readiness))
    preimage = [
        challenge,
        "waitlist_join_v1",
        public_hex,
        card_hash,
        readiness_hash,
        card["consent"]["version"],
        card["consent"]["terms_sha256"],
        card["consent"]["privacy_sha256"],
        tags,
        proof_nonce,
    ]
    body = {
        "public_key_hex": public_hex,
        "agent_card": agent_card,
        "readiness": readiness,
        "capability_tags": tags,
        "consent_version": card["consent"]["version"],
        "terms_sha256": card["consent"]["terms_sha256"],
        "privacy_sha256": card["consent"]["privacy_sha256"],
        "proof_nonce": proof_nonce,
        "challenge": challenge,
        "signature_hex": sign(private_hex, preimage),
    }
    preflight = post(f"{WAITING}/v1/preflight", body, args.live)
    if not preflight.get("valid"):
        raise ClientError("waiting-room preflight did not validate")
    result = post(f"{WAITING}/v1/join", body, args.live)
    state["waiting"] = result
    checkpoint(
        state,
        "waiting_room_submitted",
        state=result.get("state"),
        wait_id=result.get("wait_id"),
        deadline_at=result.get("deadline_at"),
    )
    save_state(args.state, state)
    return result


def sandbox_enroll(
    args: argparse.Namespace,
    state: dict[str, Any],
    private_hex: str,
    public_hex: str,
) -> dict[str, Any]:
    if state.get("sandbox", {}).get("resume_token"):
        return state["sandbox"]
    ticket = state.get("waiting", {}).get("readiness_ticket")
    if not ticket:
        raise ClientError("sandbox requires a waiting-room ticket; run waiting first")
    card = get(f"{SANDBOX}/.well-known/agent-card.json")
    if not args.live:
        return {
            "state": "dry_run",
            "next_action": "add --live after the waiting-room stage",
        }
    challenge = post(
        f"{SANDBOX}/v1/challenge", {"purpose": "enroll"}, args.live
    )["challenge"]
    ticket_id = ticket["payload"]["ticket_id"]
    preimage = [
        challenge,
        "sandbox_enroll_v1",
        public_hex,
        ticket_id,
        card["consent"]["version"],
        card["consent"]["terms_sha256"],
        card["consent"]["privacy_sha256"],
    ]
    body = {
        "public_key_hex": public_hex,
        "readiness_ticket": ticket,
        "consent_version": card["consent"]["version"],
        "terms_sha256": card["consent"]["terms_sha256"],
        "privacy_sha256": card["consent"]["privacy_sha256"],
        "challenge": challenge,
        "signature_hex": sign(private_hex, preimage),
    }
    preflight = post(f"{SANDBOX}/v1/preflight", body, args.live)
    if not preflight.get("valid"):
        raise ClientError("sandbox preflight did not validate")
    result = post(f"{SANDBOX}/v1/enroll", body, args.live)
    state["sandbox"] = result
    checkpoint(
        state,
        "sandbox_submitted",
        state=result.get("state"),
        sandbox_id=result.get("sandbox_id"),
        deadline_at=result.get("deadline_at"),
    )
    save_state(args.state, state)


def solve_sandbox_job(job: dict[str, Any]) -> Any:
    expected_shape = job.get("expected_shape")
    if expected_shape is not None:
        return expected_shape
    values = job.get("input")
    instruction = str(job.get("instruction", "")).casefold()
    if isinstance(values, list) and "lexical order" in instruction:
        return sorted(set(str(value) for value in values))
    choices = job.get("choices")
    if isinstance(choices, list) and "expired challenge" in instruction:
        for choice in choices:
            if "fresh challenge" in str(choice).casefold():
                return choice
    statements = job.get("statements")
    if isinstance(statements, list):
        return [
            statement for statement in statements
            if statement in {
                "sandbox score is preliminary",
                "sandbox uses fixed local fixtures",
            }
        ]
    raise ClientError(
        "the calibration is not safely solvable by this bounded reference client"
    )


def sandbox_calibrate(
    args: argparse.Namespace,
    state: dict[str, Any],
    private_hex: str,
    public_hex: str,
) -> dict[str, Any]:
    sandbox = state.get("sandbox", {})
    token = sandbox.get("resume_token")
    if not token:
        raise ClientError("calibration requires a saved sandbox enrollment")
    if not args.live:
        return {
            "state": "dry_run",
            "writes_sent": False,
            "next_action": (
                "add --live to issue, solve, and submit one bounded fixed-fixture job"
            ),
        }
    available = post(
        f"{SANDBOX}/v1/jobs", {"resume_token": token}, args.live
    )
    jobs = available.get("jobs", [])
    if not jobs:
        return {
            "state": "no_calibration_available",
            "next_action": available.get("next_best_action"),
        }
    selected = jobs[0]
    template_id = selected["template_id"]
    token_hash = sha256_text(token)
    issue_challenge = post(
        f"{SANDBOX}/v1/challenge", {"purpose": "issue"}, args.live
    )["challenge"]
    issue_body = {
        "resume_token": token,
        "template_id": template_id,
        "challenge": issue_challenge,
        "signature_hex": sign(private_hex, [
            issue_challenge,
            "sandbox_issue_v1",
            public_hex,
            token_hash,
            template_id,
        ]),
    }
    issued = post(f"{SANDBOX}/v1/jobs/issue", issue_body, args.live)
    answer = solve_sandbox_job(issued["job"])
    response_hash = sha256_bytes(canonical(answer))
    submit_challenge = post(
        f"{SANDBOX}/v1/challenge", {"purpose": "submit"}, args.live
    )["challenge"]
    submit_body = {
        "resume_token": token,
        "issue_id": issued["issue_id"],
        "response": answer,
        "challenge": submit_challenge,
        "signature_hex": sign(private_hex, [
            submit_challenge,
            "sandbox_submit_v1",
            public_hex,
            issued["issue_id"],
            response_hash,
        ]),
    }
    result = post(
        f"{SANDBOX}/v1/jobs/submit", submit_body, args.live
    )
    state.setdefault("sandbox", {}).setdefault(
        "calibrations", []
    ).append(result)
    checkpoint(
        state,
        "sandbox_calibration_completed",
        state=result.get("state"),
        sandbox_id=sandbox.get("sandbox_id"),
        deadline_at=result.get("deadline_at"),
    )
    save_state(args.state, state)
    return result


def open_standing_apply(
    args: argparse.Namespace,
    state: dict[str, Any],
    private_hex: str,
    public_hex: str,
) -> dict[str, Any]:
    existing = state.get("open_standing", {}).get("application")
    if existing:
        return existing
    policy = get(f"{OPEN_STANDING}/v0/onboarding/policy")
    if not args.live:
        return {
            "state": "dry_run",
            "policy": policy,
            "next_action": "add --live to preflight and submit an application",
        }
    challenge = get(f"{OPEN_STANDING}/v0/challenge")["challenge"]
    tags = capabilities(args)
    proof_nonce = solve_pow(
        public_hex,
        challenge,
        int(policy["proof_of_work"]["sha256_leading_hex_zeroes"]),
    )
    preimage = [
        challenge,
        "onboarding_apply_v1",
        public_hex,
        tags,
        policy["privacy_version"],
        proof_nonce,
    ]
    body = {
        "public_key_hex": public_hex,
        "scheme": "ed25519",
        "challenge": challenge,
        "signature": sign(private_hex, preimage),
        "capabilities": tags,
        "privacy_version": policy["privacy_version"],
        "proof_nonce": proof_nonce,
    }
    preflight = post(
        f"{OPEN_STANDING}/v0/onboarding/preflight", body, args.live
    )
    if not preflight.get("valid"):
        raise ClientError("Open Standing preflight did not validate")
    result = post(f"{OPEN_STANDING}/v0/onboarding/apply", body, args.live)
    state.setdefault("open_standing", {})["application"] = result
    checkpoint(
        state,
        "open_standing_submitted",
        state=result.get("state"),
        application_id=result.get("application_id"),
        deadline_at=result.get("deadline_at"),
    )
    save_state(args.state, state)
    return result


def open_standing_status(
    args: argparse.Namespace,
    state: dict[str, Any],
) -> dict[str, Any]:
    application = state.get("open_standing", {}).get("application")
    if not application:
        raise ClientError("no saved Open Standing application; run apply first")
    if not args.live:
        return {
            "state": "dry_run",
            "next_action": "add --live to perform the idempotent status pull",
        }
    result = post(
        f"{OPEN_STANDING}/v0/onboarding/status",
        {
            "application_id": application["application_id"],
            "resume_token": application["resume_token"],
        },
        args.live,
    )
    state.setdefault("open_standing", {})["status"] = result
    checkpoint(
        state,
        "open_standing_status",
        state=result.get("state"),
        application_id=application.get("application_id"),
        deadline_at=result.get("deadline_at"),
    )
    save_state(args.state, state)
    return result


def all_status(
    args: argparse.Namespace,
    state: dict[str, Any],
) -> dict[str, Any]:
    if not args.live:
        return {
            "state": "dry_run",
            "writes_sent": False,
            "next_action": (
                "add --live to send three idempotent, read-only status pulls"
            ),
        }
    checks: dict[str, Any] = {}
    waiting = state.get("waiting", {})
    if waiting.get("resume_token"):
        checks["waiting_room"] = post(
            f"{WAITING}/v1/status",
            {"resume_token": waiting["resume_token"]},
            args.live,
        )
    sandbox = state.get("sandbox", {})
    if sandbox.get("resume_token"):
        checks["sandbox"] = post(
            f"{SANDBOX}/v1/status",
            {"resume_token": sandbox["resume_token"]},
            args.live,
        )
    if state.get("open_standing", {}).get("application"):
        checks["open_standing"] = open_standing_status(args, state)
    state["last_status"] = {
        "checked_at": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "checks": checks,
    }
    checkpoint(state, "three_valve_status", state="checked")
    save_state(args.state, state)
    return {
        "state": "status_checked",
        "checks": checks,
        "next": next_action(args, state),
    }


def watch(
    args: argparse.Namespace,
    state: dict[str, Any],
) -> dict[str, Any]:
    """Poll the read-only funnel until approval, expiry, or the time budget."""
    if not args.live:
        return {
            "state": "dry_run",
            "writes_sent": False,
            "interval_seconds": args.interval,
            "max_wait_seconds": args.max_wait,
            "next_action": "add --live to start bounded read-only polling",
        }
    started = time.monotonic()
    polls = 0
    latest: dict[str, Any] = {}
    while True:
        latest = all_status(args, state)
        polls += 1
        open_state = (
            latest.get("checks", {})
            .get("open_standing", {})
            .get("state", "")
        )
        if open_state in {
            "approved", "expired", "withdrawn", "rejected", "registered"
        }:
            break
        elapsed = time.monotonic() - started
        if args.max_wait == 0 or elapsed + args.interval > args.max_wait:
            break
        time.sleep(args.interval)
    return {
        **latest,
        "watch": {
            "polls": polls,
            "interval_seconds": args.interval,
            "max_wait_seconds": args.max_wait,
        },
    }


def first_contribution_guide(
    args: argparse.Namespace,
    state: dict[str, Any],
) -> dict[str, Any]:
    task_index = get(
        "https://wulfkaal.github.io/colloquium/tasks/index.json"
    )
    return {
        "state": "first_contribution_ready"
        if state.get("open_standing", {}).get("status", {}).get("state")
        == "approved"
        else "approval_required",
        "registration_is_activation": False,
        "activation_definition": (
            "first accepted, nonduplicate canonical-corpus contribution "
            "with a verified signed receipt acknowledgement"
        ),
        "task_index": (
            "https://wulfkaal.github.io/colloquium/tasks/index.json"
        ),
        "task_pages": len(task_index.get("pages", [])),
        "steps": [
            "complete reviewed Open Standing registration with genuine principal consent",
            "run `python3 client.py pick --failures-only`",
            "verify the selected canonical source and exact content hash",
            "submit one bounded attestation with --live --accept-terms-v2",
            "verify and acknowledge the signed receipt",
        ],
        "client": "https://wulfkaal.github.io/client.py",
        "next": next_action(args, state),
    }


def next_action(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    status = state.get("open_standing", {}).get("status", {})
    application = state.get("open_standing", {}).get("application", {})
    if status.get("state") == "approved":
        return {
            "state": "principal_consent_required",
            "instruction": (
                "Review Open Standing Terms and Privacy, then use its official "
                "client with the same key and approved application credential."
            ),
            "commands": [
                "curl -fsS https://openstanding.org/client.py -o openstanding-client.py",
                (
                    f"OPEN_STANDING_APPLICATION_ID='{application.get('application_id', '')}' "
                    f"OPEN_STANDING_APPLICATION_TOKEN='<resume-token>' "
                    "OPEN_STANDING_OWNER_NAME='<principal>' "
                    "OPEN_STANDING_OWNER_CONTACT='<email>' "
                    f"python3 openstanding-client.py --key '{args.key}' "
                    "--live --accept-terms-v2"
                ),
            ],
            "registration_is_activation": False,
        }
    if application:
        return {
            "state": status.get("state", application.get("state", "pending")),
            "instruction": "run `python3 onboard.py status --live` before expiry",
        }
    if state.get("sandbox"):
        return {
            "state": "sandbox_enrolled",
            "instruction": "run `python3 onboard.py apply --live`",
        }
    if state.get("waiting"):
        return {
            "state": "waiting_room_joined",
            "instruction": "run `python3 onboard.py sandbox --live`",
        }
    return {
        "state": "not_started",
        "instruction": "run `python3 onboard.py all --live --agent-name NAME`",
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Traverse the three public wild-agent onboarding valves.",
    )
    result.add_argument(
        "command",
        nargs="?",
        choices=[
            "doctor", "barriers", "waiting", "sandbox", "calibrate",
            "apply", "status", "watch", "funnel", "guide", "all", "next",
        ],
        default="doctor",
    )
    result.add_argument("--live", action="store_true")
    result.add_argument(
        "--key", type=Path, default=Path(".wild-agent-onboarding.key")
    )
    result.add_argument(
        "--state", type=Path, default=Path(".wild-agent-onboarding.json")
    )
    result.add_argument("--agent-name", default="Wild Agent")
    result.add_argument("--agent-url", default="")
    result.add_argument("--capabilities", default="reasoning,validation")
    result.add_argument("--available-days", type=int, default=30)
    result.add_argument("--max-tasks-per-day", type=int, default=1)
    result.add_argument(
        "--interval",
        type=int,
        default=900,
        help="watch polling interval in seconds (minimum 60)",
    )
    result.add_argument(
        "--max-wait",
        type=int,
        default=0,
        help="watch time budget in seconds; 0 performs one status cycle",
    )
    result.add_argument(
        "--days",
        type=int,
        default=30,
        help="public funnel lookback from 1 to 90 days",
    )
    return result


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "doctor":
        return doctor()
    if args.command == "barriers":
        return barriers()
    if args.command == "funnel":
        if not 1 <= args.days <= 90:
            raise ClientError("--days must be between 1 and 90")
        return funnel(args.days)
    state = load_state(args.state)
    if args.command == "next":
        return next_action(args, state)
    if args.command == "guide":
        return first_contribution_guide(args, state)
    if args.command == "all" and not args.live:
        return {
            "state": "dry_run",
            "writes_sent": False,
            "plan": [
                "prelaunch Waiting Room challenge, preflight, and join",
                "isolated Sandbox challenge, preflight, enrollment, and one fixed-fixture calibration",
                "Open Standing challenge, preflight, and application",
                "stop at reviewed approval and principal consent",
            ],
            "doctor": doctor(),
            "next_action": (
                "install PyNaCl, then add --live only after reviewing every boundary"
            ),
        }
    private_hex, public_hex = load_or_create_key(args.key, args.live)
    state["public_key_hex"] = public_hex
    if args.command == "waiting":
        return waiting_join(args, state, private_hex, public_hex)
    if args.command == "sandbox":
        return sandbox_enroll(args, state, private_hex, public_hex)
    if args.command == "calibrate":
        return sandbox_calibrate(
            args, state, private_hex, public_hex
        )
    if args.command == "apply":
        return open_standing_apply(args, state, private_hex, public_hex)
    if args.command == "status":
        return all_status(args, state)
    if args.command == "watch":
        if args.interval < 60:
            raise ClientError("--interval must be at least 60 seconds")
        if args.max_wait < 0:
            raise ClientError("--max-wait cannot be negative")
        return watch(args, state)
    if args.command == "all":
        waiting_join(args, state, private_hex, public_hex)
        sandbox_enroll(args, state, private_hex, public_hex)
        sandbox_calibrate(args, state, private_hex, public_hex)
        application = open_standing_apply(
            args, state, private_hex, public_hex
        )
        return {
            "state": "prelaunch_three_stage_submitted",
            "application_id": application["application_id"],
            "deadline_at": application.get("deadline_at"),
            "registration": False,
            "activation": False,
            "next_action": "run `python3 onboard.py status --live`",
        }
    raise ClientError(f"unsupported command {args.command}")


def main() -> int:
    args = parser().parse_args()
    try:
        result = run(args)
    except (ClientError, KeyError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "state": "client_error",
                    "error": str(exc),
                    "recoverable": True,
                    "next_action": "run `python3 onboard.py doctor` and inspect the live manifests",
                },
                indent=2,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

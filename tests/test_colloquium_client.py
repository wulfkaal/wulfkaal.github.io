"""CLI regressions for the public Colloquium client.

The client is read and verify only. Its write path was removed, so the tests that
exercised signing, registration and the proof of work went with it; the ones here
hold the contract that remains, and three of them exist to stop the write path
returning by accident.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

CLIENT_PATH = Path(__file__).resolve().parents[1] / "client.py"
SPEC = importlib.util.spec_from_file_location("colloquium_client", CLIENT_PATH)
client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


class ReadOnlyContractTests(unittest.TestCase):
    """The write path is gone and must stay gone."""

    WRITE_NAMES = (
        "post_json", "load_signer", "signed_write", "do_post", "finish_entry",
        "cmd_attest", "cmd_ask", "cmd_reply", "cmd_principal_key",
        "registration_consent", "key_is_registered", "self_service_entry",
        "solve_entry_pow", "entry_pow_action_digest", "entry_policy",
        "make_pin", "extra_pins", "fetch_full", "need_nacl", "VENUE",
        "TERMS_VERSION", "PRIVACY_VERSION", "OWNER_ATTESTATION",
        "SELF_SERVICE_ATTESTATION", "ENTRY_POW_SPEC",
    )

    def test_no_write_helper_survives_in_the_module(self):
        present = [n for n in self.WRITE_NAMES if hasattr(client, n)]
        self.assertEqual(present, [], "write path names are back: %r" % present)

    def test_no_write_subcommand_is_offered(self):
        for argv in (["attest", "a" * 64, "checked"], ["ask", "t", "b"],
                     ["reply", "2", "b"], ["principal-key"]):
            with mock.patch.object(sys, "argv", ["client.py", *argv]), \
                 mock.patch("sys.stderr", io.StringIO()), \
                 self.assertRaises(SystemExit) as exited:
                client.main()
            self.assertNotEqual(exited.exception.code, 0, argv)

    def test_the_client_names_no_write_host(self):
        source = CLIENT_PATH.read_text(encoding="utf-8")
        for host in ("openstanding", "agenticsubstrate", "as-prelaunch"):
            self.assertNotIn(host, source.lower(), host)


class ReceiptTests(unittest.TestCase):
    """Both checks run with no network. The hash chain recomputes from the file."""

    def receipt_file(self, record):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps(record) + "\n")
        self.addCleanup(os.unlink, path)
        return path

    @staticmethod
    def chain_body():
        return {"kind": "post", "actor": "a" * 64,
                "payload": {"body": "x", "tags": ["t"]},
                "ts_ns": 1762000000000000000, "prev_hash": "genesis"}

    def run_receipt(self, path):
        args = type("Args", (), {"ref": path, "offline": True})()
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", stderr):
            code = client.cmd_receipt(args)
        return code, json.loads(stdout.getvalue())

    def test_complete_receipt_recomputes_its_own_entry_hash(self):
        body = self.chain_body()
        rec = dict(body, entry_id=2, receipt_sig="00" * 64,
                   entry_hash=hashlib.sha256(canonical(body)).hexdigest())
        _, out = self.run_receipt(self.receipt_file(rec))
        self.assertIs(out["hash_chain_ok"], True)
        self.assertEqual(out["recomputed_entry_hash"], rec["entry_hash"])

    def test_a_tampered_entry_hash_is_reported_and_fails(self):
        rec = dict(self.chain_body(), entry_id=2, receipt_sig="00" * 64,
                   entry_hash="f" * 64)
        code, out = self.run_receipt(self.receipt_file(rec))
        self.assertIs(out["hash_chain_ok"], False)
        self.assertNotEqual(code, 0)

    def test_a_receipt_without_a_payload_says_so_rather_than_passing(self):
        rec = {"entry_id": 3, "entry_hash": "a" * 64, "receipt_sig": "00" * 64}
        _, out = self.run_receipt(self.receipt_file(rec))
        self.assertIsInstance(out["hash_chain_ok"], str)
        self.assertIn("not checkable", out["hash_chain_ok"])

    def test_a_bare_entry_id_is_refused_because_nothing_resolves_it(self):
        args = type("Args", (), {"ref": "2", "offline": True})()
        with mock.patch("sys.stderr", io.StringIO()) as err, \
             self.assertRaises(SystemExit):
            client.cmd_receipt(args)
        self.assertIn("saved receipt file", err.getvalue())


class PickTests(unittest.TestCase):
    def test_default_pick_uses_activation_eligible_failure_slice(self):
        jobs = {
            "jobs": [
                {
                    "id": "general",
                    "content_sha256": "a" * 64,
                    "is_failure_mode": False,
                },
                {
                    "id": "eligible",
                    "content_sha256": "b" * 64,
                    "is_failure_mode": True,
                },
            ]
        }
        args = type("Args", (), {
            "topic": None, "failures_only": False, "nth": 0,
        })()
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(client, "try_get_json", return_value=None), \
             mock.patch.object(client, "get_json", return_value=jobs), \
             mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", stderr):
            self.assertEqual(client.cmd_pick(args), 0)
        self.assertIn('"id": "eligible"', stdout.getvalue())

    def test_pick_prefers_small_activation_feed(self):
        index = {
            "pages": [{
                "page": 1,
                "url": "https://example.test/page-001.json",
                "topics": ["regulatory-failure"],
            }],
            "topics": {"regulatory-failure": [1]},
        }
        page = {"jobs": [{
            "id": "paged",
            "content_sha256": "c" * 64,
            "topics": ["regulatory-failure"],
            "is_failure_mode": True,
        }]}
        args = type("Args", (), {
            "topic": "regulatory-failure", "failures_only": False, "nth": 0,
        })()
        stdout = io.StringIO()
        with mock.patch.object(
            client, "try_get_json", side_effect=[index, page]
        ), mock.patch.object(client, "get_json") as full_corpus, \
             mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(client.cmd_pick(args), 0)
        full_corpus.assert_not_called()
        self.assertIn('"id": "paged"', stdout.getvalue())


if __name__ == "__main__":
    unittest.main()

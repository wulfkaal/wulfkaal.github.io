"""CLI regressions for the public Colloquium client."""
from __future__ import annotations

import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

CLIENT_PATH = Path(__file__).resolve().parents[1] / "client.py"
SPEC = importlib.util.spec_from_file_location("colloquium_client", CLIENT_PATH)
client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client)


class ColloquiumCliTests(unittest.TestCase):
    def parse_write(self, argv):
        captured = {}

        def fake_attest(args):
            captured.update(vars(args))
            return 0

        with mock.patch.object(client, "cmd_attest", fake_attest), \
             mock.patch.object(sys, "argv", ["client.py", *argv]), \
             self.assertRaises(SystemExit) as exited:
            client.main()
        self.assertEqual(exited.exception.code, 0)
        return captured

    def test_live_flag_is_accepted_after_subcommand(self):
        parsed = self.parse_write([
            "attest", "a" * 64, "checked", "--live", "--accept-terms-v2",
        ])
        self.assertTrue(parsed["live"])
        self.assertTrue(parsed["accept_terms_v2"])

    def test_live_flag_is_accepted_before_subcommand(self):
        parsed = self.parse_write([
            "--live", "--accept-terms-v2", "attest", "a" * 64, "checked",
        ])
        self.assertTrue(parsed["live"])
        self.assertTrue(parsed["accept_terms_v2"])

    def test_receipt_file_is_opt_in(self):
        parsed = self.parse_write(["attest", "a" * 64, "checked"])
        self.assertIsNone(parsed["receipts"])

    def test_registration_accepts_exactly_one_approved_application(self):
        args = type("Args", (), {"accept_terms_v2": True})()
        environment = {
            "OPEN_STANDING_OWNER_NAME": "Owner",
            "OPEN_STANDING_OWNER_CONTACT": "owner@example.org",
            "OPEN_STANDING_APPLICATION_ID": "a" * 64,
            "OPEN_STANDING_APPLICATION_TOKEN": "private-token",
        }
        with mock.patch.dict("os.environ", environment, clear=True):
            consent = client.registration_consent(args)
        self.assertIsNone(consent["invitation_code"])
        self.assertEqual(consent["application_id"], "a" * 64)
        self.assertEqual(consent["application_token"], "private-token")
        self.assertEqual(
            consent["admission_hash"],
            client.sha256_hex(b"private-token"),
        )
        self.assertEqual(client.TERMS_VERSION, "2.2")
        self.assertEqual(client.PRIVACY_VERSION, "1.2")

    def test_registration_rejects_ambiguous_admission_credentials(self):
        args = type("Args", (), {"accept_terms_v2": True})()
        environment = {
            "OPEN_STANDING_OWNER_NAME": "Owner",
            "OPEN_STANDING_OWNER_CONTACT": "owner@example.org",
            "OPEN_STANDING_INVITATION": "invite",
            "OPEN_STANDING_APPLICATION_ID": "a" * 64,
            "OPEN_STANDING_APPLICATION_TOKEN": "private-token",
        }
        with mock.patch.dict("os.environ", environment, clear=True), \
             self.assertRaises(SystemExit):
            client.registration_consent(args)

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

    def test_live_post_verifies_and_acknowledges_exact_receipt(self):
        signer = mock.Mock()
        signer.verify_key = bytes.fromhex("01" * 32)
        args = type("Args", (), {
            "keep_key": None,
            "live": True,
            "accept_terms_v2": True,
            "receipts": None,
        })()
        contribution_receipt = {
            "entry_id": 41,
            "entry_hash": "ab" * 32,
            "receipt_sig": "cd" * 64,
        }
        activation_receipt = {
            "entry_id": 42,
            "entry_hash": "ef" * 32,
            "receipt_sig": "12" * 64,
        }
        signed_calls = []

        def fake_signed_write(_a, _sk, label, path, preimage_fn, body_fn):
            signed_calls.append((label, path, preimage_fn("challenge")))
            if path == "/v0/post":
                return False, {
                    "post": {"id": 7, "phase": "open"},
                    "receipt": contribution_receipt,
                }
            if path == "/v0/receipt/ack":
                body = body_fn("challenge", "signature", "01" * 32)
                self.assertEqual(body["entry_id"], contribution_receipt["entry_id"])
                self.assertEqual(body["entry_hash"], contribution_receipt["entry_hash"])
                return False, {
                    "activation": {"state": "activated", "surface": "colloquium"},
                    "receipt": activation_receipt,
                }
            self.fail("unexpected signed path %s" % path)

        stdout = io.StringIO()
        with mock.patch.object(client, "need_nacl"), \
             mock.patch.object(client, "load_signer", return_value=(signer, "test")), \
             mock.patch.object(client, "key_is_registered", return_value=True), \
             mock.patch.object(client, "signed_write", side_effect=fake_signed_write), \
             mock.patch.object(client, "verify_sig_offline", return_value=True) as verify, \
             mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(
                client.do_post(args, None, "checked", ["proving"], "a" * 64),
                0,
            )

        self.assertEqual(
            signed_calls,
            [
                (
                    "post",
                    "/v0/post",
                    [
                        "challenge", "post", "", "checked", ["proving"],
                        "a" * 64, 0, [],
                    ],
                ),
                (
                    "receipt acknowledgement",
                    "/v0/receipt/ack",
                    ["challenge", "receipt_ack", 41, "ab" * 32],
                ),
            ],
        )
        self.assertEqual(verify.call_count, 2)
        output = json.loads(stdout.getvalue())
        self.assertEqual(output["activation"]["state"], "activated")
        self.assertEqual(output["entry_id"], 42)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "notify_claim_indexes.py"
SPEC = importlib.util.spec_from_file_location("claim_notifier", SCRIPT)
NOTIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NOTIFIER)


class ClaimNotifierTests(unittest.TestCase):
    def run_main(self, argv, key="a" * 40):
        with patch.object(sys, "argv", [str(SCRIPT), *argv]), patch.dict(
            os.environ, {"INDEXNOW_KEY": key}, clear=True
        ):
            return NOTIFIER.main()

    def test_live_notification_requires_immutable_receipt(self):
        with patch.object(NOTIFIER, "fetch") as fetch_mock:
            self.assertEqual(self.run_main([]), 1)
        fetch_mock.assert_not_called()

    def test_missing_key_fails_before_network(self):
        with patch.object(NOTIFIER, "DEFAULT_KEY_FILE", Path("/definitely/missing")), \
                patch.object(NOTIFIER, "fetch") as fetch_mock:
            self.assertEqual(self.run_main(["--dry-run"], key=""), 1)
        fetch_mock.assert_not_called()

    def test_existing_receipt_fails_before_network(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt = Path(temp) / "intent.json"
            receipt.write_text("reserved\n", encoding="utf-8")
            with patch.object(NOTIFIER, "fetch") as fetch_mock:
                self.assertEqual(
                    self.run_main(["--receipt", str(receipt)]), 1
                )
            fetch_mock.assert_not_called()

    def test_dry_run_verifies_urls_and_writes_no_result(self):
        def fake_fetch(url, **_kwargs):
            if url.endswith("indexnow-key.txt"):
                return 200, ("a" * 40 + "\n").encode()
            return 200, url.encode()

        with tempfile.TemporaryDirectory() as temp, patch.object(
            NOTIFIER, "fetch", side_effect=fake_fetch
        ) as fetch_mock:
            receipt = Path(temp) / "dry-run.json"
            self.assertEqual(
                self.run_main(["--dry-run", "--receipt", str(receipt)]), 0
            )
            value = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(value["status"], "dry-run-verified")
            self.assertFalse(value["notificationSent"])
            self.assertEqual(len(value["verifiedUrls"]), len(NOTIFIER.URLS))
            self.assertFalse(NOTIFIER.result_path(receipt).exists())
            self.assertFalse(any(
                call.kwargs.get("method") == "POST" for call in fetch_mock.call_args_list
            ))

    def test_live_intent_exists_before_post_and_result_binds_it(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt = Path(temp) / "intent.json"

            def fake_fetch(url, method="GET", **_kwargs):
                if url.endswith("indexnow-key.txt"):
                    return 200, ("a" * 40 + "\n").encode()
                if method == "POST":
                    self.assertTrue(receipt.exists())
                    self.assertEqual(
                        json.loads(receipt.read_text(encoding="utf-8"))["status"],
                        "intent-recorded",
                    )
                    return 202, b"accepted"
                return 200, url.encode()

            with patch.object(NOTIFIER, "fetch", side_effect=fake_fetch):
                self.assertEqual(self.run_main(["--receipt", str(receipt)]), 0)

            result = json.loads(
                NOTIFIER.result_path(receipt).read_text(encoding="utf-8")
            )
            self.assertEqual(result["status"], "notified")
            self.assertTrue(result["notificationSent"])
            self.assertEqual(len(result["intentSha256"]), 64)

    def test_ambiguous_post_is_terminal_unknown_outcome(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt = Path(temp) / "intent.json"

            def fake_fetch(url, method="GET", **_kwargs):
                if url.endswith("indexnow-key.txt"):
                    return 200, ("a" * 40 + "\n").encode()
                if method == "POST":
                    raise RuntimeError("connection lost after send")
                return 200, url.encode()

            with patch.object(NOTIFIER, "fetch", side_effect=fake_fetch):
                self.assertEqual(self.run_main(["--receipt", str(receipt)]), 1)

            result = json.loads(
                NOTIFIER.result_path(receipt).read_text(encoding="utf-8")
            )
            self.assertEqual(result["status"], "unknown-outcome")
            self.assertFalse(result["notificationSent"])


if __name__ == "__main__":
    unittest.main()

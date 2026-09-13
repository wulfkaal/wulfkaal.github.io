import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "notify_essay_indexes.py"
SPEC = importlib.util.spec_from_file_location("essay_notifier", SCRIPT)
NOTIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NOTIFIER)


class EssayNotifierTests(unittest.TestCase):
    def run_main(self, argv, key="a" * 40):
        with patch.object(sys, "argv", [str(SCRIPT), *argv]), patch.dict(
            os.environ, {"INDEXNOW_KEY": key}, clear=True
        ):
            return NOTIFIER.main()

    def exact_get(self, url, method="GET", **_kwargs):
        if url.endswith("indexnow-key.txt"):
            return 200, ("a" * 40 + "\n").encode()
        self.assertEqual(method, "GET")
        return 200, NOTIFIER.committed_body(url)

    def test_missing_receipt_fails_before_network(self):
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
                self.assertEqual(self.run_main(["--receipt", str(receipt)]), 1)
            fetch_mock.assert_not_called()

    def test_404_fails_closed_without_post(self):
        urls = NOTIFIER.derive_urls()

        def fake_fetch(url, method="GET", **kwargs):
            if url == urls[0]:
                return 404, b"missing"
            return self.exact_get(url, method=method, **kwargs)

        with patch.object(NOTIFIER, "fetch", side_effect=fake_fetch) as fetch_mock:
            self.assertEqual(self.run_main(["--dry-run"]), 1)
        self.assertFalse(any(call.kwargs.get("method") == "POST" for call in fetch_mock.call_args_list))

    def test_byte_mismatch_fails_closed_without_post(self):
        urls = NOTIFIER.derive_urls()

        def fake_fetch(url, method="GET", **kwargs):
            if url == urls[0]:
                return 200, b"not the committed bytes"
            return self.exact_get(url, method=method, **kwargs)

        with patch.object(NOTIFIER, "fetch", side_effect=fake_fetch) as fetch_mock:
            self.assertEqual(self.run_main(["--dry-run"]), 1)
        self.assertFalse(any(call.kwargs.get("method") == "POST" for call in fetch_mock.call_args_list))

    def test_live_key_mismatch_fails_closed_without_post(self):
        def fake_fetch(url, method="GET", **kwargs):
            if url.endswith("indexnow-key.txt"):
                return 200, b"different-key\n"
            return self.exact_get(url, method=method, **kwargs)

        with patch.object(NOTIFIER, "fetch", side_effect=fake_fetch) as fetch_mock:
            self.assertEqual(self.run_main(["--dry-run"]), 1)
        self.assertFalse(any(call.kwargs.get("method") == "POST" for call in fetch_mock.call_args_list))

    def test_verified_dry_run_sends_no_post(self):
        with patch.object(NOTIFIER, "fetch", side_effect=self.exact_get) as fetch_mock:
            self.assertEqual(self.run_main(["--dry-run"]), 0)
        self.assertFalse(any(call.kwargs.get("method") == "POST" for call in fetch_mock.call_args_list))

    def test_success_writes_intent_and_result_with_exact_urls(self):
        expected = NOTIFIER.derive_urls()
        with tempfile.TemporaryDirectory() as temp:
            receipt = Path(temp) / "intent.json"

            def fake_fetch(url, method="GET", payload=None, **kwargs):
                if method == "POST":
                    self.assertTrue(receipt.exists())
                    sent = json.loads(payload)
                    self.assertEqual(sent["urlList"], expected)
                    return 202, b"accepted"
                return self.exact_get(url, method=method, **kwargs)

            with patch.object(NOTIFIER, "fetch", side_effect=fake_fetch):
                self.assertEqual(self.run_main(["--receipt", str(receipt)]), 0)

            intent = json.loads(receipt.read_text(encoding="utf-8"))
            result = json.loads(NOTIFIER.result_path(receipt).read_text(encoding="utf-8"))
            self.assertEqual(intent["status"], "intent-recorded")
            self.assertEqual(intent["urlList"], expected)
            self.assertEqual(result["status"], "notified")
            self.assertEqual(result["urlList"], expected)


if __name__ == "__main__":
    unittest.main()

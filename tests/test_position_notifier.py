import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "notify_position_indexes.py"
SPEC = importlib.util.spec_from_file_location("position_notifier", SCRIPT)
NOTIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NOTIFIER)


class PositionNotifierTests(unittest.TestCase):
    def test_missing_key_records_no_notification_after_live_gates(self):
        publication = {
            "status": "live-verified-publication-complete",
            "batchId": "test-batch",
            "commit": "a" * 40,
            "after": 8063,
            "publishedIds": ["kaal:position:2026-08-08-123"],
            "liveVerification": {
                "allHttp200": True,
                "allByteIdenticalToCanonicalCommit": True,
                "sitemapsVerified": True,
            },
            "protectedInvariant": {
                "count": 5073,
                "length": 5073,
                "sha256": NOTIFIER.PROTECTED_SHA256,
                "localLiveByteIdentical": True,
            },
        }

        def fake_fetch(url, **_kwargs):
            if url.endswith("positions/index.json"):
                return 200, json.dumps({"numberOfItems": 8063}).encode()
            return 200, b"ok"

        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "publication.json"
            output = Path(temp) / "notification.json"
            source.write_text(json.dumps(publication), encoding="utf-8")
            argv = [
                str(SCRIPT), "--publication-receipt", str(source),
                "--output-receipt", str(output),
            ]
            with patch.object(NOTIFIER, "fetch", side_effect=fake_fetch), \
                    patch.dict(os.environ, {"INDEXNOW_KEY_FILE": str(Path(temp) / "missing.txt")}, clear=True), \
                    patch.object(sys, "argv", argv):
                NOTIFIER.main()
            receipt = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(receipt["notificationSent"])
            self.assertEqual(receipt["status"], "not-notified-missing-indexnow-key")
            self.assertIn("IndexNow key is absent", receipt["blocker"])

    def test_public_key_file_is_used_and_verified_before_notification(self):
        publication = {
            "status": "live-verified-publication-complete",
            "batchId": "test-batch",
            "commit": "a" * 40,
            "after": 8063,
            "publishedIds": ["kaal:position:2026-08-08-123"],
            "liveVerification": {
                "allHttp200": True,
                "allByteIdenticalToCanonicalCommit": True,
                "sitemapsVerified": True,
            },
            "protectedInvariant": {
                "count": 5073,
                "length": 5073,
                "sha256": NOTIFIER.PROTECTED_SHA256,
                "localLiveByteIdentical": True,
            },
        }
        key = "a" * 40
        calls = []

        def fake_fetch(url, method="GET", payload=None, **_kwargs):
            calls.append((url, method, payload))
            if url.endswith("positions/index.json"):
                return 200, json.dumps({"numberOfItems": 8063}).encode()
            if url.endswith("indexnow-key.txt"):
                return 200, (key + "\n").encode()
            if method == "POST":
                body = json.loads(payload)
                self.assertEqual(body["key"], key)
                self.assertEqual(body["keyLocation"], f"{NOTIFIER.BASE}/indexnow-key.txt")
                return 202, b"accepted"
            return 200, b"ok"

        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "publication.json"
            output = Path(temp) / "notification.json"
            key_file = Path(temp) / "indexnow-key.txt"
            source.write_text(json.dumps(publication), encoding="utf-8")
            key_file.write_text(key + "\n", encoding="utf-8")
            argv = [str(SCRIPT), "--publication-receipt", str(source), "--output-receipt", str(output)]
            with patch.object(NOTIFIER, "fetch", side_effect=fake_fetch), \
                    patch.dict(os.environ, {"INDEXNOW_KEY_FILE": str(key_file)}, clear=True), \
                    patch.object(sys, "argv", argv):
                NOTIFIER.main()
            receipt = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(receipt["notificationSent"])
            self.assertEqual(receipt["httpStatus"], 202)
            self.assertTrue(any(method == "POST" for _, method, _ in calls))

    def test_failed_protected_gate_never_calls_network(self):
        publication = {
            "status": "live-verified-publication-complete",
            "commit": "a" * 40,
            "after": 1,
            "publishedIds": ["kaal:position:2026-08-08-123"],
            "liveVerification": {
                "allHttp200": True,
                "allByteIdenticalToCanonicalCommit": True,
                "sitemapsVerified": True,
            },
            "protectedInvariant": {
                "count": 5072,
                "length": 5073,
                "sha256": NOTIFIER.PROTECTED_SHA256,
                "localLiveByteIdentical": True,
            },
        }
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "publication.json"
            output = Path(temp) / "notification.json"
            source.write_text(json.dumps(publication), encoding="utf-8")
            argv = [str(SCRIPT), "--publication-receipt", str(source), "--output-receipt", str(output)]
            with patch.object(NOTIFIER, "fetch") as fetch_mock, patch.object(sys, "argv", argv):
                with self.assertRaises(SystemExit):
                    NOTIFIER.main()
            fetch_mock.assert_not_called()
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

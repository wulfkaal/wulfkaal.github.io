"""Regression tests for the three-valve onboarding orchestrator."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

CLIENT_PATH = Path(__file__).resolve().parents[1] / "onboard.py"
SPEC = importlib.util.spec_from_file_location("onboard_client", CLIENT_PATH)
client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client)


class OnboardTests(unittest.TestCase):
    def args(self, state: Path):
        return SimpleNamespace(
            live=True, state=state, interval=60, max_wait=0,
            key=Path("unused.key"),
        )

    def test_checkpoint_is_bounded_and_excludes_secrets(self):
        state = {"events": []}
        for number in range(205):
            client.checkpoint(
                state, "status", state=str(number),
                resume_token="must-not-be-recorded",
            )
        self.assertEqual(len(state["events"]), 200)
        self.assertNotIn("resume_token", state["events"][-1])

    def test_all_status_pulls_every_saved_valve(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            state = {
                "schema_version": "wild-agent-onboarding-state-v2",
                "events": [],
                "waiting": {"resume_token": "waiting-token"},
                "sandbox": {"resume_token": "sandbox-token"},
                "open_standing": {
                    "application": {
                        "application_id": "a" * 64,
                        "resume_token": "open-token",
                    }
                },
            }
            replies = [
                {"state": "verified_waiting"},
                {"state": "prelaunch_sandbox_active"},
                {"state": "pending", "expires_ns": 1},
            ]
            with mock.patch.object(client, "post", side_effect=replies):
                result = client.all_status(self.args(path), state)
            self.assertEqual(result["state"], "status_checked")
            self.assertEqual(
                set(result["checks"]),
                {"waiting_room", "sandbox", "open_standing"},
            )
            self.assertTrue(path.exists())

    def test_watch_zero_budget_performs_one_cycle(self):
        state = {}
        args = self.args(Path("unused.json"))
        pending = {
            "state": "status_checked",
            "checks": {"open_standing": {"state": "pending"}},
        }
        with mock.patch.object(client, "all_status", return_value=pending) as pull:
            result = client.watch(args, state)
        self.assertEqual(result["watch"]["polls"], 1)
        pull.assert_called_once()

    def test_funnel_reads_only_public_aggregate_endpoints(self):
        with mock.patch.object(client, "get", return_value={"ok": True}) as fetch:
            result = client.funnel(14)
        self.assertEqual(result["state"], "observed")
        self.assertEqual(fetch.call_count, 5)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "tools" / "check_kaalvis_gate_binding.py"
REQUIRED_BRANCH = "kaalvis/compounding-2026-09-12"

SPEC = importlib.util.spec_from_file_location("kaalvis_gate_binding", CHECKER)
GATE_BINDING = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE_BINDING)


def git_output(*args):
    return subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


class KaalvisGateBindingTests(unittest.TestCase):
    def test_checker_emits_exact_head_and_required_branch(self):
        head = git_output("rev-parse", "HEAD")
        result = subprocess.run(
            (sys.executable, str(CHECKER), "--expect", head),
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            [f"KAALVIS_GATE_HEAD={head}", f"KAALVIS_GATE_BRANCH={REQUIRED_BRANCH}"],
            result.stdout.splitlines(),
        )

    def test_checker_rejects_a_different_reviewed_sha(self):
        result = subprocess.run(
            (sys.executable, str(CHECKER), "--expect", "0" * 40),
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("expected commit", result.stderr)

    def test_validation_rejects_the_superseded_branch(self):
        errors = GATE_BINDING.validate_binding(
            "a" * 40,
            "kaalvis/compounding-2026-09-14",
            "a" * 40,
        )
        self.assertEqual(
            [
                "required branch kaalvis/compounding-2026-09-12, "
                "found kaalvis/compounding-2026-09-14"
            ],
            errors,
        )


if __name__ == "__main__":
    unittest.main()

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHECKER = ROOT / "tools" / "check_kaalvis_gate_binding.py"
REQUIRED_BRANCH = "kaalvis/compounding-2026-09-12"

def run(*args, cwd, check=True):
    return subprocess.run(
        args,
        cwd=cwd,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


class KaalvisGateBindingTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        tools = self.repo / "tools"
        tools.mkdir()
        checker = Path(os.environ.get("KAALVIS_BINDING_CHECKER", DEFAULT_CHECKER))
        self.checker = tools / "check_kaalvis_gate_binding.py"
        shutil.copyfile(checker, self.checker)

        run("git", "init", "-b", REQUIRED_BRANCH, cwd=self.repo)
        run("git", "config", "user.name", "Kaalvis Test", cwd=self.repo)
        run("git", "config", "user.email", "kaalvis-test@example.invalid", cwd=self.repo)
        (self.repo / "marker").write_text("gate binding fixture\n", encoding="utf-8")
        run("git", "add", "marker", cwd=self.repo)
        run("git", "commit", "-m", "fixture", cwd=self.repo)

    def tearDown(self):
        self.tempdir.cleanup()

    def git_output(self, *args):
        return run("git", *args, cwd=self.repo).stdout.strip()

    def invoke(self, expected):
        return run(
            sys.executable,
            str(self.checker),
            "--expect",
            expected,
            cwd=self.repo,
            check=False,
        )

    def test_rejects_wrong_branch_and_names_both_values(self):
        head = self.git_output("rev-parse", "HEAD")
        wrong_branch = "kaalvis/wrong-branch"
        run("git", "switch", "-c", wrong_branch, cwd=self.repo)

        result = self.invoke(head)

        self.assertNotEqual(0, result.returncode)
        self.assertIn(REQUIRED_BRANCH, result.stderr)
        self.assertIn(wrong_branch, result.stderr)

    def test_rejects_detached_head_with_explicit_message(self):
        head = self.git_output("rev-parse", "HEAD")
        run("git", "checkout", "--detach", "HEAD", cwd=self.repo)

        result = self.invoke(head)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("detached HEAD", result.stderr)

    def test_rejects_wrong_head_and_branch_and_names_both_mismatches(self):
        actual_head = self.git_output("rev-parse", "HEAD")
        expected_head = "0" * 40
        wrong_branch = "kaalvis/wrong-head-and-branch"
        run("git", "switch", "-c", wrong_branch, cwd=self.repo)

        result = self.invoke(expected_head)

        self.assertNotEqual(0, result.returncode)
        self.assertIn(REQUIRED_BRANCH, result.stderr)
        self.assertIn(wrong_branch, result.stderr)
        self.assertIn(expected_head, result.stderr)
        self.assertIn(actual_head, result.stderr)

    def test_accepts_matching_head_and_branch(self):
        head = self.git_output("rev-parse", "HEAD")

        result = self.invoke(head)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            [f"KAALVIS_GATE_HEAD={head}", f"KAALVIS_GATE_BRANCH={REQUIRED_BRANCH}"],
            result.stdout.splitlines(),
        )


if __name__ == "__main__":
    unittest.main()

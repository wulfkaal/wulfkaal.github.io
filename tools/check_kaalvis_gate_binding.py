#!/usr/bin/env python3
"""Fail closed unless a kaalvis gate is bound to its current commit and branch."""

import argparse
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parent.parent
REQUIRED_BRANCH = "kaalvis/compounding-2026-09-12"


def git_output(*args):
    result = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def validate_binding(head, branch, expected):
    errors = []
    if branch != REQUIRED_BRANCH:
        errors.append(f"required branch {REQUIRED_BRANCH}, found {branch}")
    if head != expected:
        errors.append(f"expected commit {expected}, found {head}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect", required=True, help="full commit SHA under review")
    args = parser.parse_args()

    try:
        head = git_output("rev-parse", "HEAD")
        branch = git_output("symbolic-ref", "--short", "HEAD")
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or str(exc)
        print(f"kaalvis gate binding failed: {detail}", file=sys.stderr)
        return 1

    errors = validate_binding(head, branch, args.expect)
    if errors:
        for error in errors:
            print(f"kaalvis gate binding failed: {error}", file=sys.stderr)
        return 1

    print(f"KAALVIS_GATE_HEAD={head}")
    print(f"KAALVIS_GATE_BRANCH={branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

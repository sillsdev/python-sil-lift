"""Run everything CI runs, in one command: lint, format check, type-check, and
tests under the 90% coverage floor.

Usage: python scripts/check.py
"""

import subprocess
import sys

CHECKS: list[list[str]] = [
    [sys.executable, "-m", "ruff", "check", "."],
    [sys.executable, "-m", "ruff", "format", "--check", "."],
    [sys.executable, "-m", "mypy"],
    [
        sys.executable,
        "-m",
        "pytest",
        "--cov=sil_lift",
        "--cov-report=term-missing",
        "--cov-fail-under=90",
    ],
]


def main() -> int:
    failed: list[str] = []
    for cmd in CHECKS:
        name = " ".join(cmd[2:])
        print(f"\n=== {name} ===", flush=True)
        if subprocess.run(cmd).returncode != 0:
            failed.append(name)
    if failed:
        print(f"\nFAILED: {', '.join(failed)}")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

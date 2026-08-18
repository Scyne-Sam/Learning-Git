#!/usr/bin/env python3
"""Record the outcome of the validation hooks for the commit at HEAD.

Runs as a pre-commit `post-commit` stage hook. The commit has already been
created at this point, so the hooks are replayed against the files it touched
and the per-hook result is appended to the ledger. Replaying is what lets the
ledger notice a commit that was pushed through with `--no-verify`.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "validation-log.jsonl"
RESULT_RE = re.compile(r"^(?P<name>.*?)\.{3,}(?P<status>Passed|Failed|Skipped)$")


def pre_commit_cmd() -> list[str]:
    """Locate pre-commit; git GUIs often commit without the venv on PATH."""
    found = shutil.which("pre-commit")
    if found:
        return [found]
    venv = ROOT / ".venv" / "bin" / "pre-commit"
    if venv.exists():
        return [str(venv)]
    return [sys.executable, "-m", "pre_commit"]


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True, cwd=ROOT
    ).stdout.strip()


def changed_files(commit: str) -> list[str]:
    out = git("show", "--pretty=format:", "--name-only", commit)
    return [line for line in out.splitlines() if line]


def parse_results(output: str) -> list[dict[str, str]]:
    results = []
    for line in output.splitlines():
        match = RESULT_RE.match(line.rstrip())
        if match:
            name = match["name"].replace("(no files to check)", "").strip()
            results.append({"hook": name, "status": match["status"]})
    return results


def main() -> int:
    commit = git("rev-parse", "HEAD")
    files = changed_files(commit)
    if not files:
        return 0

    proc = subprocess.run(
        [*pre_commit_cmd(), "run", "--color=never", "--files", *files],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    results = parse_results(proc.stdout)
    failed = [r["hook"] for r in results if r["status"] == "Failed"]

    entry = {
        "commit": commit,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overall": "failed" if failed else "passed",
        "hooks": results,
    }
    with LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")

    if failed:
        print(
            f"warning: commit {commit[:7]} recorded with failing checks: "
            f"{', '.join(failed)}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate a Markdown page per commit from git history and the validation ledger.

Output lands in docs/commits/ and is gitignored -- it is rebuilt from git on
every docs build, so it never needs to be committed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "commits"
LEDGER = ROOT / "validation-log.jsonl"

FIELD_SEP = "\x1f"
RECORD_SEP = "\x1e"
STATUS_ICON = {"passed": ":material-check-circle:{ .pass }", "failed": ":material-close-circle:{ .fail }"}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True, cwd=ROOT
    ).stdout


def load_ledger() -> dict[str, dict]:
    if not LEDGER.exists():
        return {}
    records: dict[str, dict] = {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entry = json.loads(line)
            # Later entries win, so a re-run supersedes an earlier record.
            records[entry["commit"]] = entry
    return records


def load_commits() -> list[dict[str, str]]:
    fmt = FIELD_SEP.join(["%H", "%h", "%an", "%aI", "%s", "%b", "%P"]) + RECORD_SEP
    raw = git("log", f"--format={fmt}")
    commits = []
    for chunk in raw.split(RECORD_SEP):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        full, short, author, date, subject, body, parents = chunk.split(FIELD_SEP)
        commits.append(
            {
                "full": full,
                "short": short,
                "author": author,
                "date": date,
                "subject": subject,
                "body": body.strip(),
                "parents": parents.split(),
            }
        )
    return commits


def status_cell(entry: dict | None) -> str:
    if entry is None:
        return ":material-help-circle:{ .unknown } No record"
    icon = STATUS_ICON[entry["overall"]]
    return f"{icon} {entry['overall'].capitalize()}"


def write_commit_page(commit: dict, entry: dict | None) -> None:
    stat = git("show", "--stat", "--pretty=format:", commit["full"]).strip()
    lines = [
        f"# {commit['subject']}",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Commit | `{commit['full']}` |",
        f"| Author | {commit['author']} |",
        f"| Date | {commit['date']} |",
        f"| Parents | {' '.join(f'`{p[:7]}`' for p in commit['parents']) or '_root commit_'} |",
        f"| Validation | {status_cell(entry)} |",
        "",
        "## Message",
        "",
        "```text",
        commit["subject"],
    ]
    if commit["body"]:
        lines += ["", commit["body"]]
    lines += ["```", ""]

    lines += ["## Validation", ""]
    if entry is None:
        lines += [
            "!!! warning \"No validation record\"",
            "    This commit predates the ledger, or was created with `--no-verify`",
            "    before the post-commit hook was installed.",
            "",
        ]
    else:
        if entry["overall"] == "failed":
            lines += [
                "!!! danger \"Checks failed for this commit\"",
                "    The commit was recorded with failing hooks -- most likely committed",
                "    with `--no-verify`.",
                "",
            ]
        lines += ["| Hook | Result |", "| --- | --- |"]
        for hook in entry["hooks"]:
            lines.append(f"| {hook['hook']} | {hook['status']} |")
        lines += ["", f"_Recorded {entry['recorded_at']}._", ""]

    if stat:
        lines += ["## Files changed", "", "```text", stat, "```", ""]

    (OUT_DIR / f"{commit['short']}.md").write_text("\n".join(lines), encoding="utf-8")


def write_index(commits: list[dict], ledger: dict[str, dict]) -> None:
    passed = sum(1 for c in commits if ledger.get(c["full"], {}).get("overall") == "passed")
    failed = sum(1 for c in commits if ledger.get(c["full"], {}).get("overall") == "failed")
    unknown = len(commits) - passed - failed

    lines = [
        "# Commit log",
        "",
        "Generated from `git log` on every docs build. Each entry links to the full",
        "commit message and the validation result recorded when it was created.",
        "",
        f"**{len(commits)} commits** — {passed} passed, {failed} failed, {unknown} without a record.",
        "",
        "| Commit | Date | Subject | Validation |",
        "| --- | --- | --- | --- |",
    ]
    for commit in commits:
        entry = ledger.get(commit["full"])
        subject = commit["subject"].replace("|", "\\|")
        lines.append(
            f"| [`{commit['short']}`]({commit['short']}.md) "
            f"| {commit['date'][:10]} | {subject} | {status_cell(entry)} |"
        )
    lines.append("")
    (OUT_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="run mkdocs build --strict afterwards")
    parser.add_argument("--site-dir", default="site")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for stale in OUT_DIR.glob("*.md"):
        stale.unlink()

    commits = load_commits()
    ledger = load_ledger()
    for commit in commits:
        write_commit_page(commit, ledger.get(commit["full"]))
    write_index(commits, ledger)
    print(f"generated {len(commits) + 1} pages in {OUT_DIR.relative_to(ROOT)}")

    if args.build:
        return subprocess.run(
            ["mkdocs", "build", "--strict", "--site-dir", args.site_dir], cwd=ROOT
        ).returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

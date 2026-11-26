#!/usr/bin/env python3
"""Record a local engineering evidence snapshot; never export research records."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

PROTOCOL_ID = "ARC-ADHD-ENGINEERING-SNAPSHOT-v1"
SOURCES = (
    "VERSION",
    "PROJECT_STATE.yaml",
    "research/quality_manifest.yaml",
    "schemas/recovery_event.schema.json",
    "config/core_task.signal_gate.example.json",
)
PYTHON_CHECKS = (
    ("unit", ("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py")),
    ("governance", ("scripts/audit_research_governance.py",)),
    ("state_machine", ("scripts/validate_state_machine.py",)),
)


def _run(argv: list[str], cwd: Path, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False,
    )


def git_state(root: Path) -> tuple[str, bool]:
    """Read the committed revision and detect uncommitted changes explicitly."""
    head = _run(["git", "rev-parse", "HEAD"], root, timeout=15)
    if head.returncode or not re.fullmatch(r"[a-fA-F0-9]{40}", head.stdout.strip()):
        raise ValueError("A Git SHA-1 commit is required for a reproducible snapshot")
    status = _run(["git", "status", "--porcelain", "--untracked-files=normal"], root, timeout=15)
    if status.returncode:
        raise ValueError("Cannot determine whether the Git worktree is dirty")
    return head.stdout.strip(), bool(status.stdout.strip())


def source_hashes(root: Path) -> dict[str, str]:
    """Hash only fixed, repository-controlled contract inputs."""
    result = {}
    for relative in SOURCES:
        path = root / relative
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Missing or unsafe source: {relative}")
        result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def output_path(root: Path, relative: str) -> Path:
    """Disallow writes outside the ignored local preview directory."""
    if (root / "_site").is_symlink():
        raise ValueError("The _site output directory may not be a symlink")
    safe_root = (root / "_site").resolve()
    target = (root / relative).resolve()
    if not safe_root.is_relative_to(root.resolve()) or not target.is_relative_to(safe_root):
        raise ValueError("Output must stay inside the repository's _site directory")
    if target == safe_root:
        raise ValueError("Output must name a JSON file")
    if target.suffix != ".json":
        raise ValueError("Output must be a JSON file")
    return target


def snapshot(root: Path, sha: str, dirty: bool, run_python: bool = False) -> dict:
    """Construct an engineering-only report with explicit unexecuted checks."""
    if not re.fullmatch(r"[a-fA-F0-9]{40}", sha):
        raise ValueError("Expected a full 40-character Git commit SHA")
    checks = []
    for name, args in PYTHON_CHECKS:
        command = [sys.executable, *args]
        entry = {"name": name, "cwd": ".", "command": command, "status": "NOT_RUN"}
        if run_python:
            try:
                completed = _run(command, root)
                entry["status"] = "PASS" if completed.returncode == 0 else "FAIL"
                entry["exit_code"] = completed.returncode
            except (OSError, subprocess.TimeoutExpired):
                entry["status"] = "BLOCKED"
        checks.append(entry)
    checks.extend((
        {"name": "android_core", "cwd": "app/mobile-android-kotlin",
         "command": ["gradle", ":app:testCoreDebugUnitTest", ":app:lintCoreDebug"],
         "status": "NOT_RUN"},
        {"name": "latex_p01", "cwd": "manuscripts/01-core-closed-loop",
         "command": ["latexmk", "-pdf", "-interaction=nonstopmode", "main.tex"],
         "status": "NOT_RUN"},
        {"name": "device_byod", "command": ["physical-device-acceptance"],
         "status": "BLOCKED", "reason": "Physical device and authorization required"},
    ))
    return {
        "protocol_id": PROTOCOL_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "engineering_only_no_participants",
        "git_sha": sha,
        "worktree_dirty": dirty,
        "version": (root / "VERSION").read_text(encoding="utf-8").strip(),
        "python_version": platform.python_version(),
        "source_sha256": source_hashes(root),
        "checks": checks,
        "interpretation": "No participant, device, clinical or release readiness is established.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", default="_site/reproducibility/local-snapshot.json",
        help="Local JSON destination strictly under _site/",
    )
    parser.add_argument(
        "--run-python-checks", action="store_true",
        help="Execute three fixed local Python checks; never dispatch Actions",
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        destination = output_path(root, args.output)
        sha, dirty = git_state(root)
        report = snapshot(root, sha, dirty, args.run_python_checks)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Evidence snapshot: {destination.relative_to(root)}")
    for item in report["checks"]:
        print(f"{item['name']}: {item['status']}")
    # Only explicitly requested Python checks gate this engineering command.
    # A blocked/timeout check is not a successful run.
    if args.run_python_checks:
        return int(any(
            item["status"] != "PASS"
            for item in report["checks"][:len(PYTHON_CHECKS)]
        ))
    return 0


if __name__ == "__main__":
    sys.exit(main())

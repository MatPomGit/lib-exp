"""Local evidence snapshot must fail closed on input and output paths."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import record_reproducibility as evidence  # noqa: E402

SHA = "a" * 40


class EvidenceSnapshotTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in evidence.SOURCES:
            file = self.root / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("v1\n", encoding="utf-8")

    def test_report_separates_executed_and_blocked_evidence(self):
        report = evidence.snapshot(self.root, SHA, dirty=True)
        self.assertEqual(report["git_sha"], SHA)
        self.assertTrue(report["worktree_dirty"])
        self.assertEqual(report["version"], "v1")
        self.assertEqual(report["source_sha256"]["VERSION"], hashlib.sha256(b"v1\n").hexdigest())
        self.assertEqual([x["status"] for x in report["checks"]],
                         ["NOT_RUN"] * 5 + ["BLOCKED"])
        self.assertNotIn("participant_records", json.dumps(report))

    def test_output_rejects_escape_and_non_json(self):
        self.assertEqual(evidence.output_path(self.root, "_site/a.json"),
                         self.root / "_site" / "a.json")
        for bad in ("../participant.json", "private.json", "_site/a.txt", "_site/../secret.json"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                evidence.output_path(self.root, bad)

    def test_rejects_symlinked_output_root(self):
        (self.root / "_site").symlink_to(self.root / "research", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            evidence.output_path(self.root, "_site/a.json")

    def test_rejects_symlink_source(self):
        file = self.root / evidence.SOURCES[0]
        file.unlink()
        file.symlink_to(self.root / evidence.SOURCES[1])
        with self.assertRaisesRegex(ValueError, "unsafe source"):
            evidence.source_hashes(self.root)

    def test_rejects_invalid_revision(self):
        with self.assertRaises(ValueError):
            evidence.snapshot(self.root, "short", dirty=False)

    def test_runs_only_explicit_python_checks(self):
        from subprocess import CompletedProcess
        with patch.object(evidence, "_run", return_value=CompletedProcess([], 0, "", "")) as run:
            report = evidence.snapshot(self.root, SHA, dirty=False, run_python=True)
        self.assertEqual(run.call_count, 3)
        self.assertEqual([x["status"] for x in report["checks"][:3]], ["PASS"] * 3)
        self.assertEqual(report["checks"][3]["status"], "NOT_RUN")

    def test_requested_checks_blocked_return_nonzero(self):
        import contextlib
        import io

        fake_script = self.root / "scripts" / "record_reproducibility.py"
        fake_script.parent.mkdir(exist_ok=True)
        with (
            patch.object(evidence, "__file__", str(fake_script)),
            patch.object(evidence, "git_state", return_value=(SHA, False)),
            patch.object(evidence, "_run", side_effect=OSError("unavailable")),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            code = evidence.main(["--run-python-checks"])
        self.assertEqual(code, 1)
        record = json.loads(
            (self.root / "_site/reproducibility/local-snapshot.json").read_text()
        )
        self.assertEqual([x["status"] for x in record["checks"][:3]],
                         ["BLOCKED"] * 3)

    def test_requested_checks_nonzero_exit_return_nonzero(self):
        import contextlib
        import io
        from subprocess import CompletedProcess

        fake_script = self.root / "scripts" / "record_reproducibility.py"
        fake_script.parent.mkdir(exist_ok=True)
        with (
            patch.object(evidence, "__file__", str(fake_script)),
            patch.object(evidence, "git_state", return_value=(SHA, False)),
            patch.object(evidence, "_run", return_value=CompletedProcess([], 5, "", "")),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            code = evidence.main(["--run-python-checks"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()

"""Offline checks use invented data only; no clinical paths are configured."""
from pathlib import Path
import hashlib
import importlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_synthetic import generate
import gold_utils
from validate_candidate import validate


class CandidateTests(unittest.TestCase):
    def test_synthetic_generation_deterministic_and_consistent(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a, b = generate(first), generate(second)
            self.assertEqual(hashlib.sha256(a.read_bytes()).digest(), hashlib.sha256(b.read_bytes()).digest())
            conn = sqlite3.connect(a.as_uri() + "?mode=ro", uri=True)
            self.assertEqual(conn.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM gold_reports_v2").fetchone()[0], 120)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM gold_clinical_events_v2").fetchone()[0], 600)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM gold_reports_v2 WHERE patient_name NOT LIKE 'SYNTHETIC_%'").fetchone()[0], 0)
            conn.close()
            with self.assertRaises(FileExistsError):
                generate(first)

    def test_private_mode_requires_explicit_configuration(self):
        with patch.dict(os.environ, {"ECHO_MODE": "PRIVATE_ANALYSIS"}, clear=True):
            module = importlib.reload(gold_utils)
            with self.assertRaises(ValueError):
                module.get_gold_db_path()

    def test_unknown_mode_fails_closed(self):
        with patch.dict(os.environ, {"ECHO_MODE": "UNKNOWN"}, clear=True):
            module = importlib.reload(gold_utils)
            with self.assertRaises(ValueError):
                module.get_gold_db_path()

    def test_public_mode_cannot_select_another_database(self):
        with patch.dict(os.environ, {"ECHO_MODE": "PUBLIC_DEMO"}, clear=True):
            module = importlib.reload(gold_utils)
            path = module.get_gold_db_path()
            with self.assertRaises(ValueError):
                module.connect_gold_readonly(ROOT / "requirements.txt")
            connection = module.connect_gold_readonly(path)
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM gold_reports_v2")
            connection.close()

    def test_notebooks_have_no_saved_outputs_or_attachments(self):
        paths = list((ROOT / "notebooks").glob("*.ipynb"))
        self.assertEqual(len(paths), 5)
        for path in paths:
            doc = json.loads(path.read_text(encoding="utf-8"))
            for cell in doc["cells"]:
                self.assertFalse(cell.get("outputs"))
                self.assertFalse(cell.get("attachments"))
                self.assertFalse(cell.get("metadata"))
                if cell["cell_type"] == "code":
                    self.assertIsNone(cell["execution_count"])

    def test_no_database_document_or_history_in_checkout(self):
        from editorial_release import approved_editorial_files
        reviewed = approved_editorial_files(ROOT)
        blocked = {".db", ".sqlite", ".sqlite3", ".docx", ".pdf", ".csv", ".parquet", ".pkl", ".zip"}
        for path in ROOT.rglob("*"):
            self.assertNotEqual(path.name, ".git")
            if path.is_file():
                if reviewed.get(path.relative_to(ROOT).as_posix()) != 'aggregate_table':
                    self.assertNotIn(path.suffix.lower(), blocked)
                with path.open("rb") as stream:
                    self.assertNotEqual(stream.read(16), b"SQLite format 3\x00")

    def test_validator_rejects_database_disguised_as_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "innocent.md"
            path.write_bytes(b"SQLite format 3\x00" + b"SYNTHETIC_TEST_HEADER")
            result = validate(directory)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("signature" in issue["category"] for issue in result["issues"]))

    def test_validator_decodes_notebook_paths_before_scanning(self):
        with tempfile.TemporaryDirectory() as directory:
            invented_path = "X" + chr(58) + chr(92) + "synthetic_test"
            document = {"cells": [], "metadata": {"example": invented_path}}
            (Path(directory) / "example.ipynb").write_text(json.dumps(document), encoding="utf-8")
            result = validate(directory)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("absolute Windows path" in issue["category"] for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()

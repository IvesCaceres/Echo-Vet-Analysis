"""Only the two explicitly reviewed metadata paths extend the public allowlist."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_candidate import validate


class PublicMetadataTests(unittest.TestCase):
    def test_only_exact_metadata_paths_are_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = ["CITATION.cff", ".github/workflows/public-checks.yml",
                     "unreviewed.cff", ".github/workflows/unreviewed.yml"]
            for relative in paths:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("name: synthetic metadata\n", encoding="utf-8")
            rejected = {item["path"] for item in validate(root)["issues"]
                        if item["category"] == "unapproved file type"}
            self.assertEqual(rejected, {"unreviewed.cff", ".github/workflows/unreviewed.yml"})

    def test_metadata_exceptions_still_receive_sensitive_path_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "CITATION.cff").write_text("source: " + "Z" + ":" + "/private/input\n", encoding="utf-8")
            self.assertTrue(any(item["category"] == "absolute Windows path"
                                for item in validate(root)["issues"]))

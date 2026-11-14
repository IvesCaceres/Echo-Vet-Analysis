"""Disclosure-control tests use invented aggregate fixtures only."""
from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from aggregate_release import (TableSpec, prepare_review_package, synthetic_example,
                               validate_public_package, approved_release_files, load_reviewed_release)
from validate_candidate import validate


def fixture(counts=(60, 60), total=120, table_id="SPECIES"):
    return {"table_id": table_id, "denominator": total,
            "rows": [{"category_code": c, "count": n} for c, n in zip(("CANINE", "FELINE"), counts)]}


class AggregateReleaseTests(unittest.TestCase):
    def setUp(self):
        self.spec = TableSpec("SPECIES", ("CANINE", "FELINE"), "REPORTS")

    def package(self, tables, specs=None):
        return prepare_review_package("SYNTHETIC_DEMO", tables, specs or [self.spec],
                                      min_count=10, cohort_ref="SYNTHETIC_COHORT")

    def test_success_is_pending_review_not_real(self):
        p = self.package([fixture()])
        self.assertEqual(p["kind"], "SYNTHETIC_DEMO")
        self.assertEqual(p["status"], "PENDING_MANUAL_REVIEW")
        self.assertTrue(p["manual_review_required"])
        self.assertEqual(p["tables"][0]["rows"][0]["percentage"], 50.0)

    def test_primary_suppression_withholds_totals_percentages_and_other_tables(self):
        sibling = TableSpec("SIBLING", ("CANINE", "FELINE"), "REPORTS")
        p = self.package([fixture((3, 117)), fixture(table_id="SIBLING")], [self.spec, sibling])
        self.assertEqual(p["status"], "WITHHELD")
        self.assertEqual(p["tables"], [])
        self.assertNotIn("denominator", json.dumps(p))
        self.assertNotIn("percentage", json.dumps(p))

    def test_small_complement_is_blocked_even_without_explicit_complement_row(self):
        spec = TableSpec("BINARY", ("POSITIVE",), "REPORTS", exclusive_partition=False)
        table = {"table_id": "BINARY", "denominator": 100, "rows": [{"category_code": "POSITIVE", "count": 95}]}
        self.assertEqual(self.package([table], [spec])["status"], "WITHHELD")

    def test_identifiers_and_free_text_are_rejected(self):
        for key in ["report_id", "patient_name", "source_text", "source_path", "caption"]:
            table = fixture()
            table["rows"][0][key] = "SYNTHETIC_REJECTED_FIELD"
            with self.assertRaises(ValueError):
                self.package([table])

    def test_caller_percentages_and_unapproved_statistics_are_rejected(self):
        for key in ["percentage", "minimum", "maximum", "mean", "p_value", "ci_lower"]:
            table = fixture()
            table["rows"][0][key] = 1
            with self.assertRaises(ValueError):
                self.package([table])

    def test_invalid_counts_and_partitions_are_rejected(self):
        for counts in [(-1, 121), (True, 119), (60.0, 60), (60, 61)]:
            with self.assertRaises(ValueError):
                self.package([fixture(counts)])

    def test_missing_or_duplicate_category_is_rejected(self):
        table = fixture()
        table["rows"].pop()
        with self.assertRaises(ValueError):
            self.package([table])
        table = fixture()
        table["rows"][1]["category_code"] = "CANINE"
        with self.assertRaises(ValueError):
            self.package([table])

    def test_shared_denominator_must_be_consistent(self):
        sibling = TableSpec("SIBLING", ("CANINE", "FELINE"), "REPORTS")
        with self.assertRaises(ValueError):
            self.package([fixture(), fixture((50, 50), 100, "SIBLING")], [self.spec, sibling])

    def test_zero_and_full_cells_do_not_bypass_manual_review(self):
        p = self.package([fixture((0, 120))])
        self.assertTrue(p["manual_review_required"])
        self.assertNotEqual(p["status"], "APPROVED_FOR_PUBLIC_CONTENT")

    def test_demo_is_not_relabelled_real(self):
        p = synthetic_example()
        self.assertTrue(validate_public_package(p))
        p["kind"] = "REAL_AGGREGATED"
        p["status"] = "APPROVED_FOR_PUBLIC_CONTENT"
        p["manual_review_required"] = False
        with self.assertRaises(ValueError):
            validate_public_package(p)

    def test_real_pending_cannot_be_displayed(self):
        p = self.package([fixture()])
        p["kind"] = "REAL_PENDING_REVIEW"
        with self.assertRaises(ValueError):
            validate_public_package(p)

    def test_empty_manifest_approves_nothing(self):
        self.assertEqual(approved_release_files(ROOT), {})
        with self.assertRaises(ValueError):
            load_reviewed_release(ROOT, "published/releases/UNAPPROVED/statistics.json")

    def test_unapproved_aggregate_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "published" / "releases" / "UNAPPROVED"
            p.mkdir(parents=True)
            (p / "statistics.json").write_text(json.dumps(synthetic_example()), encoding="utf-8")
            self.assertEqual(validate(directory)["status"], "FAIL")

    def test_percentage_tampering_is_rejected(self):
        p = synthetic_example()
        p["tables"][0]["rows"][0]["percentage"] = 49.9
        with self.assertRaises(ValueError):
            validate_public_package(p)

    def test_withheld_package_cannot_be_displayed(self):
        with self.assertRaises(ValueError):
            validate_public_package(self.package([fixture((3, 117))]))

    def test_approved_kind_cannot_be_requested_at_computation(self):
        with self.assertRaises(ValueError):
            prepare_review_package("REAL_AGGREGATED", [fixture()], [self.spec], min_count=10, cohort_ref="TEST")

    def test_package_cannot_carry_private_metadata(self):
        p = synthetic_example()
        p["source_path"] = "SYNTHETIC_REJECTED_FIELD"
        with self.assertRaises(ValueError):
            validate_public_package(p)

    def test_manifest_requires_all_review_decisions_before_reading_package(self):
        with tempfile.TemporaryDirectory() as directory:
            published = Path(directory) / "published"
            published.mkdir()
            release = {"release_id": "TEST", "package_path": "published/releases/TEST/statistics.json",
                       "package_sha256": "0" * 64, "artifacts": [], "privacy_review": "PENDING",
                       "methodology_review": "APPROVED", "owner_content_review": "APPROVED",
                       "cross_release_review": "APPROVED", "review_reference": "TEST_REVIEW"}
            (published / "approved-manifest.json").write_text(json.dumps({"schema_version": 1, "releases": [release]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                approved_release_files(directory)

    def test_changed_package_is_rejected_by_exact_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            published = Path(directory) / "published"
            path = published / "releases" / "TEST"
            path.mkdir(parents=True)
            (path / "statistics.json").write_text(json.dumps(synthetic_example()), encoding="utf-8")
            release = {"release_id": "TEST", "package_path": "published/releases/TEST/statistics.json",
                       "package_sha256": "0" * 64, "artifacts": [], "privacy_review": "APPROVED",
                       "methodology_review": "APPROVED", "owner_content_review": "APPROVED",
                       "cross_release_review": "APPROVED", "review_reference": "TEST_REVIEW"}
            (published / "approved-manifest.json").write_text(json.dumps({"schema_version": 1, "releases": [release]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                approved_release_files(directory)


if __name__ == "__main__":
    unittest.main()

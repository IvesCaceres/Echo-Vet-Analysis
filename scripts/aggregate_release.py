"""Disclosure-aware aggregate package design. No clinical database connector or export CLI.

Only invented fixtures are used during preparation. Numerical eligibility is NOT
privacy approval. Real packages need separate human review and exact-file approval.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import re


@dataclass(frozen=True)
class TableSpec:
    table_id: str
    category_codes: tuple[str, ...]
    denominator_ref: str
    unit: str = "REPORT"
    exclusive_partition: bool = True


def _code(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", value) is not None


def _integer(value):
    return type(value) is int and value >= 0


def prepare_review_package(origin, tables, specs, *, min_count, cohort_ref):
    """Pure transformation of already aggregated input; never queries or writes.

    A positive small cell OR small complement withholds the ENTIRE package,
    including totals, other tables, percentages and denominators. This is a
    conservative first implementation, not a general secondary-suppression solver.
    """
    if origin not in {"SYNTHETIC_DEMO", "REAL_PENDING_REVIEW"}:
        raise ValueError("Source kind must not claim approval")
    if not _integer(min_count) or min_count < 2 or not _code(cohort_ref):
        raise ValueError("Explicit policy and protocol cohort reference required")
    if not isinstance(specs, (list, tuple)) or not specs:
        raise ValueError("Reviewed table specifications required")
    by_id = {}
    for spec in specs:
        if (not isinstance(spec, TableSpec) or not _code(spec.table_id)
                or not _code(spec.denominator_ref) or spec.unit not in {"REPORT", "EVENT"}
                or not isinstance(spec.category_codes, tuple) or not spec.category_codes
                or len(set(spec.category_codes)) != len(spec.category_codes)
                or any(not _code(c) for c in spec.category_codes) or spec.table_id in by_id):
            raise ValueError("Invalid or duplicated table specification")
        by_id[spec.table_id] = spec
    if not isinstance(tables, list) or len(tables) != len(by_id):
        raise ValueError("Exactly the predeclared table set is required")
    prepared, denominators, seen, unsafe = [], {}, set(), False
    for table in tables:
        if not isinstance(table, dict) or set(table) != {"table_id", "denominator", "rows"}:
            raise ValueError("Unknown input fields; individual data and arbitrary metadata are rejected")
        table_id = table["table_id"]
        if table_id not in by_id or table_id in seen:
            raise ValueError("Unexpected or duplicated table")
        seen.add(table_id)
        spec, total, rows = by_id[table_id], table["denominator"], table["rows"]
        if not _integer(total) or total == 0 or not isinstance(rows, list):
            raise ValueError("Positive integer denominator and aggregate rows required")
        if spec.denominator_ref in denominators and denominators[spec.denominator_ref] != total:
            raise ValueError("Shared denominator reference has inconsistent counts")
        denominators[spec.denominator_ref] = total
        counts = {}
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"category_code", "count"}:
                raise ValueError("Unapproved row fields; no identifiers, free text or caller percentages")
            category, count = row["category_code"], row["count"]
            if category not in spec.category_codes or category in counts or not _integer(count) or count > total:
                raise ValueError("Unapproved category or invalid count")
            counts[category] = count
            unsafe |= 0 < count < min_count or 0 < total - count < min_count
        if set(counts) != set(spec.category_codes):
            raise ValueError("Missing predeclared categories; omission must not hide small groups")
        if spec.exclusive_partition and sum(counts.values()) != total:
            raise ValueError("Exclusive categories must sum to the declared denominator")
        unsafe |= total < min_count
        prepared.append({"table_id": table_id, "denominator_ref": spec.denominator_ref,
                         "unit": spec.unit, "exclusive_partition": spec.exclusive_partition,
                         "denominator": total,
                         "rows": [{"category_code": c, "count": counts[c],
                                   "percentage": round(100 * counts[c] / total, 1)}
                                  for c in spec.category_codes]})
    base = {"schema_version": 1, "kind": origin, "cohort_ref": cohort_ref,
            "policy": {"min_count": min_count, "strategy": "WHOLE_PACKAGE_WITHHOLDING"},
            "manual_review_required": True}
    if unsafe:
        return {**base, "status": "WITHHELD", "tables": [],
                "reason": "Package needs private coarsening/review; no numeric result released"}
    return {**base, "status": "PENDING_MANUAL_REVIEW", "tables": prepared}


def synthetic_example():
    """Invented aggregate fixture; not computed from any real corpus."""
    specs = [TableSpec("SPECIES", ("CANINE", "FELINE"), "DEMO_REPORTS")]
    return prepare_review_package("SYNTHETIC_DEMO", [
        {"table_id": "SPECIES", "denominator": 120,
         "rows": [{"category_code": "CANINE", "count": 60},
                  {"category_code": "FELINE", "count": 60}]}],
        specs, min_count=10, cohort_ref="SYNTHETIC_COHORT")


def _within(root, relative):
    if not isinstance(relative, str) or "\\" in relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Relative public paths required")
    target = (root / relative).resolve(strict=True)
    if not target.is_relative_to(root.resolve()) or target.is_symlink():
        raise ValueError("Release path escapes the public root")
    return target


def validate_public_package(package):
    """Validate approved-result structure without trusting arbitrary input fields."""
    required = {"schema_version", "kind", "cohort_ref", "policy", "manual_review_required", "status", "tables"}
    if not isinstance(package, dict) or set(package) != required:
        raise ValueError("Unapproved package fields")
    if package["schema_version"] != 1 or package["kind"] not in {"SYNTHETIC_DEMO", "REAL_AGGREGATED"}:
        raise ValueError("Only synthetic demos or approved real aggregates can be displayed")
    if package["kind"] == "REAL_AGGREGATED" and str(package["cohort_ref"]).startswith("SYNTHETIC"):
        raise ValueError("Synthetic provenance must not be relabeled as real")
    if package["status"] != "APPROVED_FOR_PUBLIC_CONTENT" or package["manual_review_required"] is not False:
        if not (package["kind"] == "SYNTHETIC_DEMO" and package["status"] == "PENDING_MANUAL_REVIEW"):
            raise ValueError("Unreviewed real package")
    if not isinstance(package["policy"], dict) or set(package["policy"]) != {"min_count", "strategy"}:
        raise ValueError("Unapproved policy fields")
    if package["policy"]["strategy"] != "WHOLE_PACKAGE_WITHHOLDING":
        raise ValueError("Unsupported policy")
    specs, tables = [], []
    if not isinstance(package["tables"], list) or not package["tables"]:
        raise ValueError("No displayable aggregate tables")
    for table in package["tables"]:
        if not isinstance(table, dict) or set(table) != {"table_id", "denominator_ref", "unit", "exclusive_partition", "denominator", "rows"}:
            raise ValueError("Unapproved table metadata")
        if type(table["exclusive_partition"]) is not bool:
            raise ValueError("Partition semantics required")
        if not isinstance(table["rows"], list) or not table["rows"]:
            raise ValueError("Aggregate rows required")
        if any(not isinstance(r, dict) or set(r) != {"category_code", "count", "percentage"} for r in table["rows"]):
            raise ValueError("Unapproved public row")
        specs.append(TableSpec(table["table_id"], tuple(r["category_code"] for r in table["rows"]),
                               table["denominator_ref"], table["unit"], table["exclusive_partition"]))
        tables.append({"table_id": table["table_id"], "denominator": table["denominator"],
                       "rows": [{"category_code": r["category_code"], "count": r["count"]} for r in table["rows"]]})
    check = prepare_review_package("SYNTHETIC_DEMO", tables, specs,
                                   min_count=package["policy"]["min_count"], cohort_ref=package["cohort_ref"])
    if check["status"] == "WITHHELD" or check["tables"] != package["tables"]:
        raise ValueError("Disclosure/percentage checks failed")
    return True


def approved_release_files(code_root):
    """Hash-bound administrative allowlist; not a digital signature or consent proof."""
    root = Path(code_root).resolve()
    manifest = root / "published" / "approved-manifest.json"
    if not manifest.is_file():
        return {}
    document = json.loads(manifest.read_text(encoding="utf-8"))
    if set(document) != {"schema_version", "releases"} or document["schema_version"] != 1 or not isinstance(document["releases"], list):
        raise ValueError("Invalid public approval manifest")
    approved = {}
    for release in document["releases"]:
        expected = {"release_id", "package_path", "package_sha256", "artifacts", "privacy_review",
                    "methodology_review", "owner_content_review", "cross_release_review", "review_reference"}
        if set(release) != expected or not _code(release["release_id"]) or not _code(release["review_reference"]):
            raise ValueError("Invalid release review record")
        if any(release[key] != "APPROVED" for key in ["privacy_review", "methodology_review", "owner_content_review", "cross_release_review"]):
            raise ValueError("All human review decisions are required")
        relative = release["package_path"]
        if relative != "published/releases/" + release["release_id"] + "/statistics.json":
            raise ValueError("Unapproved release package location")
        path = _within(root, relative)
        if hashlib.sha256(path.read_bytes()).hexdigest() != release["package_sha256"]:
            raise ValueError("Package changed after review")
        package = json.loads(path.read_text(encoding="utf-8"))
        validate_public_package(package)
        if package["kind"] != "REAL_AGGREGATED":
            raise ValueError("Real release manifest must not relabel a synthetic package")
        if relative in approved:
            raise ValueError("Duplicated package")
        approved[relative] = "aggregate_package"
        if not isinstance(release["artifacts"], list):
            raise ValueError("Reviewed artifact list required")
        for artifact in release["artifacts"]:
            if set(artifact) != {"path", "sha256", "type"} or artifact["type"] not in {"aggregate_figure", "results_notebook"}:
                raise ValueError("Invalid reviewed artifact")
            relative = artifact["path"]
            if not relative.startswith("published/releases/" + release["release_id"] + "/"):
                raise ValueError("Artifact outside reviewed release")
            path = _within(root, relative)
            suffixes = {"aggregate_figure": {".png", ".svg"}, "results_notebook": {".ipynb"}}
            if path.suffix not in suffixes[artifact["type"]] or relative in approved:
                raise ValueError("Unapproved artifact type or duplicate")
            if hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
                raise ValueError("Artifact changed after review")
            approved[relative] = artifact["type"]
    return approved


def load_reviewed_release(code_root, relative):
    root = Path(code_root).resolve()
    if approved_release_files(root).get(relative) != "aggregate_package":
        raise ValueError("No matching approved real release")
    return json.loads(_within(root, relative).read_text(encoding="utf-8"))


def plot_counts(package, table_id):
    validate_public_package(package)
    table = next(t for t in package["tables"] if t["table_id"] == table_id)
    import matplotlib.pyplot as plt
    fig, axis = plt.subplots()
    axis.bar([r["category_code"] for r in table["rows"]], [r["count"] for r in table["rows"]])
    axis.set(title=package["kind"] + " | " + table_id, ylabel="Report count" if table["unit"] == "REPORT" else "Event count")
    fig.tight_layout()
    return fig

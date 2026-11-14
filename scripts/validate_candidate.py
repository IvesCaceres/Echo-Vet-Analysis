"""Fail-closed publication checks for the exact candidate, without reading private data."""
from pathlib import Path
import ast
import json
import re
import sys


def validate(root):
    root = Path(root).resolve()
    issues = []
    from aggregate_release import approved_release_files
    try:
        approved = approved_release_files(root)
    except (ValueError, KeyError, TypeError, OSError):
        approved = {}
        issues.append({"path": "published/approved-manifest.json", "category": "invalid or changed release approval"})
    from editorial_release import approved_editorial_files
    try:
        editorial = approved_editorial_files(root)
        if set(editorial) & set(approved):
            raise ValueError("Duplicated release artifact")
        approved.update(editorial)
    except (ValueError, KeyError, TypeError, OSError):
        issues.append({"path": "published/editorial-manifest.json", "category": "invalid or changed exact editorial approval"})
    allowed = {".py", ".md", ".txt", ".ipynb", ".example"}
    secrets = re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----")
    files = []
    def scalar_strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, list):
            for item in value:
                yield from scalar_strings(item)
        elif isinstance(value, dict):
            for item in value.values():
                yield from scalar_strings(item)
    for p in root.rglob("*"):
        if p.is_symlink() or getattr(p.lstat(), "st_file_attributes", 0) & 1024:
            issues.append({"path": "[link withheld]", "category": "link/reparse point"})
            continue
        relative = p.relative_to(root).as_posix()
        if p.name in {".git", ".env", ".venv", "outputs", "backups", "__pycache__"}:
            issues.append({"path": relative, "category": "excluded path"})
        if not p.is_file():
            continue
        files.append(relative)
        reviewed_figure = approved.get(relative) == "aggregate_figure"
        allowed_json = relative in {"synthetic/schema.json", "published/approved-manifest.json", "published/editorial-manifest.json"} or approved.get(relative) == "aggregate_package"
        reviewed_table = approved.get(relative) == "aggregate_table"
        if p.name != ".gitignore" and not allowed_json and not reviewed_figure and not reviewed_table and p.suffix not in allowed:
            issues.append({"path": relative, "category": "unapproved file type"})
        raw = p.read_bytes()
        if raw.startswith((b"SQLite format 3\x00", b"PK\x03\x04", b"%PDF")) or (raw.startswith(b"\x89PNG") and not reviewed_figure):
            issues.append({"path": relative, "category": "database/document/binary signature"})
        if reviewed_figure and p.suffix == ".png":
            if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
                issues.append({"path": relative, "category": "invalid reviewed PNG"})
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            issues.append({"path": relative, "category": "non-text payload"})
            continue
        indicator_text = text
        if p.suffix in {".ipynb", ".json"}:
            indicator_text = "\n".join(scalar_strings(json.loads(text)))
        if secrets.search(indicator_text):
            issues.append({"path": relative, "category": "credential pattern; values withheld"})
        # A drive letter starts at a token boundary; otherwise JSON-escaped
        # Python statements such as 'Exception:\\n' produce false matches.
        if re.search(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/]", indicator_text):
            issues.append({"path": relative, "category": "absolute Windows path"})
        if reviewed_figure and p.suffix == ".svg" and re.search(r"<script|(?:href|src)\s*=\s*['\"](?:https?:|data:|file:)", text, re.I):
            issues.append({"path": relative, "category": "external or embedded SVG payload"})
        if p.suffix == ".py":
            try:
                ast.parse(text)
            except SyntaxError:
                issues.append({"path": relative, "category": "Python syntax"})
        if p.suffix == ".ipynb":
            doc = json.loads(text)
            for index, cell in enumerate(doc.get("cells", [])):
                if (cell.get("outputs") and approved.get(relative) != "results_notebook") or cell.get("attachments") or cell.get("metadata"):
                    issues.append({"path": relative, "cell": index, "category": "retained output/metadata"})
                if cell.get("cell_type") == "code" and cell.get("execution_count") is not None and approved.get(relative) != "results_notebook":
                    issues.append({"path": relative, "cell": index, "category": "execution count"})
    return {"status": "FAIL" if issues else "PASS", "files": len(files), "issues": issues,
            "scope": "Limited patterns and structural allowlist; not an anonymity or absolute-security certification"}


if __name__ == "__main__":
    result = validate(Path(__file__).resolve().parents[1])
    print(json.dumps(result))
    raise SystemExit(result["status"] != "PASS")

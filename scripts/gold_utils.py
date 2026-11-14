"""Configuration boundary for the reviewed analysis subset; no source-data defaults."""
from pathlib import Path
import hashlib
import os
import sqlite3
import tempfile

GOLD_DB_FILENAME = "gold_v2_final.db"
_SESSION = None


def find_project_root(start=None):
    """Return the code root, never search parents for clinical databases."""
    return Path(__file__).resolve().parents[1]


def _outside(path, root):
    return not path.resolve().is_relative_to(root.resolve())


def _configuration():
    global _SESSION
    mode = os.environ.get("ECHO_MODE", "PUBLIC_DEMO")
    if mode not in {"PUBLIC_DEMO", "PRIVATE_ANALYSIS"}:
        raise ValueError("Unsupported ECHO_MODE")
    if _SESSION is not None:
        if _SESSION[0] != mode:
            raise RuntimeError("Restart the process before switching modes")
        return _SESSION
    if mode == "PUBLIC_DEMO":
        from generate_synthetic import generate
        root = Path(tempfile.mkdtemp(prefix="echo_synthetic_"))
        database = generate(root)
        output = root / "synthetic_outputs"
    else:
        configured = os.environ.get("ECHO_GOLD_DB", "")
        outputs = os.environ.get("ECHO_OUTPUT_ROOT", "")
        expected = os.environ.get("ECHO_EXPECTED_GOLD_SHA256", "")
        if not configured or not outputs or len(expected) != 64:
            raise ValueError("PRIVATE_ANALYSIS requires database, output root and snapshot SHA-256")
        database = Path(configured)
        output = Path(outputs)
        if not database.is_absolute() or not output.is_absolute():
            raise ValueError("Private paths must be absolute")
        database = database.resolve(strict=True)
        output = output.resolve()
        code = find_project_root()
        if not _outside(database, code) or not _outside(output, code):
            raise ValueError("Private inputs and outputs must be outside the code checkout")
        if not _outside(output, database.parent):
            raise ValueError("Output root must be outside the input snapshot directory")
        if any(Path(str(database) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
            raise ValueError("Use an approved consistent snapshot, not an active database")
        with database.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual.casefold() != expected.casefold():
            raise ValueError("Configured snapshot identity mismatch; values withheld")
    output.mkdir(parents=True, exist_ok=True)
    _SESSION = mode, database, output
    return _SESSION


def get_gold_db_path(project_root=None, filename=None):
    if filename is not None and Path(filename).name != GOLD_DB_FILENAME:
        raise ValueError("Unexpected database filename")
    return _configuration()[1]


def get_output_root():
    return _configuration()[2]


def validate_gold_identity(db_path):
    expected_path = get_gold_db_path()
    if Path(db_path).resolve() != expected_path.resolve():
        raise ValueError("Database is outside the configured session")
    with expected_path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def connect_gold_readonly(db_path):
    path = Path(db_path).resolve(strict=True)
    if path != get_gold_db_path().resolve():
        raise ValueError("Refusing a database outside the configured session")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    return connection


def quote_identifier(identifier):
    return '"' + str(identifier).replace('"', '""') + '"'

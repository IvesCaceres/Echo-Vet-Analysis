"""Smoke test: extracción sobre un .docx 7×7 (formato moderno, 2025/2026)."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from informes_vet import extract  # noqa: E402


def _pick() -> Path | None:
    for year in ("Ecografía 2026", "Ecografía 2025"):
        base = ROOT / year
        if not base.exists():
            continue
        matches = sorted(p for p in base.rglob("*.docx") if not p.name.startswith("~$") and not p.name.startswith("._"))
        if matches:
            return matches[0]
    return None


class Test7x7(unittest.TestCase):
    def test_modern(self):
        path = _pick()
        if path is None:
            self.skipTest("No hay .docx en Ecografía 2025/2026/")
        rec = extract.parse_docx(path)
        self.assertEqual(len(rec["sha256"]), 64)
        self.assertIn(rec["estudio"], ("Abdominal", "Gestacional"))
        pj = json.loads(rec["paciente_json"])
        for forbidden in ("Nombre", "Especie", "Raza", "Edad", "Peso", "Tutor", "Fecha"):
            for k, v in pj.items():
                if v is None:
                    continue
                self.assertFalse(
                    v.strip().lower() == forbidden.lower(),
                    f"campo {k} sin parsear: '{v}' (parece label)",
                )


if __name__ == "__main__":
    unittest.main()

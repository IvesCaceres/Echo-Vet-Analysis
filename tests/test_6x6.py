"""Smoke test: extracción sobre un .docx 6×6 (formato antiguo, 2022).

El formato legacy tiene celdas únicas con 'Label: Value' tras dedupe. Este
test verifica que el parser las extrae correctamente.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from informes_vet import extract  # noqa: E402


CANDIDATES = [
    ROOT / "Ecografía 2022" / "Tonka, Particular.docx",
    ROOT / "Ecografía 2022" / "Diciembre 2022" / "Tonka, Particular.docx",
]


def _pick() -> Path | None:
    for c in CANDIDATES:
        if c.exists():
            return c
    matches = list((ROOT / "Ecografía 2022").rglob("*.docx"))
    return matches[0] if matches else None


class Test6x6(unittest.TestCase):
    def test_tonka(self):
        path = _pick()
        if path is None:
            self.skipTest("No hay .docx en Ecografía 2022/")
        rec = extract.parse_docx(path)
        self.assertIn("sha256", rec)
        self.assertEqual(len(rec["sha256"]), 64)
        self.assertIn(rec["estudio"], ("Abdominal", "Gestacional"))
        self.assertTrue(len(rec["hallazgos"]) >= 0)
        pj = json.loads(rec["paciente_json"])
        self.assertIn("nombre", pj)
        self.assertIn("especie", pj)
        # Legacy: celda única con 'Label: Value' debe extraerse.
        self.assertIsNotNone(
            pj.get("fecha"),
            "fecha no extraída del formato legacy",
        )
        self.assertIsNotNone(
            pj.get("antecedentes"),
            "antecedentes no extraídos del formato legacy",
        )
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

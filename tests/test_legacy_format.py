"""Tests para el formato legacy (A): celda única con "Label: Value".

El formato legacy surge cuando los DOCX usan tablas 6×6 o 7×7 con merges
horizontales completos: cada celda de la fila contiene "Label: Value" y la fila
se duplica N veces. Tras `_dedupe_row_cells` queda una sola celda, por lo que
el parser moderno (pares adyacentes) no puede extraer.

`_extract_from_table` debe aplicar un fallback que parte la celda en el primer
':' y matchea el prefijo contra `FIELD_LABELS`.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from informes_vet import extract  # noqa: E402

LEGACY_2022 = ROOT / "Ecografía 2022" / "Tonka, Particular.docx"
LEGACY_2024 = (
    ROOT / "Ecografía 2024" / "9. Septiembre 2024" / "Antu, Haustiere" / "Antu, Haustiere.docx"
)
LEGACY_2026 = (
    ROOT / "Ecografía 2026" / "4. Abril 2026" / "Arenita, Emergencias" / "Arenita, Emergencias.docx"
)


def _any_legacy() -> Path | None:
    for c in (LEGACY_2022, LEGACY_2024, LEGACY_2026):
        if c.exists():
            return c
    return None


class TestLegacyFormat(unittest.TestCase):
    def test_legacy_2022_extrae_fecha(self):
        if not LEGACY_2022.exists():
            self.skipTest("Falta Tonka 2022")
        rec = extract.parse_docx(LEGACY_2022)
        self.assertIsNotNone(
            rec["fecha"],
            f"fecha no extraída del formato legacy; rec.fecha={rec['fecha']!r}",
        )
        self.assertIn("2023", rec["fecha"])
        self.assertIn("noviembre", rec["fecha"].lower())

    def test_legacy_2022_extrae_antecedentes(self):
        if not LEGACY_2022.exists():
            self.skipTest("Falta Tonka 2022")
        rec = extract.parse_docx(LEGACY_2022)
        self.assertIsNotNone(rec["antecedentes"])
        self.assertIn("vulva", rec["antecedentes"].lower())

    def test_legacy_2022_paciente_json_contiene_fecha_y_antecd(self):
        if not LEGACY_2022.exists():
            self.skipTest("Falta Tonka 2022")
        rec = extract.parse_docx(LEGACY_2022)
        pj = json.loads(rec["paciente_json"])
        self.assertIn("fecha", pj)
        self.assertIn("antecedentes", pj)
        self.assertTrue(pj["fecha"], "paciente_json.fecha vacío")
        self.assertTrue(pj["antecedentes"], "paciente_json.antecedentes vacío")

    def test_legacy_2024_extrae_ambos(self):
        if not LEGACY_2024.exists():
            self.skipTest("Falta Antu 2024")
        rec = extract.parse_docx(LEGACY_2024)
        self.assertIsNotNone(rec["fecha"])
        self.assertIsNotNone(rec["antecedentes"])
        self.assertIn("septiembre", rec["fecha"].lower())
        self.assertIn("sedimento", rec["antecedentes"].lower())

    def test_legacy_2026_aun_en_formato_viejo(self):
        if not LEGACY_2026.exists():
            self.skipTest("Falta Arenita 2026")
        rec = extract.parse_docx(LEGACY_2026)
        self.assertIsNotNone(rec["fecha"])
        self.assertIsNotNone(rec["antecedentes"])

    def test_legacy_no_pisa_campos_modernos(self):
        """El fallback sólo debe activar cuando el formato moderno no extrajo."""
        if not LEGACY_2022.exists():
            self.skipTest("Falta Tonka 2022")
        rec = extract.parse_docx(LEGACY_2022)
        # nombre/especie/raza/edad/etc ya vienen del formato moderno en celdas
        # adyacentes; no deben ser pisados por el fallback legacy.
        self.assertEqual(rec["nombre"], "Tonka")
        self.assertEqual(rec["especie"], "Canino")
        self.assertEqual(rec["raza"], "Terranova")

    def test_legacy_sobre_cualquier_archivo_pre_2026(self):
        """Cualquier DOCX del corpus pre-2026 debe extraer al menos fecha."""
        path = _any_legacy()
        if path is None:
            self.skipTest("Sin archivos legacy disponibles")
        rec = extract.parse_docx(path)
        self.assertIsNotNone(
            rec["fecha"],
            f"Formato legacy sin fecha extraída en {path.name}: {rec['fecha']!r}",
        )
        self.assertIsNotNone(rec["antecedentes"])


if __name__ == "__main__":
    unittest.main()
"""Smoke test: caso gestacional (sin órganos canónicos, fallback a 'Gestación')."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from informes_vet import extract  # noqa: E402

GESTACIONAL = ROOT / "Ecografía 2022" / "Sasha, Posta los Alerces.docx"


class TestGestacional(unittest.TestCase):
    def test_gestacion(self):
        if not GESTACIONAL.exists():
            self.skipTest(f"No se encontró {GESTACIONAL.name}")
        rec = extract.parse_docx(GESTACIONAL)
        self.assertEqual(rec["estudio"], "Gestacional")
        self.assertTrue(
            len(rec["hallazgos"]) >= 1,
            "Se esperaba al menos un hallazgo (gestacional).",
        )
        organos = {h["organo"] for h in rec["hallazgos"]}
        self.assertIn("Gestación", organos)
        for h in rec["hallazgos"]:
            self.assertIn("hallazgo_hash", h)
            self.assertEqual(len(h["hallazgo_hash"]), 64)


if __name__ == "__main__":
    unittest.main()

"""Walk de carpetas + filtros de basura + apertura segura de .docx."""

import re
from pathlib import Path

JUNK_SUFFIXES = {".pdf", ".avi", ".mp4", ".mov", ".jpg", ".jpeg", ".png"}

# Denylist explícita de archivos a excluir de toda ingesta. Cada elemento es
# una subruta POSIX relativa a la raíz del proyecto (tal como aparece en
# `ruta_relativa` en BD). Mantener corta y con justificación documentada.
#
# Origen: purga 2026-06-17. Estos 3 informes (IDs 459, 477, 909 en BD previa)
# NO son estudios abdominales/gestacionales; son estudios de masa/musculatura
# que no corresponden al alcance del pipeline. El archivo del ID 477 ya fue
# movido al directorio _purgatorio/; los otros 2 permanecen en disco pero
# bloqueados por lock de Windows, por lo que se excluyen por denylist.
DENYLIST: tuple[str, ...] = (
    "Ecografía 2023/0.3 Marzo 2023/Mike, Rucalaf/Mike, Rucalaf.docx",
    "Ecografía 2024/4. Abril 2024/Olga, Rucalaf/Olga, Rucalaf.docx",
)


def is_denylisted(path: Path, root: Path) -> bool:
    """True si la ruta del archivo está en la DENYLIST explícita."""
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return False
    return rel in DENYLIST


def is_junk(path: Path) -> bool:
    """Filtra lock files de Word, AppleDouble de macOS, .DS_Store, y archivos no-docx."""
    name = path.name
    if name.startswith("~$"):
        return True
    if name.startswith("._"):
        return True
    if name == ".DS_Store":
        return True
    if path.suffix.lower() != ".docx":
        return True
    return False


def is_year_folder(path: Path) -> bool:
    """Detecta carpetas del tipo `Ecografía 2024`."""
    m = re.match(r"^Ecograf[ií]a\s+(\d{4})$", path.name)
    return m is not None


def year_from_folder(path: Path) -> int | None:
    m = re.match(r"^Ecograf[ií]a\s+(\d{4})$", path.name)
    return int(m.group(1)) if m else None


def iter_docx(root: Path, year_filter: list[int] | None = None) -> list[Path]:
    """Recorre root y devuelve todos los .docx válidos dentro de Ecografía YYYY/.

    Los archivos basura (~$*, ._*, .DS_Store, *.pdf) y los denylistados se
    filtran aquí. `year_filter` permite restringir a años específicos.
    """
    root = Path(root)
    results: list[Path] = []
    if not root.exists():
        return results
    for year_dir in sorted(root.iterdir()):
        if not year_dir.is_dir() or not is_year_folder(year_dir):
            continue
        y = year_from_folder(year_dir)
        if year_filter and y not in year_filter:
            continue
        for path in year_dir.rglob("*.docx"):
            if is_junk(path):
                continue
            if is_denylisted(path, root):
                continue
            results.append(path)
    return results

"""Verificación end-to-end de Fase 2.

Adjunta la BD RAW para poder cruzar datos y validar cobertura, idempotencia y
excepciones.
"""
import sqlite3

silver = sqlite3.connect("silver.db")
silver.execute("ATTACH DATABASE 'informes.db' AS raw")
sc = silver.cursor()
rc = silver.cursor()

print("=" * 70)
print("F2 — Verificación de Fase 2")
print("=" * 70)

# 1. Cobertura >99% por dimensión
print("\n## Cobertura por dimensión (map_*.dim_*_id NOT NULL)\n")
for tabla, col in [
    ("map_especie", "dim_especie_id"),
    ("map_sexo", "dim_sexo_id"),
    ("map_estudio", "dim_estudio_id"),
]:
    total, ok = sc.execute(
        f"SELECT COUNT(*), SUM(CASE WHEN {col} IS NOT NULL THEN 1 ELSE 0 END) "
        f"FROM {tabla}"
    ).fetchone()
    pct = 100.0 * ok / total if total else 0
    status = "✅" if pct > 99 else "❌"
    print(f"  {tabla}.{col}: {ok} / {total}  ({pct:.2f}%) {status}")

# 2. Reporte de razas no mapeadas
print("\n## Razas no auto-aprobadas (map_raza.estado_revision='pendiente')\n")
n_pend, = sc.execute(
    "SELECT COUNT(*) FROM map_raza WHERE estado_revision = 'pendiente'"
).fetchone()
n_aprob, = sc.execute(
    "SELECT COUNT(*) FROM map_raza WHERE estado_revision = 'aprobada'"
).fetchone()
print(f"  aprobadas: {n_aprob}")
print(f"  pendientes: {n_pend}")
print(f"  total: {n_aprob + n_pend}")

print("\n  Top 20 pendientes por frecuencia:")
for r in sc.execute(
    "SELECT valor_original, frecuencia FROM map_raza "
    "WHERE estado_revision = 'pendiente' ORDER BY frecuencia DESC LIMIT 20"
).fetchall():
    print(f"    {r[0]!r:40}  freq={r[1]}")

# 3. stg_valores_no_mapeados (especie/sexo/estudio)
print("\n## stg_valores_no_mapeados (dimensiones especie/sexo/estudio)\n")
for r in sc.execute(
    "SELECT dimension, valor_original, frecuencia, propuesta_canonica, observaciones "
    "FROM stg_valores_no_mapeados ORDER BY dimension, frecuencia DESC"
).fetchall():
    print(f"  [{r[0]}] {r[1]!r:30} freq={r[2]:3} prop={r[3]!r:25} | {r[4]}")

# 4. Valores conflictivos: misma valor_original mapeando a cosas distintas
# (imposible por la UNIQUE constraint, pero verificamos que no haya duplicados
# en valor_original dentro de cada map_*)
print("\n## Valores conflictivos (duplicados en valor_original)\n")
for tabla in ["map_especie", "map_sexo", "map_estudio", "map_raza"]:
    n_dup, = sc.execute(
        f"SELECT COUNT(*) FROM (SELECT valor_original FROM {tabla} "
        f"GROUP BY valor_original HAVING COUNT(*) > 1)"
    ).fetchone()
    status = "✅" if n_dup == 0 else "❌"
    print(f"  {tabla}: {n_dup} duplicados {status}")

# 5. Valores RAW no presentes en map_*
print("\n## Valores RAW sin entrada en map_*\n")
for tabla_map, col_raw, dim_table, dim_col in [
    ("map_especie", "especie", "dim_especie", "nombre_canonico"),
    ("map_sexo", "genero", "dim_sexo", "nombre_canonico"),
    ("map_estudio", "estudio", "dim_estudio", "nombre_canonico"),
    ("map_raza", "raza", "dim_raza", "nombre_canonico"),
]:
    n_raw = rc.execute(
        f"SELECT COUNT(DISTINCT {col_raw}) FROM raw.informes "
        f"WHERE {col_raw} IS NOT NULL AND {col_raw} != ''"
    ).fetchone()[0]
    n_map = sc.execute(f"SELECT COUNT(*) FROM {tabla_map}").fetchone()[0]
    diff = n_raw - n_map
    status = "✅" if diff <= 0 else "⚠️"
    print(f"  {col_raw} RAW distintos: {n_raw}  |  en {tabla_map}: {n_map}  "
          f"| diff: {diff} {status}")

# 6. Idempotencia: re-correr F2 produce misma Silver
print("\n## Idempotencia (re-run F2 produce misma Silver)\n")
import subprocess
result = subprocess.run(
    ["python", "scripts/build_silver.py", "--phase", "f2", "--root", "."],
    capture_output=True, text=True,
    env={"PYTHONIOENCODING": "utf-8",
         "PATH": "/c/Python:/c/Python/Scripts",
         "SYSTEMROOT": "C:\\Windows"},
)
# Buscar la línea de cobertura
for line in result.stdout.split("\n"):
    if "map_" in line and "dim_" in line and "100.0%" in line:
        print(f"  {line.strip()}")
    if "OK en" in line:
        print(f"  {line.strip()}")

# Conteos antes y después del re-run
print("\nConteos después del re-run:")
for tabla in ["map_especie", "map_sexo", "map_estudio", "map_raza",
              "dim_raza", "stg_valores_no_mapeados", "stg_razas_detectadas"]:
    n = sc.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    print(f"  {tabla}: {n}")

# 7. silver_etl_runs historial
print("\n## silver_etl_runs (F2 runs)\n")
for r in sc.execute(
    "SELECT id, phase, status, rows_read, rows_written, duration_ms, "
    "datetime(started_at), actor FROM silver_etl_runs WHERE phase='f2' ORDER BY id"
).fetchall():
    print(f"  id={r[0]} phase={r[1]} status={r[2]} read={r[3]} "
          f"written={r[4]} dur={r[5]}ms at={r[6]} actor={r[7]}")

silver.close()
print("\n" + "=" * 70)
print("Verificación completada")
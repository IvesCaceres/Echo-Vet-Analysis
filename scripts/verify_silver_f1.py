"""Verificación end-to-end de Fase 1.

Adjunta la BD RAW para validar FKs lógicas cross-DB sin duplicar engines.
"""
import sqlite3

silver = sqlite3.connect("silver.db")
silver.execute("ATTACH DATABASE 'informes.db' AS raw")
sc = silver.cursor()

print("=== Cobertura ===")
n_sil = sc.execute("SELECT COUNT(*) FROM silver_informes").fetchone()[0]
n_raw = sc.execute("SELECT COUNT(*) FROM raw.informes").fetchone()[0]
print(f"  silver_informes: {n_sil}")
print(f"  raw.informes:    {n_raw}")
assert n_sil == n_raw, "Cobertura no es 100%"
print("  ✅ 100% cobertura")

print()
print("=== FK cross-DB silver_informes.informe_id -> raw.informes.id ===")
n_match = sc.execute(
    "SELECT COUNT(*) FROM silver_informes si "
    "WHERE EXISTS (SELECT 1 FROM raw.informes r WHERE r.id = si.informe_id)"
).fetchone()[0]
n_orphan = n_sil - n_match
print(f"  válidos: {n_match}  huérfanos: {n_orphan}")
assert n_orphan == 0, "Hay FKs huérfanas"
print("  ✅ 0 huérfanos")

print()
print("=== Dims base (deben tener seeds esperados) ===")
expected = {
    "dim_organo": 16,
    "dim_especie": 9,
    "dim_sexo": 3,
    "dim_estado_reproductivo": 4,
    "dim_estudio": 8,
    "dim_edad_categoria": 5,
}
for tbl, expected_count in expected.items():
    n = sc.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    status = "✅" if n == expected_count else "❌"
    print(f"  {tbl}: {n} (esperado {expected_count}) {status}")

print()
print("=== Idempotencia (silver_etl_runs) ===")
runs = sc.execute(
    "SELECT id, phase, status, rows_read, rows_written, duration_ms, "
    "datetime(started_at), actor FROM silver_etl_runs ORDER BY id"
).fetchall()
for r in runs:
    print(f"  id={r[0]} phase={r[1]} status={r[2]} read={r[3]} "
          f"written={r[4]} dur={r[5]}ms at={r[6]} actor={r[7]}")
ok_runs = [r for r in runs if r[2] == "ok"]
assert ok_runs, "No hay runs exitosos"
print(f"  ✅ {len(ok_runs)} ejecuciones exitosas registradas")

print()
print("=== Distribución de dim_estudio ===")
for r in sc.execute(
    "SELECT e.nombre_canonico, COUNT(*) FROM silver_informes si "
    "JOIN dim_estudio e ON e.id = si.dim_estudio_id "
    "GROUP BY e.nombre_canonico ORDER BY 2 DESC"
).fetchall():
    print(f"  {r[0]}: {r[1]}")

print()
print("=== Distribución de dim_edad_categoria ===")
for r in sc.execute(
    "SELECT ec.nombre, COUNT(*) FROM silver_informes si "
    "LEFT JOIN dim_edad_categoria ec ON ec.id = si.dim_edad_categoria_id "
    "GROUP BY ec.nombre ORDER BY 2 DESC"
).fetchall():
    print(f"  {r[0]}: {r[1]}")

print()
print("=== Distribución de dim_especie ===")
for r in sc.execute(
    "SELECT e.nombre_canonico, COUNT(*) FROM silver_informes si "
    "LEFT JOIN dim_especie e ON e.id = si.dim_especie_id "
    "GROUP BY e.nombre_canonico ORDER BY 2 DESC"
).fetchall():
    print(f"  {r[0]}: {r[1]}")

print()
print("=== Distribución de dim_estado_reproductivo ===")
for r in sc.execute(
    "SELECT er.nombre_canonico, COUNT(*) FROM silver_informes si "
    "JOIN dim_estado_reproductivo er ON er.id = si.dim_estado_reproductivo_id "
    "GROUP BY er.nombre_canonico ORDER BY 2 DESC"
).fetchall():
    print(f"  {r[0]}: {r[1]}")

print()
print("=== Distribución de dim_sexo ===")
for r in sc.execute(
    "SELECT s.nombre_canonico, COUNT(*) FROM silver_informes si "
    "JOIN dim_sexo s ON s.id = si.dim_sexo_id GROUP BY s.nombre_canonico "
    "ORDER BY 2 DESC"
).fetchall():
    print(f"  {r[0]}: {r[1]}")

print()
print("=== Cobertura fecha_parseada ===")
r = sc.execute(
    "SELECT COUNT(*), "
    "SUM(CASE WHEN fecha_parseada IS NOT NULL THEN 1 ELSE 0 END), "
    "ROUND(100.0 * SUM(CASE WHEN fecha_parseada IS NOT NULL THEN 1 ELSE 0 END) "
    "/ COUNT(*), 1) FROM silver_informes"
).fetchone()
print(f"  total={r[0]}  con_fecha={r[1]}  cobertura={r[2]}%")

print()
print("=== Causas de dim_especie_id NULL (debe ser ruido esperado) ===")
for r in sc.execute(
    "SELECT si.informe_id, ri.especie, ri.edad FROM silver_informes si "
    "JOIN raw.informes ri ON ri.id = si.informe_id "
    "WHERE si.dim_especie_id IS NULL ORDER BY si.informe_id"
).fetchall():
    print(f"  silver_id={r[0]:5}  raw.especie={r[1]!r:25}  raw.edad={r[2]!r}")

print()
print("=== Causas de dim_edad_categoria_id NULL (debe ser ruido esperado) ===")
for r in sc.execute(
    "SELECT si.informe_id, ri.edad FROM silver_informes si "
    "JOIN raw.informes ri ON ri.id = si.informe_id "
    "WHERE si.dim_edad_categoria_id IS NULL ORDER BY si.informe_id"
).fetchall():
    print(f"  silver_id={r[0]:5}  raw.edad={r[1]!r}")

silver.close()
print()
print("=" * 60)
print("✅ FASE 1 VERIFICADA — todas las aserciones pasaron")
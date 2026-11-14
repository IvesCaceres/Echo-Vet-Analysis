# Adapted analytical code; default PUBLIC_DEMO. No clinical results included.
from pathlib import Path
import sys
CODE_ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "scripts" / "gold_utils.py").is_file() and (p / "synthetic" / "schema.json").is_file())
sys.path.insert(0, str(CODE_ROOT / "scripts"))
from gold_utils import find_project_root, get_output_root


from pathlib import Path
import sys
import sqlite3
import pandas as pd
import numpy as np

def _find_root(start):
    return find_project_root()
PROJECT_ROOT = _find_root(Path.cwd())
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from gold_utils import connect_gold_readonly, get_gold_db_path, quote_identifier, validate_gold_identity
DB_PATH = get_gold_db_path(PROJECT_ROOT)
sha_pre = validate_gold_identity(DB_PATH)
print('ACTIVE GOLD: gold_v2_final.db')
print(f'Raíz del proyecto: {PROJECT_ROOT}')
print(f'Ruta absoluta de Gold V2: {DB_PATH}')
print(f'Existe: {DB_PATH.exists()}')
if not DB_PATH.exists():
    raise FileNotFoundError(f'No se encontró Gold V2 en {DB_PATH}')
print(f'Tamaño: {DB_PATH.stat().st_size / 1024 ** 2:.2f} MB')


conn = connect_gold_readonly(DB_PATH)
print('Conexión SQLite abierta exclusivamente con mode=ro.')
print('Solo se ejecutarán consultas SELECT y PRAGMA de lectura.')


sqlite_version = conn.execute('SELECT sqlite_version()').fetchone()[0]
database_list = pd.read_sql_query('PRAGMA database_list', conn)
quick_check = conn.execute('PRAGMA quick_check').fetchone()[0]
print(f'Versión SQLite: {sqlite_version}')
display(database_list)
print(f'PRAGMA quick_check: {quick_check}')
print(f'Tamaño aproximado: {DB_PATH.stat().st_size / 1024 ** 2:.2f} MB')


objects = pd.read_sql_query("\n    SELECT type, name, tbl_name, sql\n    FROM sqlite_master\n    WHERE name NOT LIKE 'sqlite_%'\n    ORDER BY type, name\n", conn)
tables = objects.loc[objects.type.eq('table'), 'name'].tolist()
views = objects.loc[objects.type.eq('view'), 'name'].tolist()
indexes = objects.loc[objects.type.eq('index'), ['name', 'tbl_name']].copy()
print('Tablas:')
display(objects[objects.type.eq('table')][['name', 'sql']].reset_index(drop=True))
print('Vistas:')
display(objects[objects.type.eq('view')][['name', 'sql']].reset_index(drop=True))
print('Índices relevantes:')
display(indexes.reset_index(drop=True))


row_counts = []
for table in tables:
    qtable = quote_identifier(table)
    row_counts.append({'nombre_tabla': table, 'n_filas': conn.execute(f'SELECT COUNT(*) FROM {qtable}').fetchone()[0]})
row_counts_df = pd.DataFrame(row_counts).sort_values('n_filas', ascending=False, ignore_index=True)
display(row_counts_df)


schemas = {}
for table in tables:
    info = pd.read_sql_query(f'PRAGMA table_info({quote_identifier(table)})', conn)
    info = info.rename(columns={'name': 'nombre_columna', 'type': 'tipo_declarado', 'notnull': 'no_nulo', 'dflt_value': 'default', 'cid': 'posicion', 'pk': 'primary_key'})
    info['nullable'] = np.where(info['no_nulo'].eq(1), 'NO', 'YES')
    schemas[table] = info[['nombre_columna', 'tipo_declarado', 'nullable', 'default', 'posicion', 'primary_key']]
    print(f'## {table}')
    display(schemas[table])


foreign_keys = {}
index_details = {}
for table in tables:
    qtable = quote_identifier(table)
    fk = pd.read_sql_query(f'PRAGMA foreign_key_list({qtable})', conn)
    il = pd.read_sql_query(f'PRAGMA index_list({qtable})', conn)
    details = []
    for index_name in il['name'].tolist() if not il.empty else []:
        ii = pd.read_sql_query(f'PRAGMA index_info({quote_identifier(index_name)})', conn)
        details.append({'index_name': index_name, 'columns': ii['name'].tolist()})
    foreign_keys[table] = fk
    index_details[table] = details
    print(f'## {table} — foreign keys')
    display(fk if not fk.empty else pd.DataFrame({'status': ['none']}))
    print(f'## {table} — indexes')
    display(pd.DataFrame(details) if details else pd.DataFrame({'status': ['none']}))


for table in tables:
    print(f'## Muestra: {table}')
    sample = pd.read_sql_query(f'SELECT * FROM {quote_identifier(table)} LIMIT 5', conn)
    display(sample.head(5))


profile_rows = []
row_count_map = dict(zip(row_counts_df['nombre_tabla'], row_counts_df['n_filas']))
for table in tables:
    qtable = quote_identifier(table)
    for column in schemas[table]['nombre_columna']:
        qcolumn = quote_identifier(column)
        row_count = row_count_map[table]
        non_null = conn.execute(f'SELECT COUNT({qcolumn}) FROM {qtable}').fetchone()[0]
        distinct = conn.execute(f'SELECT COUNT(DISTINCT {qcolumn}) FROM {qtable}').fetchone()[0]
        profile_rows.append({'table': table, 'column': column, 'sqlite_type': schemas[table].loc[schemas[table].nombre_columna.eq(column), 'tipo_declarado'].iloc[0], 'row_count': row_count, 'non_null_count': non_null, 'null_count': row_count - non_null, 'null_pct': (row_count - non_null) / row_count * 100 if row_count else np.nan, 'distinct_count': distinct})
profile_df = pd.DataFrame(profile_rows)
display(profile_df)


pk_rows = []
for table, schema in schemas.items():
    for _, row in schema[schema.primary_key.astype(int).gt(0)].iterrows():
        pk_rows.append({'table': table, 'column': row.nombre_columna, 'position': row.posicion})
pk_df = pd.DataFrame(pk_rows)
id_df = profile_df[profile_df.column.str.lower().eq('id') | profile_df.column.str.lower().str.endswith('_id')].copy()
unique_df = profile_df[(profile_df.non_null_count > 0) & profile_df.distinct_count.eq(profile_df.non_null_count)].copy()
print('Primary keys declaradas:')
display(pk_df if not pk_df.empty else pd.DataFrame({'status': ['none']}))
print('Columnas id / *_id:')
display(id_df[['table', 'column', 'sqlite_type', 'non_null_count', 'distinct_count']])
print('Unicidad aparente entre valores no nulos:')
display(unique_df[['table', 'column', 'non_null_count', 'distinct_count']])


keywords = ['fecha', 'date', 'edad', 'age', 'genero', 'género', 'sexo', 'sex', 'raza', 'breed', 'especie', 'species', 'diagnostico', 'diagnóstico', 'diagnosis', 'hallazgo', 'finding', 'organ', 'status', 'strength', 'outcome', 'study', 'study_type', 'concept']
matches = []
for _, row in profile_df.iterrows():
    column_lower = str(row.column).lower()
    for keyword in keywords:
        if keyword in column_lower:
            matches.append({'table': row.table, 'column': row.column, 'sqlite_type': row.sqlite_type, 'matched_keyword': keyword})
            break
analytical_df = pd.DataFrame(matches).drop_duplicates().reset_index(drop=True)
display(analytical_df if not analytical_df.empty else pd.DataFrame({'status': ['no matches']}))


largest_tables = row_counts_df.head(5)
largest_nulls = profile_df.sort_values('null_pct', ascending=False).head(10)
structural_issues = []
if not views:
    structural_issues.append('No hay vistas de usuario.')
if pk_df.empty:
    structural_issues.append('No se detectaron primary keys declaradas.')
if profile_df.null_pct.max() > 50:
    structural_issues.append('Hay columnas con más de 50% de NULL; revisar en data quality.')
if not profile_df.empty and profile_df.row_count.eq(0).any():
    structural_issues.append('Hay tablas vacías.')
print(f'Tablas: {len(tables)}')
print(f'Filas totales sumadas: {int(row_counts_df.n_filas.sum())}')
print(f'Columnas totales: {len(profile_df)}')
print('Tablas más grandes:')
display(largest_tables)
print('Columnas con mayor porcentaje de NULL:')
display(largest_nulls[['table', 'column', 'null_pct']])
print('Posibles claves principales:')
display(pk_df if not pk_df.empty else pd.DataFrame({'status': ['none']}))
print('Variables analíticas encontradas:')
display(analytical_df)
print('Problemas estructurales evidentes:')
for issue in structural_issues or ['No se observaron problemas estructurales evidentes en este inventario.']:
    print(f'- {issue}')
sha_post = validate_gold_identity(DB_PATH)
assert sha_post == sha_pre, 'Gold SHA changed during inventory.'
print(f'SHA PRE: {sha_pre}')
print(f'SHA POST: {sha_post}')
conn.close()
print('Conexión cerrada.')


"""Exact-file editorial allowlist. Administrative review record, not a signature.

This supports local candidate approval only; it never authorizes a remote action.
Clinical inputs are neither located nor opened here.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import math
import re

PREFIX = 'published/editorial/'
TYPES = {
    PREFIX+'tables/corpus_volume.csv':'aggregate_table',
    PREFIX+'tables/species.csv':'aggregate_table',
    PREFIX+'tables/sex.csv':'aggregate_table',
    PREFIX+'tables/field_coverage.csv':'aggregate_table',
    PREFIX+'figures/species.png':'aggregate_figure',
    PREFIX+'figures/sex.png':'aggregate_figure',
    PREFIX+'results.md':'aggregate_text',
}

def integer(value):
    if not isinstance(value,str) or not re.fullmatch(r'0|[1-9][0-9]*',value):
        raise ValueError('Nonnegative integer required')
    return int(value)

def positive_support(count, total):
    if count > total or (0 < count < 10) or (0 < total-count < 10):
        raise ValueError('Small cell/complement or invalid count')

def read_rows(path, fields):
    reader=csv.DictReader(io.StringIO(path.read_text(encoding='utf-8'),newline=''))
    if reader.fieldnames!=fields:raise ValueError('Unreviewed CSV fields')
    rows=list(reader)
    if not rows or any(set(row)!=set(fields) or None in row.values() for row in rows):
        raise ValueError('Malformed aggregate table')
    return rows

def validate_editorial_tables(root):
    folder=root/PREFIX/'tables'
    volume=read_rows(folder/'corpus_volume.csv',['metric','count','unit','denominator'])
    expected=[('Gold report records','Gold record'),('Extraction events','Event row')]
    if len(volume)!=2:raise ValueError('Unreviewed volume rows')
    for row,(metric,unit) in zip(volume,expected):
        if row['metric']!=metric or row['unit']!=unit or row['denominator']!='Not applicable: snapshot count':
            raise ValueError('Unreviewed volume labels')
        if integer(row['count'])<10:raise ValueError('Small corpus')
    total=integer(volume[0]['count'])
    labels={
      'species':[('Canine','Canina'),('Feline','Felina'),('Unresolved species','Especie no resuelta'),('Missing species','Especie ausente')],
      'sex':[('Male','Macho'),('Female','Hembra'),('Not specified','No especificado'),('Blank or null','Vacío o nulo')]}
    distributions={}
    for name,expected_labels in labels.items():
        rows=read_rows(folder/(name+'.csv'),['category_en','category_es','count','denominator_records','percentage'])
        if len(rows)!=4:raise ValueError('Missing predeclared category')
        counts=[]
        for row,(en,es) in zip(rows,expected_labels):
            if (row['category_en'],row['category_es'])!=(en,es):raise ValueError('Unreviewed labels')
            count=integer(row['count']);positive_support(count,total)
            percentage=float(row['percentage'])
            if integer(row['denominator_records'])!=total or not math.isfinite(percentage) or percentage!=round(100*count/total,1):
                raise ValueError('Wrong denominator or percentage')
            counts.append(count)
        if sum(counts)!=total:raise ValueError('Partition does not sum to corpus')
        distributions[name]=counts
    coverage=read_rows(folder/'field_coverage.csv',['field','records_with_nonblank_value','records_null_or_blank','denominator_records','nonblank_percentage'])
    fields=['species','sex','breed','study_type','outcome']
    if [r['field'] for r in coverage]!=fields:raise ValueError('Unreviewed field or retained age/time')
    for row in coverage:
        yes=integer(row['records_with_nonblank_value']);no=integer(row['records_null_or_blank'])
        positive_support(yes,total)
        if yes+no!=total or integer(row['denominator_records'])!=total or float(row['nonblank_percentage'])!=round(100*yes/total,1):
            raise ValueError('Invalid field coverage')
        if row['field'] in distributions and no!=distributions[row['field']][-1]:
            raise ValueError('Coverage disagrees with distribution')

def approved_editorial_files(root):
    root=Path(root).resolve()
    manifest=root/'published/editorial-manifest.json'
    if not manifest.exists():return {}
    doc=json.loads(manifest.read_text(encoding='utf-8'))
    if set(doc)!={'schema_version','release_id','kind','owner_decision','permission_basis','publication_authorized','files'}:
        raise ValueError('Unreviewed editorial manifest fields')
    if doc['schema_version']!=1 or doc['kind']!='REAL_AGGREGATED' or not re.fullmatch('[A-Z][A-Z0-9_]{0,63}',doc['release_id']):
        raise ValueError('Invalid editorial release')
    if doc['owner_decision']!='APPROVED_FOR_LOCAL_CANDIDATE' or doc['permission_basis']!='OWNER_CONFIRMED_AGGREGATE_ONLY' or doc['publication_authorized'] is not False:
        raise ValueError('Local exact-content approval required; no remote authorization')
    if not isinstance(doc['files'],list) or len(doc['files'])!=len(TYPES):raise ValueError('Exactly seven files required')
    approved={}
    for item in doc['files']:
        if set(item)!={'path','sha256','type'}:raise ValueError('Invalid artifact record')
        rel=item['path']
        if rel not in TYPES or item['type']!=TYPES[rel] or rel in approved:raise ValueError('Unreviewed or repeated artifact')
        if not re.fullmatch('[0-9a-f]{64}',item['sha256']):raise ValueError('Invalid hash')
        path=root/rel
        for component in [path,*path.parents]:
            if component==root:break
            if component.is_symlink() or getattr(component.lstat(),'st_file_attributes',0)&1024:raise ValueError('Linked artifact rejected')
        if not path.resolve(strict=True).is_relative_to(root):raise ValueError('Artifact escapes root')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Editorial artifact changed after approval')
        if item['type']=='aggregate_figure' and not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Invalid reviewed PNG')
        approved[rel]=item['type']
    validate_editorial_tables(root)
    return approved

def load_editorial_tables(root):
    """Read only the hash-reviewed public CSVs, without any clinical connection."""
    root=Path(root).resolve()
    if set(approved_editorial_files(root))!=set(TYPES):
        raise ValueError('No exact owner-approved editorial bundle')
    result={}
    for name in ['corpus_volume','species','sex','field_coverage']:
        with (root/PREFIX/'tables'/(name+'.csv')).open(encoding='utf-8',newline='') as stream:
            result[name]=list(csv.DictReader(stream))
    return result

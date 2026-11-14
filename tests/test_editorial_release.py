"""Invented aggregates simulate approval records; no clinical inputs or results."""
from pathlib import Path
import csv,hashlib,json,struct,sys,tempfile,unittest,zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from editorial_release import TYPES,approved_editorial_files
from validate_candidate import validate

def fixture(root):
    for rel in TYPES:(root/rel).parent.mkdir(parents=True,exist_ok=True)
    def put(name,header,rows):
        with (root/'published/editorial/tables'/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f);w.writerow(header);w.writerows(rows)
    put('corpus_volume.csv',['metric','count','unit','denominator'],[
        ['Gold report records',120,'Gold record','Not applicable: snapshot count'],
        ['Extraction events',600,'Event row','Not applicable: snapshot count']])
    header=['category_en','category_es','count','denominator_records','percentage']
    put('species.csv',header,[['Canine','Canina',60,120,50.0],['Feline','Felina',60,120,50.0],['Unresolved species','Especie no resuelta',0,120,0.0],['Missing species','Especie ausente',0,120,0.0]])
    put('sex.csv',header,[['Male','Macho',60,120,50.0],['Female','Hembra',60,120,50.0],['Not specified','No especificado',0,120,0.0],['Blank or null','Vacío o nulo',0,120,0.0]])
    put('field_coverage.csv',['field','records_with_nonblank_value','records_null_or_blank','denominator_records','nonblank_percentage'],[[s,120,0,120,100.0] for s in ['species','sex','breed','study_type','outcome']])
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0\x20\x60\x80\xff'))+chunk(b'IEND',b'')
    for name in ['species','sex']:(root/'published/editorial/figures'/(name+'.png')).write_bytes(png)
    (root/'published/editorial/results.md').write_text('Invented software-test aggregates only. No scientific results.',encoding='utf-8')
    doc={'schema_version':1,'release_id':'SYNTHETIC_TEST_ONLY','kind':'REAL_AGGREGATED','owner_decision':'APPROVED_FOR_LOCAL_CANDIDATE','permission_basis':'OWNER_CONFIRMED_AGGREGATE_ONLY','publication_authorized':False,'files':[]}
    for rel,kind in TYPES.items():doc['files'].append({'path':rel,'type':kind,'sha256':hashlib.sha256((root/rel).read_bytes()).hexdigest()})
    save(root,doc)
    return doc

def save(root,doc):
    (root/'published/editorial-manifest.json').write_text(json.dumps(doc),encoding='utf-8')

def rehash(root,doc,rel):
    for item in doc['files']:
        if item['path']==rel:item['sha256']=hashlib.sha256((root/rel).read_bytes()).hexdigest()
    save(root,doc)

class EditorialTests(unittest.TestCase):
    def test_exact_reviewed_set_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root)
            self.assertEqual(set(approved_editorial_files(root)),set(TYPES))
            self.assertEqual(validate(root)['status'],'PASS')

    def test_changed_file_fails_without_reapproval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root)
            (root/'published/editorial/results.md').write_text('Changed',encoding='utf-8')
            self.assertEqual(validate(root)['status'],'FAIL')

    def test_individual_fields_fail_even_with_updated_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);doc=fixture(root);rel='published/editorial/tables/species.csv'
            (root/rel).write_text('report_id,source_text\nSYNTHETIC_ID,SYNTHETIC_TEXT\n',encoding='utf-8');rehash(root,doc,rel)
            self.assertEqual(validate(root)['status'],'FAIL')

    def test_wrong_denominator_fails_even_with_updated_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);doc=fixture(root);rel='published/editorial/tables/species.csv'
            p=root/rel;p.write_text(p.read_text(encoding='utf-8').replace(',120,50.0',',121,50.0'),encoding='utf-8');rehash(root,doc,rel)
            self.assertEqual(validate(root)['status'],'FAIL')

    def test_extra_csv_not_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root)
            (root/'unreviewed.csv').write_text('SYNTHETIC_COLUMN\nSYNTHETIC_VALUE\n',encoding='utf-8')
            self.assertEqual(validate(root)['status'],'FAIL')

    def test_missing_owner_decision_and_remote_claim_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);doc=fixture(root);doc['owner_decision']='PENDING';save(root,doc)
            self.assertEqual(validate(root)['status'],'FAIL')
            doc['owner_decision']='APPROVED_FOR_LOCAL_CANDIDATE';doc['publication_authorized']=True;save(root,doc)
            self.assertEqual(validate(root)['status'],'FAIL')

if __name__=='__main__':unittest.main()

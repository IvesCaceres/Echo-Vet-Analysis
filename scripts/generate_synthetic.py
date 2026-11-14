"""Generate invented Gold-compatible examples; never reads a clinical database."""
from pathlib import Path
import json
import sqlite3


def generate(destination):
    root = Path(destination).resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = root / "gold_v2_final.db"
    if path.exists():
        raise FileExistsError("Refusing to overwrite an existing database")
    schema_path = Path(__file__).resolve().parents[1] / "synthetic" / "schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    conn = sqlite3.connect(path)
    for table in schema:
        columns = []
        for col in table["columns"]:
            definition = '"' + col["name"] + '" ' + col["type"]
            if col["pk"] and sum(bool(c["pk"]) for c in table["columns"]) == 1:
                definition += " PRIMARY KEY"
            columns.append(definition)
        composite = sorted((c for c in table["columns"] if c["pk"]), key=lambda c: c["pk"])
        if len(composite) > 1:
            columns.append("PRIMARY KEY (" + ",".join('"' + c["name"] + '"' for c in composite) + ")")
        for fk in table.get("foreign_keys", []):
            if fk["to"]:
                columns.append('FOREIGN KEY ("' + fk["from"] + '") REFERENCES "' + fk["table"] + '"("' + fk["to"] + '")')
        conn.execute('CREATE TABLE "' + table["name"] + '" (' + ",".join(columns) + ")")

    def insert(name, values):
        columns = next(t["columns"] for t in schema if t["name"] == name)
        row = []
        for col in columns:
            key = col["name"]
            default = 1 if "INT" in col["type"].upper() else 1.0 if "REAL" in col["type"].upper() else "SYNTHETIC"
            row.append(values.get(key, default))
        conn.execute('INSERT INTO "' + name + '" VALUES (' + ",".join("?" for _ in row) + ")", row)

    insert("gold_build_runs_v2", {"build_run_id": "SYNTHETIC_RUN", "report_count": 120, "event_count": 600,
                                   "publication_mode": "SYNTHETIC_DEMO", "validation_status": "DEMO_ONLY"})
    for concept in range(1, 5):
        label = "synthetic_concept_" + str(concept)
        insert("dim_clinical_concept_v2", {"concept_id": concept, "canonical_name": label,
                                          "display_name": label, "concept_type": "SYNTHETIC", "active": 1})
        insert("clinical_concept_alias_v2", {"alias": "synthetic_alias_" + str(concept), "concept_id": concept})
    insert("clinical_concept_taxonomy_v2", {"parent_concept_id": 1, "child_concept_id": 2})
    event = 100000
    for i in range(120):
        report = 100000 + i
        year = 2022 + i % 5
        month = 1 + i % 12
        date = f"{year}-{month:02d}-01"
        insert("gold_reports_v2", {"report_id": report, "raw_report_id": report,
              "patient_name": f"SYNTHETIC_EXAMPLE_{i:03d}", "species": ["Canino", "Felino"][i % 2],
              "breed": ["SYNTHETIC_BREED_A", "SYNTHETIC_BREED_B"][i % 2], "sex": ["Macho", "Hembra"][i % 2],
              "age_text": f"{1+i%12} años", "study_type": "SYNTHETIC_STUDY", "study_date": date,
              "study_year": year, "study_month": month, "study_day": 1, "study_date_raw": date,
              "date_interval_start": date, "date_interval_end": date, "date_precision": "day",
              "date_source": "synthetic_generator", "date_quality": "SYNTHETIC", "outcome": "SYNTHETIC",
              "source_document": "SYNTHETIC_ONLY", "source_path": "SYNTHETIC_ONLY"})
        for index, status in enumerate(["present", "present", "absent", "possible", "present"]):
            event += 1
            concept = 1 if index < 3 else 2 + i % 3
            text = "SYNTHETIC_DESCRIPTION_A" if index < 3 else "SYNTHETIC_DESCRIPTION_B"
            insert("gold_clinical_events_v2", {"event_id": event, "report_id": report, "concept_id": concept,
                  "canonical_concept": "synthetic_concept_"+str(concept), "assertion_status": status,
                  "relation_type": "direct", "strength": "explicit", "descriptor_json": "{}",
                  "source_span_start": 0, "source_span_end": 10, "source_text": text, "source_clause": text,
                  "source_type": "SYNTHETIC", "event_origin": "SYNTHETIC", "rule_id": "SYNTHETIC_RULE"})
            insert("gold_event_provenance_v2", {"event_id": event, "provenance_order": 1,
                  "source_type": "SYNTHETIC", "source_row_id": report, "source_field": "SYNTHETIC",
                  "source_hash": "SYNTHETIC_HASH", "rule_id": "SYNTHETIC_RULE", "discarded": 0})
        insert("gold_discarded_event_provenance_v2", {"discarded_provenance_id": report, "report_id": report,
              "kept_event_id": event, "canonical_concept": "synthetic_concept_1", "assertion_status": "present",
              "relation_type": "direct", "source_span_start": 0, "source_span_end": 10,
              "source_text": "SYNTHETIC_DESCRIPTION", "source_rule": "SYNTHETIC_RULE",
              "discard_reason": "SYNTHETIC_DUPLICATE", "provenance_status": "SYNTHETIC",
              "build_run_id": "SYNTHETIC_RUN"})
    conn.commit()
    conn.close()
    (root / "SYNTHETIC_ONLY.json").write_text(json.dumps({"type": "SYNTHETIC_DEMO", "reports": 120,
         "description": "Invented examples; not a sample or statistical model of the clinical corpus."})+"\n", encoding="utf-8")
    return path

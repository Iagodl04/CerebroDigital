import sqlite3, zipfile, json, os, time

ZIP_PATH = "Salud conectada.zip"
EXTRACT_DIR = "./salud_conectada_unzip"
OUTPUT_JSON = "./health_data.json"
MERGE_OLD = False   # ⬅️ Recomendado: sobrescribir (evita acumulación)
# Si quieres fusionar varias exportaciones, pon True (tenemos dedup abajo).

# 1) Extraer ZIP si no existe la carpeta
if not os.path.exists(EXTRACT_DIR):
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(EXTRACT_DIR)
        print("✅ ZIP extraído")

# 2) Abrir DB
db_files = [f for f in os.listdir(EXTRACT_DIR) if f.endswith(".db")]
if not db_files:
    raise FileNotFoundError("No hay .db dentro del ZIP")
DB_PATH = os.path.join(EXTRACT_DIR, db_files[0])

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 3) Listar tablas con datos
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';")]
export_data = {}
for t in tables:
    try:
        n = cur.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0]
        if n == 0:
            continue
        cols = [c[1] for c in cur.execute(f"PRAGMA table_info({t});").fetchall()]
        rows = cur.execute(f"SELECT * FROM {t};").fetchall()
        export_data[t] = [dict(zip(cols, r)) for r in rows]
        print(f"✅ {t}: {len(rows)} filas")
    except Exception as e:
        print(f"⚠️ {t}: {e}")

conn.close()

# 4) Fusionar con JSON previo (opcional) **con dedup**
def make_key(table, rec):
    # Prioridad: uuid > dedupe_hash > clave compuesta
    if "uuid" in rec and rec["uuid"]:
        return f"{table}|uuid|{rec['uuid']}"
    if "dedupe_hash" in rec and rec["dedupe_hash"]:
        return f"{table}|dedupe|{rec['dedupe_hash']}"
    # Clave compuesta segura para pasos (y parecidas)
    comp = []
    for k in ("start_time","end_time","time","count","app_info_id","device_info_id","recording_method","local_date"):
        if k in rec: comp.append(str(rec[k]))
    if comp:
        return f"{table}|comp|" + "|".join(comp)
    # Último recurso: todas las columnas (menos row_id)
    return f"{table}|row|" + "|".join([f"{k}={rec[k]}" for k in sorted(rec.keys()) if k!="row_id"])

if MERGE_OLD and os.path.exists(OUTPUT_JSON):
    try:
        with open(OUTPUT_JSON,"r",encoding="utf-8") as f:
            old = json.load(f)
    except Exception:
        old = {}
    merged = {}
    for t in set(list(export_data.keys()) + list(old.keys())):
        new_list = export_data.get(t, [])
        old_list = old.get(t, [])
        seen = set()
        out = []
        for rec in old_list + new_list:
            k = make_key(t, rec)
            if k in seen: 
                continue
            seen.add(k)
            out.append(rec)
        merged[t] = out
    export_data = merged
    print("🧩 Fusionado + deduplicado.")

# 5) Guardar JSON
payload = {
    "_meta": {"exported_at": int(time.time()*1000)},
    **export_data
}
with open(OUTPUT_JSON,"w",encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

print(f"\n🎉 Guardado: {OUTPUT_JSON} | Tablas: {len(export_data)}")


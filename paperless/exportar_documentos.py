#!/usr/bin/env python3
import sqlite3
import csv
import subprocess
import os
from datetime import datetime

# Configuración
DB_SOURCE = "/var/lib/docker/volumes/paperless-ngx_data/_data/db.sqlite3"
DB_COPY = "./db_copy.sqlite3"
OUTPUT_CSV = "./documentos_paperless.csv"

# Paso 1: Copiar la BD actualizada (requiere sudo)
print("📥 Copiando base de datos actualizada...")
subprocess.run(['sudo', 'cp', DB_SOURCE, DB_COPY], check=True)
subprocess.run(['sudo', 'chown', 'piQuique:piQuique', DB_COPY], check=True)
print("✅ Copia actualizada")

# Paso 2: Conectar y exportar
print("📊 Exportando datos...")
conn = sqlite3.connect(DB_COPY)
cur = conn.cursor()

query = """
SELECT id, title, modified, filename, page_count, content 
FROM documents_document
ORDER BY modified DESC;
"""

cur.execute(query)
rows = cur.fetchall()
columns = [description[0] for description in cur.description]

# Guardar en CSV
with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    writer.writerows(rows)

conn.close()

print(f"✅ Exportados {len(rows)} documentos a: {OUTPUT_CSV}")

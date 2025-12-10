import json
import pandas as pd
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

# --- Configuración ---
# Ruta al archivo JSON DENTRO del contenedor
JSON_FILE_PATH = "/data/health_data.json"
# ---------------------

app = Flask(__name__)
CORS(app) # Permite que tu index.html (en otro puerto) haga peticiones

# --- Variables globales para guardar los datos procesados ---
daily_steps = None
daily_sleep = None

# --- Funciones de tu script (parseo y helpers) ---
def parse_ts(x):
    try:
        x = float(x)
        if x > 1e12: return pd.to_datetime(x, unit="ms", utc=True)
        if x > 1e9:  return pd.to_datetime(x, unit="s", utc=True)
    except Exception: pass
    return pd.to_datetime(x, utc=True, errors="coerce")

def safe_numeric(df, *cols):
    for c in cols:
        if c in df.columns:
            s = pd.to_numeric(df[c], errors="coerce")
            if s.notna().any(): return s
    return pd.Series(dtype=float)

# --- Funciones para cargar y procesar los datos AL INICIO ---
def load_and_process_data():
    global daily_steps, daily_sleep
    print(f"--- Cargando datos desde {JSON_FILE_PATH} ---")
    
    try:
        # 1. Leer el JSON directamente
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"--- JSON '{JSON_FILE_PATH}' cargado y parseado ---")
        if "_meta" in data: data.pop("_meta", None)

        # 2. Procesar Pasos (como en tu script)
        if "steps_record_table" in data:
            df_steps = pd.DataFrame(data["steps_record_table"])
            df_steps["start_time"] = df_steps["start_time"].apply(parse_ts)
            df_steps["date"] = df_steps["start_time"].dt.tz_convert("Europe/Madrid").dt.date
            df_steps["count"] = safe_numeric(df_steps, "count", "steps", "step_count", "value")
            df_steps = df_steps.dropna(subset=["date", "count"])
            if not df_steps.empty:
                daily_steps = df_steps.groupby("date")["count"].sum()
                print(f"✅ Datos de Pasos procesados ({len(daily_steps)} días)")
        
        # 3. Procesar Sueño (como en tu script)
        if "sleep_session_record_table" in data:
            df_sleep = pd.DataFrame(data["sleep_session_record_table"])
            df_sleep["start_time"] = df_sleep["start_time"].apply(parse_ts)
            df_sleep["end_time"] = df_sleep["end_time"].apply(parse_ts)
            df_sleep["duration_h"] = (df_sleep["end_time"] - df_sleep["start_time"]).dt.total_seconds() / 3600
            df_sleep = df_sleep.dropna(subset=["duration_h"])
            df_sleep["date"] = df_sleep["end_time"].dt.tz_convert("Europe/Madrid").dt.date
            if not df_sleep.empty:
                daily_sleep = df_sleep.groupby("date")["duration_h"].sum()
                print(f"✅ Datos de Sueño procesados ({len(daily_sleep)} días)")
        
        print("--- Carga de datos inicial completada ---")

    except FileNotFoundError:
        print(f"!!! ERROR: No se encontró el archivo {JSON_FILE_PATH}")
    except Exception as e:
        print(f"!!! ERROR al cargar o procesar datos: {e}")

# --- El Endpoint de la API ---
@app.route('/health')
def get_health_data():
    date_query_str = request.args.get('date') # ej: "2025-11-03"
    if not date_query_str:
        return jsonify({"error": "Falta el parámetro 'date'"}), 400
    
    try:
        query_date_obj = datetime.strptime(date_query_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido, usar YYYY-MM-DD"}), 400

    steps = 0
    if daily_steps is not None and query_date_obj in daily_steps:
        steps = int(daily_steps[query_date_obj])
        
    sleep = 0.0
    if daily_sleep is not None and query_date_obj in daily_sleep:
        sleep = round(daily_sleep[query_date_obj], 1)

    health_data = {
        "steps": steps,
        "sleep": sleep
    }
    return jsonify(health_data)

# --- Ejecución ---
if __name__ == '__main__':
    load_and_process_data() # Carga los datos una sola vez al iniciar
    print("--- Iniciando servidor web Flask en puerto 5000 ---")
    app.run(host='0.0.0.0', port=5000)

from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import csv
import os

app = Flask(__name__)
# Permitir que tu index.html (en :8088) llame a esta API (en :8093)
CORS(app) 

# Rutas a tus archivos (basado en tu 'ls' y 'pwd')
BASE_PATH = "/home/piQuique/ptiProject/calendar/data"
SCRIPT_PATH = os.path.join(BASE_PATH, "generar_csv.sh")
CSV_PATH = os.path.join(BASE_PATH, "eventos_limpios.csv")

@app.route('/calendar', methods=['GET'])
def get_calendar_events():
    # 1. Obtener la fecha de la URL (ej: ?date=2025-11-06)
    date_query = request.args.get('date')
    if not date_query:
        return jsonify({"error": "Falta el parámetro 'date'"}), 400

    # 2. Ejecutar tu script .sh para regenerar el CSV
    try:
        # Importante: ejecutar el script desde su directorio base
        # Damos 10 segundos de tiempo límite
        subprocess.run(
            ['bash', SCRIPT_PATH], 
            cwd=BASE_PATH, 
            check=True, 
            timeout=10,
            capture_output=True, # Captura stdout/stderr
            text=True
        )
    except Exception as e:
        error_output = e.stderr if hasattr(e, 'stderr') else str(e)
        print(f"Error al ejecutar generar_csv.sh: {error_output}")
        return jsonify({"error": "Fallo al generar el script de CSV", "details": error_output}), 500

    # 3. Leer el archivo eventos_limpios.csv
    events = []
    try:
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                events.append(row)
    except Exception as e:
        print(f"Error al leer el CSV: {e}")
        return jsonify({"error": "Fallo al leer el archivo CSV"}), 500

    # 4. Filtrar los eventos por la fecha solicitada
    filtered_events = []
    for event in events:
        # Tu CSV usa formato DD-MM-YYYY (ej: 07-11-2025)
        # La API de JS pide YYYY-MM-DD (ej: 2025-11-07)
        # Hay que convertirlos para que coincidan
        try:
            csv_day, csv_month, csv_year = event['Dia'].split('-')
            csv_date_iso = f"{csv_year}-{csv_month}-{csv_day}"
        except ValueError:
            continue # Ignorar fila si la fecha está mal

        if csv_date_iso == date_query:
            # 5. Formatear los datos como los espera tu index.html
            filtered_events.append({
                "type": "calendar", # Tipo para la timeline
                "time": event['Inicio'], # ej: "10:00" o "00:00"
                "title": event['Titulo'],
                "location": event['Ubicacion'],
                "description": event['Descripcion'],
                "end_time": event['Fin'] # ej: "13:00" o "24:00"
            })

    # 6. Devolver los eventos filtrados como JSON
    # Ordenamos por hora de inicio (time)
    sorted_events = sorted(filtered_events, key=lambda x: x['time'])
    return jsonify(sorted_events)

if __name__ == '__main__':
    # Ejecutar la API en el puerto 8093, accesible en tu red local
    print("Iniciando API de Calendario en http://0.0.0.0:8093")
    app.run(host='0.0.0.0', port=8093, debug=True)

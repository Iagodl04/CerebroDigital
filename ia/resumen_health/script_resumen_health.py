#!/usr/bin/env python3
import json
import requests
import csv
from datetime import datetime, timedelta
from collections import defaultdict

# Configuración de Ollama
OLLAMA_URL = "http://localhost:11435/api/generate"
MODEL = "gemma2:2b"

# Rutas
HEALTH_JSON = "../../health/health_data.json"
OUTPUT_TXT = "./resumenes_health.txt"
CSV_TEMP = "./health_daily.csv"

def cargar_datos_health():
    """Carga datos de health_data.json"""
    with open(HEALTH_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def agrupar_por_dia(data):
    """Agrupa los datos de salud por día"""
    dias = defaultdict(lambda: {
        'pasos': 0,
        'distancia_km': 0,
        'horas_sueno': 0,
        'calorias': 0,
        'ejercicio_min': 0
    })
    
    # Procesar pasos
    if 'steps_record_table' in data:
        for record in data['steps_record_table']:
            local_date = record.get('local_date')
            if local_date:
                fecha = datetime(1970, 1, 1) + timedelta(days=local_date)
                dia_str = fecha.strftime('%Y-%m-%d')
                dias[dia_str]['pasos'] += record.get('count', 0)
    
    # Procesar distancia
    if 'distance_record_table' in data:
        for record in data['distance_record_table']:
            local_date = record.get('local_date')
            if local_date:
                fecha = datetime(1970, 1, 1) + timedelta(days=local_date)
                dia_str = fecha.strftime('%Y-%m-%d')
                dias[dia_str]['distancia_km'] += record.get('distance', 0) / 1000
    
    # Procesar sueño
    if 'sleep_session_record_table' in data:
        for record in data['sleep_session_record_table']:
            start_time = record.get('start_time')
            end_time = record.get('end_time')
            if start_time and end_time:
                duracion_ms = end_time - start_time
                duracion_horas = duracion_ms / (1000 * 60 * 60)
                
                local_date = record.get('local_date')
                if local_date:
                    fecha = datetime(1970, 1, 1) + timedelta(days=local_date)
                    dia_str = fecha.strftime('%Y-%m-%d')
                    dias[dia_str]['horas_sueno'] += duracion_horas
    
    # Procesar ejercicio
    if 'exercise_session_record_table' in data:
        for record in data['exercise_session_record_table']:
            start_time = record.get('start_time')
            end_time = record.get('end_time')
            if start_time and end_time:
                duracion_ms = end_time - start_time
                duracion_min = duracion_ms / (1000 * 60)
                
                local_date = record.get('local_date')
                if local_date:
                    fecha = datetime(1970, 1, 1) + timedelta(days=local_date)
                    dia_str = fecha.strftime('%Y-%m-%d')
                    dias[dia_str]['ejercicio_min'] += duracion_min
    
    # Procesar calorías
    if 'total_calories_burned_record_table' in data:
        for record in data['total_calories_burned_record_table']:
            local_date = record.get('local_date')
            if local_date:
                fecha = datetime(1970, 1, 1) + timedelta(days=local_date)
                dia_str = fecha.strftime('%Y-%m-%d')
                energia = record.get('energy', 0)
                if isinstance(energia, (int, float)):
                    dias[dia_str]['calorias'] += energia
    
    return dias

def exportar_csv(dias):
    """Exporta datos agregados a CSV para pasarle a la IA"""
    with open(CSV_TEMP, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['fecha', 'pasos', 'distancia_km', 'ejercicio_min', 'horas_sueno', 'calorias'])
        
        for fecha, datos in sorted(dias.items()):
            # Solo exportar días con datos significativos
            if any([datos['pasos'] > 0, datos['distancia_km'] > 0.1, 
                   datos['horas_sueno'] > 0.5, datos['ejercicio_min'] > 5]):
                writer.writerow([
                    fecha,
                    int(datos['pasos']),
                    round(datos['distancia_km'], 2),
                    int(datos['ejercicio_min']),
                    round(datos['horas_sueno'], 2),
                    int(datos['calorias'])
                ])

def generar_resumen_ia(fecha, datos):
    """Genera resumen interpretativo usando Ollama"""
    
    # Preparar datos en formato legible
    datos_texto = f"""Fecha: {fecha}
Pasos: {int(datos['pasos'])}
Distancia: {datos['distancia_km']:.2f} km
Ejercicio: {int(datos['ejercicio_min'])} minutos
Sueño: {datos['horas_sueno']:.1f} horas
Calorías: {int(datos['calorias'])} kcal"""
    
    prompt = f"""Genera un resumen narrativo de UN DÍA de actividad física en una sola frase siguiendo este formato:

"El día [fecha], hiciste [X pasos], recorriste [X km], [si ejercicio > 5 min: hiciste ejercicio durante X min], [si sueño > 0.5h: dormiste X horas]"

Datos del día:
{datos_texto}

IMPORTANTE:
- Una sola frase en español
- Solo menciona datos que sean > 0
- Si pasos = 0, no lo menciones
- Si sueño = 0, no lo menciones
- Usa comas para separar y "y" antes del último elemento
- Ejemplo: "El día 2025-10-13 hiciste 8542 pasos, recorriste 6.34 km y dormiste 7.5 horas."

Responde SOLO con la frase, sin explicaciones."""
    
    data = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=data, timeout=90)
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception as e:
        return f"Error al generar resumen para {fecha}: {str(e)}"

def procesar_health(health_json, archivo_salida):
    """Procesa datos de salud y genera resúmenes con IA"""
    
    print("📊 Cargando datos de salud...")
    data = cargar_datos_health()
    
    print("📅 Agrupando datos por día...")
    dias = agrupar_por_dia(data)
    
    print("💾 Exportando CSV temporal...")
    exportar_csv(dias)
    
    # Filtrar días con datos significativos
    dias_con_datos = {
        fecha: datos for fecha, datos in dias.items()
        if any([datos['pasos'] > 0, datos['distancia_km'] > 0.1, 
               datos['horas_sueno'] > 0.5, datos['ejercicio_min'] > 5])
    }
    
    dias_ordenados = sorted(dias_con_datos.items())
    
    print(f"\n🤖 Generando resúmenes con IA para {len(dias_ordenados)} días...\n")
    
    with open(archivo_salida, 'w', encoding='utf-8') as out:
        out.write(f"=== RESÚMENES DE ACTIVIDAD DIARIA (Generados por IA) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
        
        for i, (fecha, datos) in enumerate(dias_ordenados, 1):
            print(f"[{i}/{len(dias_ordenados)}] Generando resumen para {fecha}...")
            
            resumen = generar_resumen_ia(fecha, datos)
            
            out.write(f"{resumen}\n\n")
            print(f"  ✓ Completado")
    
    print(f"\n✅ Resúmenes guardados en: {archivo_salida}")
    print(f"📈 Total procesado: {len(dias_ordenados)} días")
    print(f"📄 CSV temporal guardado en: {CSV_TEMP}")

if __name__ == "__main__":
    import os
    
    if not os.path.exists(HEALTH_JSON):
        print(f"❌ Error: No se encuentra {HEALTH_JSON}")
        exit(1)
    
    procesar_health(HEALTH_JSON, OUTPUT_TXT)

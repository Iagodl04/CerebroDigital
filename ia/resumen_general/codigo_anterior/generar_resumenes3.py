#!/usr/bin/env python3
import csv
import requests
import sys
from datetime import datetime

# Configuración de Ollama
OLLAMA_URL = "http://localhost:11435/api/generate"
MODEL = "gemma2:2b"

# Rutas
INPUT_CSV = "./datos_unificados.csv"
OUTPUT_TXT = "./resumen_dia.txt"

def leer_datos_dia(fecha_objetivo):
    """Lee datos de un día específico del CSV, incluyendo fotos"""
    datos = {
        'health': None,
        'eventos': [],
        'documentos': [],
        'fotos': None # Nuevo campo para fotos
    }

    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fecha = row.get('fecha', '')

            if fecha != fecha_objetivo:
                continue

            # --- 1. HEALTH ---
            try:
                pasos = int(row.get('pasos', '0') or '0')
                if pasos > 0 and not datos['health']:
                    datos['health'] = {
                        'pasos': pasos,
                        'distancia_km': float(row.get('distancia_km', '0') or '0'),
                        'ejercicio_min': int(row.get('ejercicio_min', '0') or '0'),
                        'horas_sueno': float(row.get('horas_sueno', '0') or '0'),
                        'calorias': int(row.get('calorias', '0') or '0')
                    }
            except (ValueError, TypeError):
                pass

            # --- 2. FOTOS (NUEVO) ---
            try:
                cant_fotos = int(row.get('fotos_cantidad', '0') or '0')
                # Si encontramos fotos y aún no las hemos guardado (o si esta fila tiene más datos)
                if cant_fotos > 0:
                    current_count = datos['fotos']['cantidad'] if datos['fotos'] else 0
                    if cant_fotos >= current_count:
                        datos['fotos'] = {
                            'cantidad': cant_fotos,
                            'inicio': row.get('fotos_hora_inicio', ''),
                            'fin': row.get('fotos_hora_fin', ''),
                            'nombres': row.get('fotos_nombres', '')
                        }
            except (ValueError, TypeError):
                pass

            # --- 3. EVENTOS ---
            evento_titulo = row.get('evento_titulo', '').strip()
            if evento_titulo and evento_titulo not in ['', 'no tiene']:
                evento = {
                    'titulo': evento_titulo,
                    'ubicacion': row.get('evento_ubicacion', '').strip(),
                    'descripcion': row.get('evento_descripcion', '').strip(),
                    'hora_inicio': row.get('evento_hora_inicio', '').strip(),
                    'hora_fin': row.get('evento_hora_fin', '').strip()
                }
                if not any(e['titulo'] == evento['titulo'] for e in datos['eventos']):
                    datos['eventos'].append(evento)

            # --- 4. DOCUMENTOS ---
            doc_titulo = row.get('doc_titulo', '').strip()
            if doc_titulo:
                doc = {
                    'titulo': doc_titulo,
                    'filename': row.get('doc_filename', '').strip(),
                    'paginas': row.get('doc_paginas', '').strip(),
                    'content': row.get('doc_content_preview', '').strip()
                }
                if not any(d['titulo'] == doc['titulo'] for d in datos['documentos']):
                    datos['documentos'].append(doc)

    return datos

def generar_resumen_dia(fecha, datos):
    """Genera resumen natural con personalidad de DIARIO"""

    # Preparar bloques de texto para el prompt
    info_health = ""
    if datos['health']:
        h = datos['health']
        info_health = f"""
        - Pasos caminados: {h['pasos']}
        - Distancia: {h['distancia_km']} km
        - Tiempo ejercicio: {h['ejercicio_min']} min
        - Sueño: {h['horas_sueno']} horas
        """

    info_eventos = ""
    if datos['eventos']:
        for ev in datos['eventos']:
            info_eventos += f"- Evento: {ev['titulo']} (Hora: {ev['hora_inicio']})\n"
            if ev['ubicacion']: info_eventos += f"  Ubicación: {ev['ubicacion']}\n"

    info_docs = ""
    if datos['documentos']:
        for doc in datos['documentos']:
            preview = doc['content'][:250].replace('\n', ' ') if doc['content'] else "Sin vista previa"
            info_docs += f"- Documento leído: '{doc['titulo']}'. Contenido: {preview}\n"

    info_fotos = ""
    if datos['fotos'] and datos['fotos']['cantidad'] > 0:
        f = datos['fotos']
        info_fotos = f"""
        - Total fotos tomadas: {f['cantidad']}
        - Hora primera foto: {f['inicio']}
        - Hora última foto: {f['fin']}
        - Nombres de archivo (pista): {f['nombres'][:300]}...
        """

    # --- PROMPT DIARIO PERSONAL ---
    prompt = f"""
Actúa como mi Diario Personal Inteligente. Escribe una entrada de diario para mí, basada en lo que hice el día {fecha}.

DATOS DE MI DÍA:
[SALUD Y ACTIVIDAD]
{info_health if info_health else "No se registraron datos de salud."}

[AGENDA Y EVENTOS]
{info_eventos if info_eventos else "Sin eventos agendados."}

[MEMORIAS Y FOTOS]
{info_fotos if info_fotos else "No hiciste fotos hoy."}

[TRABAJO Y DOCUMENTOS]
{info_docs if info_docs else "No se consultaron documentos."}

INSTRUCCIONES DE ESTILO:
1. Escribe en PRIMERA PERSONA ("Hoy he caminado...") o SEGUNDA PERSONA ("Hoy caminaste..."). Elige lo que suene más natural.
2. Tono: Reflexivo, cercano y casual. NO uses lenguaje robótico.
3. FOTOS: Si hay fotos, menciónalo como algo positivo (guardar recuerdos). Si la hora de inicio es muy temprano (00:00 - 05:00), comenta que estabas despierto tarde/temprano. Si hay muchas fotos, di que estabas creativo.
4. DOCUMENTOS: Resume brevemente qué tema trataste.
5. Longitud: Unos 2 párrafos bien conectados.

Genera la entrada del diario:
"""

    data_request = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,    # Creatividad para sonar humano
            "top_p": 0.9,          # Variedad de vocabulario
            "num_predict": 350,    # Longitud suficiente
            "repeat_penalty": 1.1 
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=data_request, timeout=180)
        response.raise_for_status()
        return response.json()["response"].strip()

    except Exception as e:
        return f"Error generando resumen: {str(e)}"

def procesar_dia(fecha):
    """Procesa un día específico y muestra debug en consola"""

    print(f"🔍 Buscando datos del {fecha}...\n")
    datos = leer_datos_dia(fecha)

    tiene_health = datos['health'] is not None
    tiene_eventos = len(datos['eventos']) > 0
    tiene_docs = len(datos['documentos']) > 0
    tiene_fotos = datos['fotos'] is not None and datos['fotos']['cantidad'] > 0

    if not (tiene_health or tiene_eventos or tiene_docs or tiene_fotos):
        print(f"❌ No hay datos para el dia {fecha}")
        return

    # --- DEBUG EN CONSOLA ---
    print("✅ Datos encontrados:")
    if tiene_health:
        print(f"   🏃 Actividad: {datos['health']['pasos']:,} pasos")
    if tiene_eventos:
        print(f"   📅 Eventos: {len(datos['eventos'])}")
    if tiene_docs:
        print(f"   📄 Documentos: {len(datos['documentos'])}")
    if tiene_fotos:
        print(f"   📸 Fotos: {datos['fotos']['cantidad']} (De {datos['fotos']['inicio']} a {datos['fotos']['fin']})")

    print(f"\n🧠 Generando resumen con IA...\n")
    resumen = generar_resumen_dia(fecha, datos)

    # Guardar en TXT (Modo Legacy/Debug)
    with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
        f.write(f"=== DIARIO DEL {fecha} ===\n")
        f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"{resumen}\n")

    print("📜 RESUMEN GENERADO:")
    print(f"\n{resumen}\n")
    print(f"💾 Guardado en: {OUTPUT_TXT}")

if __name__ == "__main__":
    import os

    if not os.path.exists(INPUT_CSV):
        print(f"Error: No se encuentra {INPUT_CSV}")
        exit(1)

    if len(sys.argv) < 2:
        print("Uso: python3 generar_resumenes.py YYYY-MM-DD")
        exit(1)

    fecha = sys.argv[1]

    try:
        datetime.strptime(fecha, '%Y-%m-%d')
    except ValueError:
        print("Formato incorrecto. Usa: YYYY-MM-DD")
        exit(1)

    procesar_dia(fecha)

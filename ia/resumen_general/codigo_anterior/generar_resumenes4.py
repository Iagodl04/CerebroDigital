#!/usr/bin/env python3
import csv
import requests
import sys
import os
from datetime import datetime

# --- IMPORTAR UNIFICADOR ---
# Intentem importar les funcions de l'altre script per actualitzar les dades al moment
try:
    from unificar_datos import unificar_datos, guardar_csv
except ImportError:
    print("⚠️ Error CRÍTIC: No es troba 'unificar_datos.py' al mateix directori.")
    print("   Assegura't que els dos fitxers estan junts.")
    sys.exit(1)

# --- CONFIGURACIÓ ---
OLLAMA_URL = "http://localhost:11435/api/generate" # Assegura't del port (11434 o 11435)
MODEL = "gemma2:2b"
INPUT_CSV = "./datos_unificados.csv"
OUTPUT_TXT = "./resumen_dia.txt"

# --- FUNCIONS ---

def leer_datos_dia(fecha_objetivo):
    """Lee datos de un día específico del CSV, incluyendo fotos"""
    datos = {
        'health': None,
        'eventos': [],
        'documentos': [],
        'fotos': {'cantidad': 0, 'inicio': '', 'fin': '', 'nombres': ''}
    }

    if not os.path.exists(INPUT_CSV):
        return datos

    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fecha = row.get('fecha', '')

            if fecha != fecha_objetivo:
                continue

            # 1. HEALTH (Dades de salut)
            try:
                pasos = int(row.get('pasos', '0') or '0')
                # Si hi ha passos i encara no hem guardat salut
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

            # 2. FOTOS (Nou bloc)
            try:
                cant_fotos = int(row.get('fotos_cantidad', '0') or '0')
                if cant_fotos > 0:
                    # Actualitzem si trobem dades (agafem el que tingui més info)
                    if cant_fotos >= datos['fotos']['cantidad']:
                        datos['fotos'] = {
                            'cantidad': cant_fotos,
                            'inicio': row.get('fotos_hora_inicio', ''),
                            'fin': row.get('fotos_hora_fin', ''),
                            'nombres': row.get('fotos_nombres', '')
                        }
            except (ValueError, TypeError):
                pass

            # 3. EVENTOS (Agenda)
            evento_titulo = row.get('evento_titulo', '').strip()
            if evento_titulo and evento_titulo not in ['', 'no tiene']:
                evento = {
                    'titulo': evento_titulo,
                    'ubicacion': row.get('evento_ubicacion', '').strip(),
                    'descripcion': row.get('evento_descripcion', '').strip(),
                    'hora_inicio': row.get('evento_hora_inicio', '').strip(),
                    'hora_fin': row.get('evento_hora_fin', '').strip()
                }
                # Evitem duplicats
                if not any(e['titulo'] == evento['titulo'] for e in datos['eventos']):
                    datos['eventos'].append(evento)

            # 4. DOCUMENTOS (Paperless)
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
    """Genera el prompt i crida a la IA"""

    # Construcció del text per a la IA (Context)
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
            # Retallem el contingut per no saturar la IA
            preview = doc['content'][:250].replace('\n', ' ') if doc['content'] else "Sin vista previa"
            info_docs += f"- Documento leído: '{doc['titulo']}'. Contenido: {preview}\n"

    info_fotos = ""
    if datos['fotos']['cantidad'] > 0:
        f = datos['fotos']
        info_fotos = f"""
        - Total fotos tomadas: {f['cantidad']}
        - Hora primera foto: {f['inicio']}
        - Hora última foto: {f['fin']}
        - Nombres de archivo: {f['nombres'][:300]}...
        """

    # --- PROMPT MESTRE (Roleplay Diari) ---
    prompt = f"""
Actúa como mi Diario Personal Inteligente. Tu tarea es escribir una entrada de diario para mí, basada en lo que hice el día {fecha}.

DATOS DE MI DÍA:
[SALUD Y ACTIVIDAD]
{info_health if info_health else "No se registraron datos de salud."}

[AGENDA Y EVENTOS]
{info_eventos if info_eventos else "Sin eventos agendados."}

[FOTOS Y RECUERDOS]
{info_fotos if info_fotos else "No hiciste fotos hoy."}

[TRABAJO Y DOCUMENTOS]
{info_docs if info_docs else "No se consultaron documentos."}

INSTRUCCIONES DE ESTILO:
1. Escribe en PRIMERA PERSONA ("Hoy he caminado...") o SEGUNDA PERSONA ("Hoy caminaste..."). Elige lo que suene más natural e íntimo.
2. Tono: Reflexivo, cercano y casual. NO uses lenguaje robótico o de reporte.
3. FOTOS: Si hay fotos, menciónalo como algo positivo (creatividad, recuerdos). Usa la hora de las fotos para deducir momentos del día (mañana, tarde, noche).
4. DOCUMENTOS: Resume brevemente qué tema trataste.
5. Si hice mucho ejercicio, felicítame. Si dormí poco, recomiéndame descansar.

Genera la entrada del diario:
"""

    data_request = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.4,    # Creativitat
            "top_p": 0.9,          # Varietat
            "num_predict": 350,    # Longitud
            "repeat_penalty": 1.1 
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=data_request, timeout=180)
        response.raise_for_status()
        return response.json()["response"].strip()

    except Exception as e:
        return f"Error conectando con Ollama: {str(e)}"

def procesar_dia(fecha):
    """Funció principal de processament"""

    print(f"🔍 Buscando datos para el {fecha}...")
    datos = leer_datos_dia(fecha)

    # Comprovar si tenim algo
    tiene_datos = (
        datos['health'] is not None or 
        len(datos['eventos']) > 0 or 
        len(datos['documentos']) > 0 or 
        datos['fotos']['cantidad'] > 0
    )

    if not tiene_datos:
        print(f"❌ No hay ninguna información registrada para el día {fecha}")
        return

    # Debug visual a la terminal
    print("\n✅ Datos encontrados:")
    if datos['health']:
        print(f"   🏃 Actividad: {datos['health']['pasos']:,} pasos")
    if datos['eventos']:
        print(f"   📅 Eventos: {len(datos['eventos'])}")
    if datos['documentos']:
        print(f"   📄 Documentos: {len(datos['documentos'])}")
    if datos['fotos']['cantidad'] > 0:
        print(f"   📸 Fotos: {datos['fotos']['cantidad']} (De {datos['fotos']['inicio']} a {datos['fotos']['fin']})")

    print(f"\n🧠 Generando historia con IA ({MODEL})...\n")
    resumen = generar_resumen_dia(fecha, datos)

    # Guardar resultat
    with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
        f.write(f"=== DIARIO DEL {fecha} ===\n")
        f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"{resumen}\n")

    print("📜 RESUMEN GENERADO:")
    print("-" * 40)
    print(resumen)
    print("-" * 40)
    print(f"💾 Guardado en: {OUTPUT_TXT}")

# --- PUNT D'ENTRADA PRINCIPAL ---
if __name__ == "__main__":
    
    # 1. Validació d'arguments
    if len(sys.argv) < 2:
        print("Uso: python3 generar_resumenes.py YYYY-MM-DD")
        sys.exit(1)

    fecha = sys.argv[1]

    try:
        datetime.strptime(fecha, '%Y-%m-%d')
    except ValueError:
        print("❌ Formato incorrecto. Usa: YYYY-MM-DD")
        sys.exit(1)

    # 2. ACTUALITZACIÓ AUTOMÀTICA DE DADES (La connexió clau)
    print("\n🔄 Sincronizando datos (Fotos, Calendar, Paperless, Health)...")
    try:
        # Cridem a les funcions de unificar_datos.py
        nuevos_datos = unificar_datos()
        guardar_csv(nuevos_datos)
        print("✅ Base de datos actualizada correctamente.\n")
    except Exception as e:
        print(f"❌ Error al actualizar datos: {e}")
        print("⚠️ Continuaremos usando el CSV existente...\n")

    # 3. GENERACIÓ DEL RESUM
    if not os.path.exists(INPUT_CSV):
        print(f"Error: No existe el archivo {INPUT_CSV}")
        sys.exit(1)

    procesar_dia(fecha)

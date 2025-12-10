#!/usr/bin/env python3
import csv
import requests
import sys
import os
from datetime import datetime

# --- IMPORTAR UNIFICADOR ---
try:
    from unificar_datos import unificar_datos, guardar_csv
except ImportError:
    print("⚠️ Error CRÍTIC: No es troba 'unificar_datos.py' al mateix directori.")
    print("   Assegura't que els dos fitxers estan junts.")
    sys.exit(1)

# --- CONFIGURACIÓ ---
OLLAMA_URL = "http://localhost:11435/api/generate" # Port del teu Docker
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

            # 1. HEALTH
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

            # 2. FOTOS
            try:
                cant_fotos = int(row.get('fotos_cantidad', '0') or '0')
                if cant_fotos > 0:
                    if cant_fotos >= datos['fotos']['cantidad']:
                        datos['fotos'] = {
                            'cantidad': cant_fotos,
                            'inicio': row.get('fotos_hora_inicio', ''),
                            'fin': row.get('fotos_hora_fin', ''),
                            'nombres': row.get('fotos_nombres', '')
                        }
            except (ValueError, TypeError):
                pass

            # 3. EVENTOS
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

            # 4. DOCUMENTOS
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
    """Genera el prompt i crida a la IA con instrucciones estrictas de estilo"""

    # Construcció del text per a la IA (Context)
    info_health = ""
    if datos['health']:
        h = datos['health']
        info_health = f"""
        - Pasos: {h['pasos']}
        - Distancia: {h['distancia_km']} km
        - Sueño: {h['horas_sueno']} horas
        """

    info_eventos = ""
    if datos['eventos']:
        for ev in datos['eventos']:
            info_eventos += f"- Evento: {ev['titulo']}\n"
            if ev['ubicacion']: info_eventos += f"  Lugar: {ev['ubicacion']}\n"

    info_docs = ""
    if datos['documentos']:
        for doc in datos['documentos']:
            preview = doc['content'][:200].replace('\n', ' ') if doc['content'] else ""
            info_docs += f"- Leíste sobre: '{doc['titulo']}'. Contexto: {preview}\n"

    info_fotos = ""
    if datos['fotos']['cantidad'] > 0:
        f = datos['fotos']
        # Passem la hora només com a referència pel prompt, però li prohibirem usar-la al text
        info_fotos = f"""
        - Cantidad de fotos: {f['cantidad']}
        - Momento del día (referencia): {f['inicio']} a {f['fin']}
        - Contexto visual: {f['nombres'][:300]}
        """

    # --- PROMPT MESTRE (MODIFICADO) ---
    prompt = f"""
Eres un narrador personal. Escribe una entrada de diario dirigida a MÍ, resumiendo mi día {fecha}.

DATOS DE MI DÍA:
[SALUD]
{info_health if info_health else "Sin datos de salud."}

[AGENDA]
{info_eventos if info_eventos else "Sin eventos."}

[GALERÍA DE FOTOS]
{info_fotos if info_fotos else "No hiciste fotos."}

[DOCUMENTOS LEÍDOS]
{info_docs if info_docs else "No leíste documentos."}

INSTRUCCIONES ESTRICTAS DE ESTILO:
1. **VOZ:** Escribe SIEMPRE en SEGUNDA PERSONA DEL SINGULAR ("Hoy caminaste...", "Hiciste fotos...", "Te sentiste...").
   - PROHIBIDO usar la primera persona ("Yo", "He caminado").

2. **NATURALIDAD:** El texto debe fluir como una conversación. No hagas listas con guiones.

3. **SOBRE LAS FOTOS:**
   - Si hubo fotos, intégralo en la narrativa (ej: "También dedicaste un rato a capturar recuerdos...").
   - **PROHIBIDO** decir la hora exacta (ej: NO digas "A las 14:30 hiciste fotos"). Usa expresiones como "por la tarde", "durante el día" o "más tarde".
   - **PROHIBIDO** mencionar nombres de archivo (ej: NO digas "IMG_2024.jpg").
   - **PROHIBIDO** frases meta como "puedes ver la foto aquí" o "se adjunta imagen".

4. **CONTENIDO:**
   - Si caminé mucho (+10k pasos), felicítame.
   - Conecta los eventos y documentos de forma lógica.

Genera el texto ahora:
"""

    data_request = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.6,    # Un pelín más creativo para evitar frases robóticas
            "top_p": 0.9,
            "num_predict": 300,
            "repeat_penalty": 1.2  # Penalización alta para que no repita palabras
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

    tiene_datos = (
        datos['health'] is not None or 
        len(datos['eventos']) > 0 or 
        len(datos['documentos']) > 0 or 
        datos['fotos']['cantidad'] > 0
    )

    if not tiene_datos:
        print(f"❌ No hay ninguna información registrada para el día {fecha}")
        return

    print("\n✅ Datos encontrados:")
    if datos['health']:
        print(f"   🏃 Actividad: {datos['health']['pasos']:,} pasos")
    if datos['eventos']:
        print(f"   📅 Eventos: {len(datos['eventos'])}")
    if datos['documentos']:
        print(f"   📄 Documentos: {len(datos['documentos'])}")
    if datos['fotos']['cantidad'] > 0:
        print(f"   📸 Fotos: {datos['fotos']['cantidad']}")

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

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Uso: python3 generar_resumenes.py YYYY-MM-DD")
        sys.exit(1)

    fecha = sys.argv[1]

    try:
        datetime.strptime(fecha, '%Y-%m-%d')
    except ValueError:
        print("❌ Formato incorrecto. Usa: YYYY-MM-DD")
        sys.exit(1)

    print("\n🔄 Sincronizando datos (Fotos, Calendar, Paperless, Health)...")
    try:
        nuevos_datos = unificar_datos()
        guardar_csv(nuevos_datos)
        print("✅ Base de datos actualizada correctamente.\n")
    except Exception as e:
        print(f"❌ Error al actualizar datos: {e}")
        print("⚠️ Continuaremos usando el CSV existente...\n")

    if not os.path.exists(INPUT_CSV):
        print(f"Error: No existe el archivo {INPUT_CSV}")
        sys.exit(1)

    procesar_dia(fecha)

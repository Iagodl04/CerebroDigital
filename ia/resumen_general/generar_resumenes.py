#!/usr/bin/env python3
import csv
import requests
import sys
import os
import time
from datetime import datetime

# --- RUTAS ABSOLUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "datos_unificados.csv")
OUTPUT_TXT = os.path.join(BASE_DIR, "resumen_dia.txt")

# --- IMPORTAR UNIFICADOR ---
try:
    sys.path.append(BASE_DIR)
    from unificar_datos import unificar_datos, guardar_csv
except ImportError:
    pass

# --- CONFIGURACIÓN OLLAMA ---
OLLAMA_URL = "http://127.0.0.1:11435/api/generate"
MODEL = "qwen2.5:1.5b" 

# --- 1. LECTURA Y ORGANIZACIÓN DE DATOS ---

def leer_datos_completos(fecha_objetivo):
    """
    Lee TODAS las columnas tal cual vienen del CSV (sin conversión de kcal ni filtros).
    """
    datos = {
        'health': {},
        'timeline': [], 
        'docs': []
    }

    if not os.path.exists(INPUT_CSV):
        return datos

    eventos_vistos = set() 

    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('fecha', '') != fecha_objetivo:
                continue

            # --- A. SALUD ---
            if not datos['health']:
                try:
                    pasos = int(row.get('pasos', '0') or '0')
                    
                    # SIN CONVERSIÓN: Se guardan las calorías tal cual (millones)
                    calorias = row.get('calorias', '0')
                    
                    datos['health'] = {
                        'pasos': pasos,
                        'distancia': row.get('distancia_km', '0'),
                        'ejercicio': row.get('ejercicio_min', '0'),
                        'sueno': row.get('horas_sueno', '0'),
                        'calorias': calorias
                    }
                except ValueError: pass

            # --- B. EVENTOS ---
            evt = row.get('evento_titulo', '').strip()
            hora_inicio = row.get('evento_hora_inicio', '00:00')
            
            if evt and evt not in ['', 'None']:
                firma = f"{evt}-{hora_inicio}"
                if firma not in eventos_vistos:
                    
                    # SIN FILTRO: Se pone la ubicación tal cual, aunque sea "no tiene"
                    ubicacion = row.get('evento_ubicacion', '')
                    
                    datos['timeline'].append({
                        'hora_sort': hora_inicio,
                        'texto': (
                            f"⏰ {hora_inicio}: "
                            f"Asistir al evento '{evt}' en {ubicacion}. " 
                            f"Nota: {row.get('evento_descripcion', '')}"
                        )
                    })
                    eventos_vistos.add(firma)

            # --- C. FOTOS ---
            try:
                cant = int(row.get('fotos_cantidad', '0') or '0')
                if cant > 0:
                    hora_foto = row.get('fotos_hora_inicio', '00:00')
                    nombres = row.get('fotos_nombres', '')
                    
                    firma_foto = f"FOTOS-{hora_foto}-{cant}"
                    if firma_foto not in eventos_vistos:
                        datos['timeline'].append({
                            'hora_sort': hora_foto,
                            'texto': (
                                f"📸 {hora_foto}: "
                                f"Sesión de fotos ({cant} imágenes). "
                                f"Archivos: [{nombres}]"
                            )
                        })
                        eventos_vistos.add(firma_foto)
            except ValueError: pass

            # --- D. DOCUMENTOS ---
            doc_tit = row.get('doc_titulo', '').strip()
            if doc_tit:
                doc_id = row.get('doc_id', '')
                if doc_id not in [d['id'] for d in datos['docs']]:
                    datos['docs'].append({
                        'id': doc_id,
                        'titulo': doc_tit,
                        'archivo': row.get('doc_filename', ''),
                        'paginas': row.get('doc_paginas', '')
                    })

    # Ordenar cronológicamente
    datos['timeline'].sort(key=lambda x: x['hora_sort'])
    
    return datos

# --- 2. LLAMADA A OLLAMA ---

def llamar_ollama(prompt):
    data_request = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1, 
            "num_predict": 400,
            "num_ctx": 2048
        }
    }
    try:
        print(f"[IA] Escribiendo historia con {MODEL}...")
        res = requests.post(OLLAMA_URL, json=data_request, timeout=120)
        res.raise_for_status()
        return res.json()["response"].strip()
    except Exception as e:
        return f"Error generando resumen: {e}"

# --- 3. CONSTRUCCIÓN DEL PROMPT ---

def generar_resumen(fecha, datos):
    h = datos['health']
    
    txt_salud = (
        f"Datos físicos: Caminaste {h.get('pasos')} pasos ({h.get('distancia')} km) "
        f"y quemaste {h.get('calorias')} calorías. "
        f"Ejercicio registrado: {h.get('ejercicio')} min. "
        f"Sueño: {h.get('sueno')} horas."
    )

    txt_timeline = ""
    if datos['timeline']:
        for item in datos['timeline']:
            txt_timeline += f"- {item['texto']}\n"
    else:
        txt_timeline = "No hubo eventos ni fotos registradas."

    txt_docs = ""
    if datos['docs']:
        for d in datos['docs']:
            txt_docs += f"- Doc ID {d['id']}: '{d['titulo']}' (Archivo: {d['archivo']}, {d['paginas']} págs).\n"
    else:
        txt_docs = "Sin gestión documental."

    prompt = f"""
Actua como un narrador personal meticuloso. Resume mi dia {fecha} en SEGUNDA PERSONA ("El dia [fecha] hiciste...", "Registraste...").
Tu objetivo es contar una historia coherente que integre TODOS los datos.

INSTRUCCIONES:
1. Sigue estrictamente el orden de la AGENDA (Timeline).
2. Integra los nombres de los archivos de fotos y documentos de forma natural en el texto.
3. NO inventes nada (nada de escuelas o trabajo si no está escrito).
4. Termina con el resumen de salud.
5. Habla en segunda persona y en pasado.

DATOS A INCLUIR Y ejemplos de algunos:

[AGENDA Y FOTOS - CRONOLOGICO]
{txt_timeline}
A las [evento_hora_inicio] fuiste al [evento titulo] hasta las [evento_hora_fin]
Hiciste la foto �[foto_nombres] a las  [fotos_hora_inicio]
[DOCUMENTOS PROCESADOS]
{txt_docs}

[ESTADISTICAS DE SALUD]
{txt_salud}
Has dormido [horas_sueno] nunca pongas he dormido [evento_hora_inicio] o [hora_incio]
Escribe el resumen ahora:
"""
    return llamar_ollama(prompt)

# --- 4. FUNCIÓN PÚBLICA PARA LA API ---

def obtener_resumen_texto(fecha):
    """
    Función requerida por IAapi.py
    """
    print(f"[GENERADOR] Procesando fecha {fecha}...")
    datos = leer_datos_completos(fecha)
    
    if not datos['timeline'] and not datos['health'].get('pasos') and not datos['docs']:
        return "El día está vacío, no hay suficientes datos para generar un resumen."
    
    return generar_resumen(fecha, datos)

# --- EJECUCIÓN ---

def procesar_dia(fecha):
    if 'unificar_datos' in sys.modules:
        try:
            print("🔄 Sincronizando...")
            guardar_csv(unificar_datos())
        except: pass

    datos = leer_datos_completos(fecha)
    
    if not datos['timeline'] and not datos['health'].get('pasos'):
        print("⚠️ El día parece vacío.")
    
    resumen = generar_resumen(fecha, datos)

    print("\n📜 RESUMEN GENERADO:")
    print("-" * 50)
    print(resumen)
    print("-" * 50)

    with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
        f.write(f"=== {fecha} ===\n\n{resumen}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 generar_resumenes.py YYYY-MM-DD")
    else:
        procesar_dia(sys.argv[1])

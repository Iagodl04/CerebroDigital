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
    """Lee datos de un día específico del CSV"""
    datos = {
        'health': None,
        'eventos': [],
        'documentos': []
    }
    
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fecha = row.get('fecha', '')
            
            if fecha != fecha_objetivo:
                continue
            
            # Health
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
            
            # Eventos
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
            
            # Documentos
            doc_titulo = row.get('doc_titulo', '').strip()
            if doc_titulo:
                doc = {
                    'titulo': doc_titulo,
                    'filename': row.get('doc_filename', '').strip(),
                    'paginas': row.get('doc_paginas', '').strip(),
                    'content': row.get('doc_content', '').strip()
                }
                if not any(d['titulo'] == doc['titulo'] for d in datos['documentos']):
                    datos['documentos'].append(doc)
    
    return datos

def generar_resumen_dia(fecha, datos):
    """Genera resumen natural y humano"""
    
    tiene_eventos = len(datos['eventos']) > 0
    tiene_docs = len(datos['documentos']) > 0
    tiene_health = datos['health'] is not None
    
    # Construir contexto detallado
    contexto = f"FECHA: {fecha}\n\n"
    
    if tiene_eventos:
        contexto += "EVENTOS DEL DIA:\n"
        for ev in datos['eventos']:
            contexto += f"- {ev['titulo']}\n"
            if ev['ubicacion'] and ev['ubicacion'] != 'no tiene':
                contexto += f"  Ubicacion: {ev['ubicacion']}\n"
            if ev['descripcion'] and ev['descripcion'] != 'no tiene':
                contexto += f"  Descripcion: {ev['descripcion']}\n"
        contexto += "\n"
    
    if tiene_docs:
        contexto += "DOCUMENTOS CONSULTADOS:\n"
        for doc in datos['documentos']:
            contexto += f"- Titulo: {doc['titulo']}\n"
            if doc['content']:
                contexto += f"  Contenido: {doc['content'][:400]}\n"
        contexto += "\n"
    
    if tiene_health:
        h = datos['health']
        contexto += "ACTIVIDAD FISICA:\n"
        contexto += f"- Pasos: {h['pasos']:,}\n"
        contexto += f"- Distancia: {h['distancia_km']} km\n"
        if h['ejercicio_min'] > 5:
            contexto += f"- Ejercicio: {h['ejercicio_min']} minutos\n"
        if h['horas_sueno'] > 0.5:
            contexto += f"- Sueno: {h['horas_sueno']} horas\n"
    
    # Prompt para estilo natural
    prompt = f"""Genera un resumen natural y humano del dia {fecha} basandote EXCLUSIVAMENTE en estos datos:

{contexto}

ESTILO Y FORMATO:
1. Usa un lenguaje natural, como si fuera un diario personal
2. Que parezca escrito por un humano
3. Mas adelante te pondre unos ejemplos pero tampoco quiero que lo hagas exactamente igual que estos, pero si basandote en la estructura
4. No esribas redundancias
5. Para cada documento: Resume su contenido en alrededor de 40 palabras basandote en el texto del contenido
6. Conecta las partes de forma fluida
7. Si el dia no corresponde a hoy hablame en pasado
8. Importante hablarle en segunda perosna 

EJEMPLOS:

Si SOLO hay evento y nada mas:
"El dia (dia que toque) unicamente anotaste que se celebro el evento (event_title) de (hora_ini) a (hora_fin)." (y si hay mas de un evento en un mismo dia pues lo concatenas tambien)

Si hay actividad + documentos:
"El dia (dia que toque) se realizo la actividad con un total de X pasos y una distancia recorrida de X, y se consultaron los documentos (y aqui escribes los documentos que hay con su correspondida descripcion) 

Si hay eventos + actividad + documentos: haces algo con sentido teniendo en cuenta lo de arriba

REGLAS CRITICAS:
- NO menciones datos que NO aparecen arriba
- Si no hay ACTIVIDAD FISICA arriba, NO la menciones
- Si no hay DOCUMENTOS arriba, NO los menciones  
- Resume cada documento basandote en su contenido real
- Si hay documento importante la descripcion del content, en alrededor de 40 paginas

Genera el resumen:"""
    
    data_request = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.15,
            "top_p": 0.7,
            "num_predict": 150
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=data_request, timeout=180)
        response.raise_for_status()
        resumen = response.json()["response"].strip()
        
        # Validacion post-procesamiento
        palabras_prohibidas = []
        if not tiene_docs:
            palabras_prohibidas.extend(['documento', 'consultaron', 'subiste'])
        if not tiene_health:
            palabras_prohibidas.extend(['pasos', 'distancia', 'actividad fisica'])
        
        # Si menciona cosas que no existen, generar respuesta simple
        if any(palabra in resumen.lower() for palabra in palabras_prohibidas):
            if tiene_eventos and not tiene_docs and not tiene_health:
                evento_nombre = datos['eventos'][0]['titulo']
                return f"El dia {fecha} unicamente anotaste que se celebro el cumpleanos de {evento_nombre.replace('cumpleanos', '').replace('cumpleaños', '').strip().title()}."
        
        return resumen
        
    except Exception as e:
        return f"Error: {str(e)}"

def procesar_dia(fecha):
    """Procesa un día específico"""
    
    print(f"Buscando datos del {fecha}...\n")
    datos = leer_datos_dia(fecha)
    
    tiene_health = datos['health'] is not None
    tiene_eventos = len(datos['eventos']) > 0
    tiene_docs = len(datos['documentos']) > 0
    
    if not (tiene_health or tiene_eventos or tiene_docs):
        print(f"No hay datos para el dia {fecha}")
        return
    
    print("Datos encontrados:")
    if tiene_health:
        print(f"  Actividad: {datos['health']['pasos']:,} pasos")
    else:
        print(f"  Sin actividad fisica")
    
    if tiene_eventos:
        print(f"  Eventos: {len(datos['eventos'])}")
        for ev in datos['eventos']:
            print(f"    - {ev['titulo']}")
    else:
        print(f"  Sin eventos")
    
    if tiene_docs:
        print(f"  Documentos: {len(datos['documentos'])}")
        for doc in datos['documentos']:
            print(f"    - {doc['titulo']}")
    else:
        print(f"  Sin documentos")
    
    print(f"\nGenerando resumen natural...\n")
    resumen = generar_resumen_dia(fecha, datos)
    
    with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
        f.write(f"=== RESUMEN DEL DIA {fecha} ===\n")
        f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"{resumen}\n")
    
    print("RESUMEN GENERADO:")
    print(f"\n{resumen}\n")
    print(f"Guardado en: {OUTPUT_TXT}")

if __name__ == "__main__":
    import os
    
    if not os.path.exists(INPUT_CSV):
        print(f"Error: No se encuentra {INPUT_CSV}")
        exit(1)
    
    if len(sys.argv) < 2:
        print("Uso: python3 generar_resumenes.py 2025-11-06")
        exit(1)
    
    fecha = sys.argv[1]
    
    try:
        datetime.strptime(fecha, '%Y-%m-%d')
    except ValueError:
        print("Formato incorrecto. Usa: YYYY-MM-DD")
        exit(1)
    
    procesar_dia(fecha)

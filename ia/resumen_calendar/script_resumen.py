#!/usr/bin/env python3
import csv
import requests
import json
import os
from datetime import datetime

# Configuración de Ollama (puerto correcto 11435)
OLLAMA_URL = "http://localhost:11435/api/generate"
MODEL = "gemma2:2b"

def generar_resumen(evento):
    """Genera un resumen del evento usando TinyDolphin en formato narrativo"""
    titulo = evento.get('Titulo', 'Sin título')
    ubicacion = evento.get('Ubicacion', 'no tiene')
    descripcion = evento.get('Descripcion', 'no tiene')
    dia = evento.get('Dia', 'Sin fecha')
    inicio = evento.get('Inicio', '00:00')
    fin = evento.get('Fin', '00:00')
    
    # Crear prompt específico para el formato deseado
    prompt = f"""Genera un resumen narrativo de este evento de calendario en una sola frase:
Título: {titulo}
Fecha: {dia}
Horario: {inicio} a {fin}
Ubicación: {ubicacion}
Descripción: {descripcion}

El resumen debe seguir este formato: "El día [fecha], tuviste el evento [título] de las [hora inicio] a las [hora fin]". Si tiene ubicación (diferente de "no tiene"), añade "en [ubicación]". Si tiene descripción (diferente de "no tiene"), añade información relevante al final."""
    
    data = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=data, timeout=60)
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception as e:
        return f"Error: {str(e)}"

def procesar_csv(archivo_entrada, archivo_salida_txt):
    """Procesa el CSV y genera resúmenes en formato texto"""
    
    with open(archivo_entrada, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        eventos = list(reader)
    
    print(f"Procesando {len(eventos)} eventos...")
    
    # Abrir archivo de salida para escribir los resúmenes
    with open(archivo_salida_txt, 'w', encoding='utf-8') as out:
        out.write(f"=== RESÚMENES DE EVENTOS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
        
        for i, evento in enumerate(eventos, 1):
            titulo = evento.get('Titulo', 'Sin título')
            
            print(f"[{i}/{len(eventos)}] Generando resumen para: {titulo}...")
            resumen = generar_resumen(evento)
            
            # Escribir solo el resumen
            out.write(f"{resumen}\n\n")
            
            print(f"  ✓ Completado")
    
    print(f"\n✓ Resúmenes guardados en: {archivo_salida_txt}")

if __name__ == "__main__":
    # Rutas relativas desde ia/resumen_calendar/
    archivo_entrada = "../../calendar/data/eventos_limpios.csv"
    archivo_salida_txt = "resumenes_eventos.txt"
    
    # Verificar que existe el archivo de entrada
    if not os.path.exists(archivo_entrada):
        print(f"Error: No se encuentra {archivo_entrada}")
        exit(1)
    
    procesar_csv(archivo_entrada, archivo_salida_txt)

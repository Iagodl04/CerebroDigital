#!/usr/bin/env python3
import csv
import requests
import json
import os
import subprocess
from datetime import datetime

# Configuración de Ollama
OLLAMA_URL = "http://localhost:11435/api/generate"
MODEL = "gemma2:2b"

# Rutas
CSV_PAPERLESS = "../../paperless/documentos_paperless.csv"
OUTPUT_TXT = "./resumenes_documentos.txt"

def exportar_documentos():
    """Ejecuta el script de exportación para obtener CSV actualizado"""
    print("📥 Exportando documentos de Paperless...")
    script_path = "../../paperless/exportar_documentos.py"
    try:
        subprocess.run(['python3', script_path], check=True, cwd='../../paperless')
        print("✅ Documentos exportados")
    except Exception as e:
        print(f"⚠️ Error al exportar: {e}")

def generar_resumen(documento):
    """Genera un resumen del documento usando Gemma 2:2b"""
    titulo = documento.get('title', 'Sin título')
    fecha_subida = documento.get('modified', 'Fecha desconocida')[:10]  # Solo YYYY-MM-DD
    nombre_archivo = documento.get('filename', 'Sin nombre')
    content = documento.get('content', 'Sin contenido disponible')
    
    # Extraer extensión del archivo
    extension = nombre_archivo.split('.')[-1] if '.' in nombre_archivo else 'desconocido'
    
    # Crear prompt para el resumen muy corto
    prompt = f"""Resume en una sola frase muy corta (maximo 40 palabras) de qué trata este documento:

Título: {titulo}
Contenido: {content[:500]}

Responde SOLO con el resumen, sin introducción ni explicaciones adicionales."""
    
    data = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=data, timeout=120)
        response.raise_for_status()
        resumen_corto = response.json()["response"].strip()
        
        # Generar frase completa
        frase = f"Subiste el archivo {titulo} en formato {extension} el día {fecha_subida}, y trata sobre {resumen_corto}"
        return frase
        
    except Exception as e:
        return f"Subiste el archivo {titulo} en formato {extension} el día {fecha_subida}. Error al generar resumen: {str(e)}"

def procesar_documentos(archivo_csv, archivo_salida):
    """Procesa el CSV de documentos y genera resúmenes"""
    
    # Leer CSV
    with open(archivo_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        documentos = list(reader)
    
    print(f"\n📊 Procesando {len(documentos)} documentos...")
    
    # Escribir resúmenes
    with open(archivo_salida, 'w', encoding='utf-8') as out:
        out.write(f"=== RESÚMENES DE DOCUMENTOS PAPERLESS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
        
        for i, doc in enumerate(documentos, 1):
            titulo = doc.get('title', 'Sin título')
            
            print(f"[{i}/{len(documentos)}] Generando resumen para: {titulo}...")
            resumen = generar_resumen(doc)
            
            # Escribir resumen
            out.write(f"{resumen}\n\n")
            
            print(f"  ✓ Completado")
    
    print(f"\n✅ Resúmenes guardados en: {archivo_salida}")
    print(f"📈 Total procesado: {len(documentos)} documentos")

if __name__ == "__main__":
    # Paso 1: Exportar documentos actualizados de Paperless
    exportar_documentos()
    
    # Paso 2: Verificar que existe el CSV
    if not os.path.exists(CSV_PAPERLESS):
        print(f"❌ Error: No se encuentra {CSV_PAPERLESS}")
        exit(1)
    
    # Paso 3: Procesar y generar resúmenes
    procesar_documentos(CSV_PAPERLESS, OUTPUT_TXT)

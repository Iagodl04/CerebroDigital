#!/usr/bin/env python3
import csv
import json
from datetime import datetime
from collections import defaultdict

# Rutas de archivos
CALENDAR_CSV = "../../calendar/data/eventos_limpios.csv"
PAPERLESS_CSV = "../../paperless/documentos_paperless.csv"
HEALTH_CSV = "../resumen_health/health_daily.csv"
OUTPUT_CSV = "./datos_unificados.csv"

def cargar_eventos():
    """Carga eventos del calendario agrupados por fecha"""
    eventos_por_fecha = defaultdict(list)
    
    with open(CALENDAR_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dia = row.get('Dia', '')
            if dia:
                # Convertir DD-MM-YYYY a YYYY-MM-DD
                try:
                    fecha_obj = datetime.strptime(dia, '%d-%m-%Y')
                    fecha_std = fecha_obj.strftime('%Y-%m-%d')
                    
                    evento = {
                        'titulo': row.get('Titulo', ''),
                        'ubicacion': row.get('Ubicacion', ''),
                        'descripcion': row.get('Descripcion', ''),
                        'inicio': row.get('Inicio', ''),
                        'fin': row.get('Fin', '')
                    }
                    eventos_por_fecha[fecha_std].append(evento)
                except ValueError:
                    continue
    
    return eventos_por_fecha

def cargar_documentos():
    """Carga documentos de Paperless agrupados por fecha"""
    docs_por_fecha = defaultdict(list)
    
    with open(PAPERLESS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            modified = row.get('modified', '')
            if modified:
                # Extraer solo YYYY-MM-DD
                try:
                    fecha_std = modified.split(' ')[0]
                    
                    doc = {
                        'id': row.get('id', ''),
                        'titulo': row.get('title', ''),
                        'filename': row.get('filename', ''),
                        'paginas': row.get('page_count', ''),
                        'content_preview': row.get('content', '')  # Solo primeros 100 chars
                    }
                    docs_por_fecha[fecha_std].append(doc)
                except:
                    continue
    
    return docs_por_fecha

def cargar_health():
    """Carga datos de salud por fecha"""
    health_por_fecha = {}
    
    with open(HEALTH_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fecha = row.get('fecha', '')
            if fecha:
                health_por_fecha[fecha] = {
                    'pasos': row.get('pasos', '0'),
                    'distancia_km': row.get('distancia_km', '0'),
                    'ejercicio_min': row.get('ejercicio_min', '0'),
                    'horas_sueno': row.get('horas_sueno', '0'),
                    'calorias': row.get('calorias', '0')
                }
    
    return health_por_fecha

def unificar_datos():
    """Unifica todos los datos por fecha"""
    print("📅 Cargando eventos del calendario...")
    eventos = cargar_eventos()
    
    print("📄 Cargando documentos de Paperless...")
    documentos = cargar_documentos()
    
    print("💪 Cargando datos de salud...")
    health = cargar_health()
    
    # Obtener todas las fechas únicas
    todas_fechas = set()
    todas_fechas.update(eventos.keys())
    todas_fechas.update(documentos.keys())
    todas_fechas.update(health.keys())
    
    # Crear lista unificada
    datos_unificados = []
    
    for fecha in sorted(todas_fechas):
        # Datos de salud (siempre hay como máximo 1 por día)
        health_data = health.get(fecha, {})
        
        # Eventos (puede haber múltiples)
        eventos_dia = eventos.get(fecha, [])
        
        # Documentos (puede haber múltiples)
        docs_dia = documentos.get(fecha, [])
        
        # Si hay eventos o documentos, crear una fila por cada uno
        # Si no hay ninguno, crear una fila solo con health
        if not eventos_dia and not docs_dia:
            # Solo health
            datos_unificados.append({
                'fecha': fecha,
                'pasos': health_data.get('pasos', '0'),
                'distancia_km': health_data.get('distancia_km', '0'),
                'ejercicio_min': health_data.get('ejercicio_min', '0'),
                'horas_sueno': health_data.get('horas_sueno', '0'),
                'calorias': health_data.get('calorias', '0'),
                'evento_titulo': '',
                'evento_ubicacion': '',
                'evento_descripcion': '',
                'evento_hora_inicio': '',
                'evento_hora_fin': '',
                'doc_id': '',
                'doc_titulo': '',
                'doc_filename': '',
                'doc_paginas': '',
                'doc_content_preview': ''
            })
        else:
            # Combinar eventos y documentos
            max_items = max(len(eventos_dia), len(docs_dia))
            
            for i in range(max_items):
                evento = eventos_dia[i] if i < len(eventos_dia) else {}
                doc = docs_dia[i] if i < len(docs_dia) else {}
                
                datos_unificados.append({
                    'fecha': fecha,
                    'pasos': health_data.get('pasos', '0'),
                    'distancia_km': health_data.get('distancia_km', '0'),
                    'ejercicio_min': health_data.get('ejercicio_min', '0'),
                    'horas_sueno': health_data.get('horas_sueno', '0'),
                    'calorias': health_data.get('calorias', '0'),
                    'evento_titulo': evento.get('titulo', ''),
                    'evento_ubicacion': evento.get('ubicacion', ''),
                    'evento_descripcion': evento.get('descripcion', ''),
                    'evento_hora_inicio': evento.get('inicio', ''),
                    'evento_hora_fin': evento.get('fin', ''),
                    'doc_id': doc.get('id', ''),
                    'doc_titulo': doc.get('titulo', ''),
                    'doc_filename': doc.get('filename', ''),
                    'doc_paginas': doc.get('paginas', ''),
                    'doc_content_preview': doc.get('content_preview', '')
                })
    
    return datos_unificados

def guardar_csv(datos):
    """Guarda los datos unificados en CSV"""
    print(f"\n💾 Guardando datos unificados...")
    
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        fieldnames = [
            'fecha',
            'pasos', 'distancia_km', 'ejercicio_min', 'horas_sueno', 'calorias',
            'evento_titulo', 'evento_ubicacion', 'evento_descripcion', 
            'evento_hora_inicio', 'evento_hora_fin',
            'doc_id', 'doc_titulo', 'doc_filename', 'doc_paginas', 'doc_content_preview'
        ]
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(datos)
    
    print(f"✅ Datos guardados en: {OUTPUT_CSV}")
    print(f"📊 Total de registros: {len(datos)}")

if __name__ == "__main__":
    import os
    
    # Verificar que existen los archivos
    archivos = [
        (CALENDAR_CSV, "eventos del calendario"),
        (PAPERLESS_CSV, "documentos de Paperless"),
        (HEALTH_CSV, "datos de salud")
    ]
    
    for archivo, nombre in archivos:
        if not os.path.exists(archivo):
            print(f"⚠️ Advertencia: No se encuentra {nombre} en {archivo}")
    
    print("🚀 Unificando datos...\n")
    datos_unificados = unificar_datos()
    guardar_csv(datos_unificados)
    
    print("\n📈 Estadísticas:")
    fechas_con_health = sum(1 for d in datos_unificados if int(d.get('pasos', 0)) > 0)
    fechas_con_eventos = sum(1 for d in datos_unificados if d.get('evento_titulo', ''))
    fechas_con_docs = sum(1 for d in datos_unificados if d.get('doc_titulo', ''))
    
    print(f"   Días con datos de salud: {fechas_con_health}")
    print(f"   Eventos de calendario: {fechas_con_eventos}")
    print(f"   Documentos: {fechas_con_docs}")

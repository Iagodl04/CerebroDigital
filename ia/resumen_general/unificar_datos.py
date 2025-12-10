#!/usr/bin/env python3
import csv
import os
import re
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# --- CONFIGURACIÓ ---
# Ajusta estas rutas si es necesario, uso rutas relativas basadas en tu estructura
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CALENDAR_CSV = os.path.abspath(os.path.join(BASE_DIR, "../../calendar/data/eventos_limpios.csv"))
PAPERLESS_CSV = os.path.abspath(os.path.join(BASE_DIR, "../../paperless/documentos_paperless.csv"))
HEALTH_CSV = os.path.abspath(os.path.join(BASE_DIR, "../resumen_health/health_daily.csv"))
OUTPUT_CSV = os.path.join(BASE_DIR, "datos_unificados.csv")
FOTOS_ROOT = Path("/home/piQuique/ptiProject/fotos_immich/admin") 

# --- FUNCIONS DE CÀRREGA ---

def cargar_eventos():
    eventos_por_fecha = defaultdict(list)
    if not os.path.exists(CALENDAR_CSV): return eventos_por_fecha
    with open(CALENDAR_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dia = row.get('Dia', '')
            if dia:
                try:
                    fecha_obj = datetime.strptime(dia, '%d-%m-%Y')
                    fecha_std = fecha_obj.strftime('%Y-%m-%d')
                    eventos_por_fecha[fecha_std].append({
                        'titulo': row.get('Titulo', ''),
                        'ubicacion': row.get('Ubicacion', ''),
                        'descripcion': row.get('Descripcion', ''),
                        'inicio': row.get('Inicio', ''),
                        'fin': row.get('Fin', '')
                    })
                except ValueError: continue
    return eventos_por_fecha

def cargar_documentos():
    docs_por_fecha = defaultdict(list)
    if not os.path.exists(PAPERLESS_CSV): return docs_por_fecha
    with open(PAPERLESS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            modified = row.get('modified', '')
            if modified:
                try:
                    fecha_std = modified.split(' ')[0]
                    docs_por_fecha[fecha_std].append({
                        'id': row.get('id', ''),
                        'titulo': row.get('title', ''),
                        'filename': row.get('filename', ''),
                        'paginas': row.get('page_count', '')
                        # ELIMINADO: content_preview
                    })
                except: continue
    return docs_por_fecha

def cargar_health():
    health_por_fecha = {}
    if not os.path.exists(HEALTH_CSV): return health_por_fecha
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

def obtener_info_archivo(filepath):
    nombre = filepath.name
    hora = "00:00"
    match = re.search(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', nombre)
    if match:
        hora = f"{match.group(4)}:{match.group(5)}"
    else:
        try:
            ts = os.path.getmtime(filepath)
            dt = datetime.fromtimestamp(ts)
            hora = dt.strftime('%H:%M')
        except: pass
    return hora, nombre

def cargar_fotos():
    print(f"   ...buscant fotos a {FOTOS_ROOT}")
    fotos_por_fecha = {} 
    if not FOTOS_ROOT.exists(): return fotos_por_fecha

    for any_dir in FOTOS_ROOT.iterdir():
        if any_dir.is_dir() and any_dir.name.isdigit():
            for dia_dir in any_dir.iterdir():
                try:
                    datetime.strptime(dia_dir.name, '%Y-%m-%d')
                    fecha_str = dia_dir.name
                    archivos = [f for f in dia_dir.glob('*') if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.heic', '.webp', '.mp4']]
                    if archivos:
                        datos_imgs = [obtener_info_archivo(f) for f in archivos]
                        datos_imgs.sort(key=lambda x: x[0])
                        horas = [x[0] for x in datos_imgs]
                        nombres = [x[1] for x in datos_imgs]
                        fotos_por_fecha[fecha_str] = {
                            'count': len(archivos),
                            'inicio': horas[0],
                            'fin': horas[-1],
                            'nombres': "; ".join(nombres)
                        }
                except ValueError: continue 
    return fotos_por_fecha

def unificar_datos():
    print("📅 Calendario...")
    eventos = cargar_eventos()
    print("📄 Paperless...")
    documentos = cargar_documentos()
    print("💪 Health...")
    health = cargar_health()
    print("📸 Fotos...")
    fotos = cargar_fotos()

    todas_fechas = set()
    todas_fechas.update(eventos.keys())
    todas_fechas.update(documentos.keys())
    todas_fechas.update(health.keys())
    todas_fechas.update(fotos.keys())

    datos_unificados = []

    for fecha in sorted(todas_fechas):
        h_data = health.get(fecha, {})
        ev_dia = eventos.get(fecha, [])
        doc_dia = documentos.get(fecha, [])
        f_data = fotos.get(fecha, {'count': 0, 'inicio': '', 'fin': '', 'nombres': ''})

        max_items = max(len(ev_dia), len(doc_dia))
        if max_items == 0: max_items = 1

        for i in range(max_items):
            ev = ev_dia[i] if i < len(ev_dia) else {}
            doc = doc_dia[i] if i < len(doc_dia) else {}

            row = {
                'fecha': fecha,
                # Health
                'pasos': h_data.get('pasos', '0'),
                'distancia_km': h_data.get('distancia_km', '0'),
                'ejercicio_min': h_data.get('ejercicio_min', '0'),
                'horas_sueno': h_data.get('horas_sueno', '0'),
                'calorias': h_data.get('calorias', '0'),
                # Fotos
                'fotos_cantidad': f_data['count'],
                'fotos_hora_inicio': f_data['inicio'],
                'fotos_hora_fin': f_data['fin'],
                'fotos_nombres': f_data['nombres'],
                # Events
                'evento_titulo': ev.get('titulo', ''),
                'evento_ubicacion': ev.get('ubicacion', ''),
                'evento_descripcion': ev.get('descripcion', ''),
                'evento_hora_inicio': ev.get('inicio', ''),
                'evento_hora_fin': ev.get('fin', ''),
                # Docs (SIN CONTENT)
                'doc_id': doc.get('id', ''),
                'doc_titulo': doc.get('titulo', ''),
                'doc_filename': doc.get('filename', ''),
                'doc_paginas': doc.get('paginas', '')
            }
            datos_unificados.append(row)

    return datos_unificados

def guardar_csv(datos):
    print(f"\n💾 Guardando datos...")
    fieldnames = [
        'fecha',
        'pasos', 'distancia_km', 'ejercicio_min', 'horas_sueno', 'calorias',
        'fotos_cantidad', 'fotos_hora_inicio', 'fotos_hora_fin', 'fotos_nombres',
        'evento_titulo', 'evento_ubicacion', 'evento_descripcion',
        'evento_hora_inicio', 'evento_hora_fin',
        'doc_id', 'doc_titulo', 'doc_filename', 'doc_paginas' # SIN PREVIEW
    ]

    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(datos)

    print(f"✅ CSV guardado: {OUTPUT_CSV}")
    print(f"📊 Registros totales: {len(datos)}")

if __name__ == "__main__":
    datos = unificar_datos()
    guardar_csv(datos)

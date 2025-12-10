#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
import csv

def parse_datetime(line):
    """
    Analiza una línea DTSTART o DTEND para extraer día y hora.
    """
    
    # Lógica para "Todo el dia" (ej: DTSTART;VALUE=DATE:20251107)
    match_date = re.search(r'VALUE=DATE:(\d{4})(\d{2})(\d{2})', line)
    if match_date:
        year, month, day = match_date.groups()
        dia_fmt = f"{day}-{month}-{year}"
        # Devuelve 00:00 y 24:00 como pediste
        return dia_fmt, "00:00", "24:00" 

    # Lógica para "Tiene hora" (ej: DTSTART;TZID=...:20251114T100000)
    match_time = re.search(r':(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})', line)
    if match_time:
        year, month, day, hour, minute, second = match_time.groups()
        dia_fmt = f"{day}-{month}-{year}"
        hora_fmt = f"{hour}:{minute}"
        # Devuelve día y hora, el fin se calcula por separado
        return dia_fmt, hora_fmt, None 
        
    return None, None, None

def get_field(ical_text, field):
    """
    Extrae un campo simple como SUMMARY o LOCATION.
    Busca el texto entre 'CAMPO:' y el siguiente salto de línea (\r\n).
    """
    # El formato iCalendar usa \r\n (CHAR(13) + CHAR(10)) como fin de línea
    match = re.search(fr'{field}:(.*?)\r\n', ical_text, re.DOTALL)
    if match:
        # Limpia el valor de saltos de línea escapados (\\n) y espacios
        return match.group(1).replace('\\n', ' ').strip()
    return "no tiene"

def main():
    # 1. Preparamos el archivo CSV de salida (lo imprimirá en la terminal)
    writer = csv.writer(sys.stdout)
    writer.writerow(['Titulo', 'Ubicacion', 'Descripcion', 'Dia', 'Inicio', 'Fin'])
    
    # 2. Leemos los datos crudos de SQLite que vienen del script .sh
    stdin_data = sys.stdin.read()
    
    # 3. Separamos cada evento (usando el separador especial)
    eventos_ical = stdin_data.split('---EVENTO---')

    # 4. Procesamos cada evento
    for ical in eventos_ical:
        if not ical.strip():
            continue
            
        titulo = get_field(ical, 'SUMMARY')
        ubicacion = get_field(ical, 'LOCATION')
        descripcion = get_field(ical, 'DESCRIPTION')
        
        # Obtenemos la LÍNEA entera de DTSTART y DTEND
        dtstart_line_match = re.search(r'DTSTART(.*?)\r\n', ical)
        dtend_line_match = re.search(r'DTEND(.*?)\r\n', ical)
        
        dtstart_line = dtstart_line_match.group(0) if dtstart_line_match else "no tiene"
        dtend_line = dtend_line_match.group(0) if dtend_line_match else "no tiene"

        if dtstart_line == "no tiene":
            continue # Si no tiene fecha de inicio, lo saltamos

        # 5. Analizamos la línea de inicio
        dia, inicio, fin_allday = parse_datetime(dtstart_line)
        
        if fin_allday:
            # Es "Todo el dia"
            fin = fin_allday
        elif dtend_line != "no tiene":
            # Es "Tiene hora", analizamos la línea de fin
            _, fin_time, _ = parse_datetime(dtend_line)
            fin = fin_time if fin_time else "Error"
        else:
            fin = "no tiene"
            
        if dia: # Solo escribimos si pudimos analizar la fecha
            # 6. Escribimos la fila final en el CSV
            writer.writerow([titulo, ubicacion, descripcion, dia, inicio, fin])

if __name__ == "__main__":
    main()

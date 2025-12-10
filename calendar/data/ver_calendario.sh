#!/bin/bash

# Define la ubicación exacta de la base de datos
DB_PATH="/home/piQuique/ptiProject/calendar/docker/nextcloud_data/data/owncloud.db"

echo "--- 📅 Eventos ACTIVOS (Consulta Corregida v2) ---"
echo "----------------------------------------------------"

# Ejecuta sqlite3 con sudo para garantizar permisos de lectura
sudo sqlite3 "$DB_PATH" <<SQL
.headers off
.mode list
.separator " | "
SELECT
    -- 1. ID
    'ID: ' || o.id,
    
    -- 2. Título (SUMMARY)
    'Titulo: ' || CASE 
      WHEN INSTR(o.calendardata, 'SUMMARY:') > 0 
      THEN TRIM(SUBSTR(
             o.calendardata, 
             INSTR(o.calendardata, 'SUMMARY:') + 8, 
             INSTR(SUBSTR(o.calendardata, INSTR(o.calendardata, 'SUMMARY:') + 8), CHAR(13)) - 1
           ))
      ELSE 'no tiene' 
    END,
    
    -- 3. Ubicación (LOCATION)
    'Ubicacion: ' || CASE 
      WHEN INSTR(o.calendardata, 'LOCATION:') > 0 
      THEN TRIM(SUBSTR(
             o.calendardata, 
             INSTR(o.calendardata, 'LOCATION:') + 9, 
             INSTR(SUBSTR(o.calendardata, INSTR(o.calendardata, 'LOCATION:') + 9), CHAR(13)) - 1
           ))
      ELSE 'no tiene' 
    END,
    
    -- 4. Descripción (DESCRIPTION)
    'Descripcion: ' || CASE 
      WHEN INSTR(o.calendardata, 'DESCRIPTION:') > 0 
      THEN TRIM(SUBSTR(
             o.calendardata, 
             INSTR(o.calendardata, 'DESCRIPTION:') + 12, 
             INSTR(SUBSTR(o.calendardata, INSTR(o.calendardata, 'DESCRIPTION:') + 12), CHAR(13)) - 1
           ))
      ELSE 'no tiene' 
    END,

    -- 5. Inicio (DTSTART)
    'Inicio: ' || CASE 
      WHEN INSTR(o.calendardata, 'DTSTART') > 0 
      THEN TRIM(SUBSTR(
             o.calendardata, 
             INSTR(o.calendardata, 'DTSTART'), 
             INSTR(SUBSTR(o.calendardata, INSTR(o.calendardata, 'DTSTART')), CHAR(13)) - 1
           ))
      ELSE 'no tiene' 
    END,

    -- 6. Fin (DTEND)
    'Fin: ' || CASE 
      WHEN INSTR(o.calendardata, 'DTEND') > 0 
      THEN TRIM(SUBSTR(
             o.calendardata, 
             INSTR(o.calendardata, 'DTEND'), 
             INSTR(SUBSTR(o.calendardata, INSTR(o.calendardata, 'DTEND')), CHAR(13)) - 1
           ))
      ELSE 'no tiene' 
    END,

    -- 7. Tipo de Duración (LÓGICA CORREGIDA USANDO INSTR)
    CASE 
      WHEN INSTR(o.calendardata, 'DTSTART;VALUE=DATE') > 0 THEN 'Tipo: Todo el dia' 
      ELSE 'Tipo: Tiene hora' 
    END
FROM
    oc_calendarobjects o
WHERE
    o.uri NOT LIKE '%-deleted.ics'
    AND o.calendardata NOT LIKE '%STATUS:CANCELLED%'
ORDER BY
    o.firstoccurence;
SQL
echo "----------------------------------------------------"

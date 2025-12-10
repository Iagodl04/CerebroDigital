#!/bin/bash

# Define la ubicación exacta de la base de datos
DB_PATH="/home/piQuique/ptiProject/calendar/docker/nextcloud_data/data/owncloud.db"
# Ubicación del script de Python
PYTHON_SCRIPT="/home/piQuique/ptiProject/calendar/data/parsear_calendario.py"

# 1. Ejecutamos la consulta de SQLite (SIN SUDO)
# El usuario piQuique ya debería tener permisos
DATOS_CRUDOS=$(sqlite3 "$DB_PATH" <<SQL
.headers off
.mode list
SELECT
    calendardata || '---EVENTO---'
FROM
    oc_calendarobjects
WHERE
    uri NOT LIKE '%-deleted.ics'
    AND calendardata NOT LIKE '%STATUS:CANCELLED%';
SQL
)

# 2. Pasamos los datos crudos al script de Python
echo "$DATOS_CRUDOS" | python3 "$PYTHON_SCRIPT" > eventos_limpios.csv

# 3. Este script ya no imprime "¡Éxito!" para que la API no se confunda

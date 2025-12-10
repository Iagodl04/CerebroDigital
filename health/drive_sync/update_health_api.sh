#!/bin/bash

# 1. Define la ruta base y ve a ella
# Es vital porque tu script 'export_all_health_data.py' usa rutas relativas
BASE_DIR="/home/piQuique/ptiProject/health"
cd $BASE_DIR

echo "--- Actualización de Health API iniciada $(date) ---"

# 2. Ejecuta TU script de Python para crear el JSON
# Asumo que usas 'python3'
python3 $BASE_DIR/export_all_health_data.py

if [ $? -eq 0 ]; then
    echo "health_data.json actualizado con éxito por tu script."
    
    # 3. Reinicia el contenedor de Docker para que cargue los nuevos datos
    echo "Reiniciando contenedor health-api-container..."
    docker restart health-api-container
    
    echo "Contenedor reiniciado. Proceso completado."
else
    echo "ERROR: Falla al ejecutar export_all_health_data.py"
fi
echo "------------------------------------------------"


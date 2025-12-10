#!/bin/bash
set -e

# === CONFIGURACIÓN ===
FOLDER_URL="https://drive.google.com/drive/folders/1D8molqIbHCpAMay6iHwvExBIpGzUmUwf"
DEST_DIR="/home/piQuique/ptiProject/health/drive_sync"
LOG_FILE="/home/piQuique/ptiProject/health/drive_sync.log"

echo "[$(date)] 🔄 Iniciando sincronización de carpeta Drive..." | tee -a "$LOG_FILE"

# Crear carpeta destino si no existe
mkdir -p "$DEST_DIR"

# Descargar TODO lo que haya en la carpeta Drive
gdown --folder "$FOLDER_URL" -O "$DEST_DIR" --remaining-ok | tee -a "$LOG_FILE"

echo "[$(date)] ✅ Sincronización completa. Archivos descargados en: $DEST_DIR" | tee -a "$LOG_FILE"


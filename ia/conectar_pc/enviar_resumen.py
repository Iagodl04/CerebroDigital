#!/usr/bin/env python3
import requests
import sys

SERVIDOR_URL = "http://192.168.1.212:5000/generar_resumen"
CSV_PATH = "/home/piQuique/ptiProject/ia/resumen_general/datos_unificados.csv"

def generar_resumen(fecha):
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        csv_content = f.read()
    
    payload = {
        'csv_content': csv_content,
        'fecha': fecha
    }
    
    response = requests.post(SERVIDOR_URL, json=payload, timeout=180)
    
    if response.status_code == 200:
        data = response.json()
        resumen = data['resumen']
        
        # Guardar en archivo
        output_file = f"resumen_{fecha}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"=== DIARIO DEL {fecha} ===\n\n{resumen}\n")
        
        print(f"✅ Resumen generado y guardado en {output_file}")
        print(resumen)
    else:
        print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 enviar_resumen.py YYYY-MM-DD")
        sys.exit(1)
    
    fecha = sys.argv[1]
    generar_resumen(fecha)

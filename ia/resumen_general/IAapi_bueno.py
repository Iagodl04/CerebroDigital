from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Importem els teus scripts (han d'estar a la mateixa carpeta)
try:
    from unificar_datos import unificar_datos, guardar_csv
    from generar_resumenes import obtener_resumen_texto
except ImportError as e:
    print(f"ERROR CRÍTIC: No es poden importar els scripts: {e}")

app = FastAPI()

# Permetre que la teva web (index.html) es connecti des de qualsevol origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Cervell Digital Online", "service": "IA Summarizer"}

@app.get("/diario/{fecha}")
def api_generar_resumen(fecha: str):
    print(f"📥 API: Rebuda petició per al dia {fecha}")
    
    # 1. Actualitzar dades al moment (Sincronització)
    try:
        print("   🔄 Unificant dades fresques (calendar, paperless, fotos, health)...")
        nuevos_datos = unificar_datos()
        guardar_csv(nuevos_datos)
    except Exception as e:
        print(f"   ⚠️ Error unificant (usarem dades antigues si n'hi ha): {e}")

    # 2. Generar el text amb IA (Ollama)
    try:
        print("   🧠 Cridant a Ollama per generar la història...")
        resumen = obtener_resumen_texto(fecha)
        return {"fecha": fecha, "resumen": resumen}
    except Exception as e:
        print(f"   ❌ Error IA: {e}")
        raise HTTPException(status_code=500, detail=f"Error generant resum: {str(e)}")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Ajustar path para encontrar los módulos si se ejecuta desde fuera
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from unificar_datos import unificar_datos, guardar_csv
    # Ahora sí existe esta función gracias al cambio anterior:
    from generar_resumenes import obtener_resumen_texto 
except ImportError as e:
    print(f"ERROR CRÍTIC: No es poden importar els scripts: {e}")

app = FastAPI()

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
    
    # 1. Actualitzar dades al moment
    try:
        print("   🔄 Unificant dades fresques...")
        nuevos_datos = unificar_datos()
        guardar_csv(nuevos_datos)
    except Exception as e:
        print(f"   ⚠️ Error unificant (usarem dades antigues): {e}")

    # 2. Generar el text
    try:
        print("   🧠 Cridant a Ollama...")
        # Esta llamada ahora funcionará correctamente
        resumen = obtener_resumen_texto(fecha)
        return {"fecha": fecha, "resumen": resumen}
    except Exception as e:
        print(f"   ❌ Error IA: {e}")
        raise HTTPException(status_code=500, detail=f"Error generant resum: {str(e)}")

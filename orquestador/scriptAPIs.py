import requests
import datetime
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# --- CONFIGURACIÓN ---
OPENWEATHER_API_KEY = "f15a5d04173834ed0474f6ba29e07e7d"
NEWSAPI_KEY = "498fa2b0961a4402a0f31ae0db0a30cf"
CIUDAD = "Barcelona"
PAIS = "es"

# --- TIEMPO ---
def obtener_resumen_tiempo(fecha):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CIUDAD}&appid={OPENWEATHER_API_KEY}&units=metric&lang=es"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            descripcion = data['weather'][0]['description']
            temp_actual = data['main']['temp']
            sensacion = data['main']['feels_like']
            return f"El tiempo en {CIUDAD}: {descripcion}, {temp_actual}°C (sensación {sensacion}°C)."
        else:
            return "No se pudo obtener el estado del tiempo."
    except requests.exceptions.RequestException as e:
        return f"Error de conexión con la API del tiempo: {e}"

# --- NOTICIAS ---
def obtener_titulares_noticias():
    url = f"https://newsapi.org/v2/top-headlines?country={PAIS}&apiKey={NEWSAPI_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            titulares = [a['title'] for a in data['articles'][:3]]
            if titulares:
                return "Titulares de hoy:\n- " + "\n- ".join(titulares)
            else:
                return "No se encontraron noticias destacadas."
        else:
            return "No se pudieron obtener las noticias."
    except requests.exceptions.RequestException as e:
        return f"Error de conexión con la API de noticias: {e}"

# --- PROMPT ---
def construir_prompt_diario(fecha):
    resumen_tiempo = obtener_resumen_tiempo(fecha)
    resumen_noticias = obtener_titulares_noticias()
    resumen_eventos = obtener_eventos_google_calendar(fecha)

    prompt = f"""
Crea un resumen del día {fecha.strftime('%d de %B de %Y')} en formato de diario personal, usando la siguiente información contextual.
Sé un poco reflexivo y conecta las ideas de forma natural.

**Contexto del día:**
- **Clima:** {resumen_tiempo}
- **Actualidad:** {resumen_noticias}
- **Eventos:** {resumen_eventos}

Basándote en esto, escribe una entrada de diario en primera persona.
"""
    return prompt

# --- EJECUCIÓN ---
if __name__ == "__main__":
    fecha_str = input("Introduce la fecha (YYYY-MM-DD) o deja vacío para hoy: ").strip()
    if fecha_str:
        fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
    else:
        fecha = datetime.date.today()

    prompt = construir_prompt_diario(fecha)
    print("\n--- PROMPT GENERADO PARA OLLAMA ---\n")
    print(prompt)

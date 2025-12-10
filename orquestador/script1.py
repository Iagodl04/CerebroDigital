import datetime
import os.path
import requests
import argparse
import sys

# --- CONFIGURACIÓN ---
OPENWEATHER_API_KEY = "f15a5d04173834ed0474f6ba29e07e7d"  # Reemplaza con tu clave
NEWSAPI_KEY = "498fa2b0961a4402a0f31ae0db0a30cf"              # Reemplaza con tu clave

# --- TIEMPO ---
def obtener_resumen_tiempo(ciudad, api_key):
    """Obtiene el resumen del tiempo actual de OpenWeatherMap para una ciudad específica."""
    # NOTA: La API gratuita de OpenWeatherMap solo devuelve el tiempo actual, no datos históricos.
    url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={api_key}&units=metric&lang=es"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        descripcion = data['weather'][0]['description']
        temp_actual = data['main']['temp']
        sensacion = data['main']['feels_like']
        return f"El tiempo en {ciudad.capitalize()}: {descripcion}, {temp_actual:.1f}°C (sensación de {sensacion:.1f}°C)."
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión con la API del tiempo: {e}")
        return "No se pudo obtener el estado del tiempo."
    except KeyError:
        return "Respuesta inesperada de la API del tiempo."

# --- NOTICIAS ---
def obtener_titulares_noticias(pais, api_key):
    """Obtiene los 3 titulares principales de NewsAPI para un país específico."""
    # NOTA: La API de titulares de NewsAPI solo devuelve noticias actuales.
    url = f"https://newsapi.org/v2/top-headlines?country={pais}&apiKey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        titulares = [a['title'] for a in data.get('articles', [])[:3]]
        if titulares:
            return "Titulares de hoy:\n- " + "\n- ".join(titulares)
        else:
            return "No se encontraron noticias destacadas."
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión con la API de noticias: {e}")
        return "No se pudieron obtener las noticias."
    except KeyError:
        return "Respuesta inesperada de la API de noticias."

# --- PROMPT ---
def construir_prompt_diario(fecha, ciudad, pais):
    """Construye el prompt final con toda la información del día."""
    resumen_tiempo = obtener_resumen_tiempo(ciudad, OPENWEATHER_API_KEY)
    resumen_noticias = obtener_titulares_noticias(pais, NEWSAPI_KEY)

    prompt = f"""
Crea un resumen del día {fecha.strftime('%A, %d de %B de %Y')} en formato de diario personal,
usando la siguiente información contextual. Sé un poco reflexivo y conecta las ideas de forma natural.

**Contexto del día:**
- **Clima:** {resumen_tiempo}
- **Actualidad:** {resumen_noticias}

Basándote en esto, ahora escribe una entrada de diario en primera persona que comience con "Querido diario:".
"""
    return prompt

# --- EJECUCIÓN ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Genera un prompt para un diario personal basado en el tiempo y las noticias de un día específico.",
        epilog="Ejemplo de uso:\n"
               "python generador_prompt.py --fecha 2023-10-26 --ciudad Londres --pais gb\n"
               "python generador_prompt.py --ciudad Paris --pais fr"
    )
    parser.add_argument(
        '--fecha', 
        help="La fecha para generar el prompt en formato YYYY-MM-DD. Si no se especifica, se usa el día de hoy."
    )
    parser.add_argument(
        '--ciudad',
        default='Barcelona',
        help="La ciudad para obtener el tiempo. Por defecto: Barcelona."
    )
    parser.add_argument(
        '--pais',
        default='es',
        help="El código de país (2 letras) para las noticias. Por defecto: es."
    )
    
    args = parser.parse_args()
    
    fecha_seleccionada = None
    if args.fecha:
        try:
            fecha_seleccionada = datetime.datetime.strptime(args.fecha, '%Y-%m-%d').date()
        except ValueError:
            print("Error: El formato de la fecha es incorrecto. Por favor, usa YYYY-MM-DD.", file=sys.stderr)
            sys.exit(1)
    else:
        fecha_seleccionada = datetime.date.today()
        
    print(f"--- Generando prompt para el día: {fecha_seleccionada.strftime('%Y-%m-%d')} en {args.ciudad.capitalize()} ({args.pais.upper()}) ---")
    
    prompt_completo = construir_prompt_diario(fecha_seleccionada, args.ciudad, args.pais)
    print("\n--- PROMPT GENERADO PARA OLLAMA ---")
    print(prompt_completo)


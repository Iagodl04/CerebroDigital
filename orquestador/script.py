import datetime
import os.path
# import pickle # Comentado - No es necesario sin Google Calendar
import requests
# from google.auth.transport.requests import Request # Comentado
# from google_auth_oauthlib.flow import InstalledAppFlow # Comentado
# from googleapiclient.discovery import build # Comentado

# --- CONFIGURACIÓN ---
# NOTA: Por seguridad, es mejor guardar estas claves como variables de entorno.
OPENWEATHER_API_KEY = "f15a5d04173834ed0474f6ba29e07e7d"  # Reemplaza con tu clave
NEWSAPI_KEY = "498fa2b0961a4402a0f31ae0db0a30cf"          # Reemplaza con tu clave
CIUDAD = "Barcelona"
PAIS = "es"
# Alcance para la API de Google Calendar (solo lectura)
# SCOPES = ['https://www.googleapis.com/auth/calendar.readonly'] # Comentado

# --- TIEMPO ---
def obtener_resumen_tiempo():
    """Obtiene el resumen del tiempo actual de OpenWeatherMap."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CIUDAD}&appid={OPENWEATHER_API_KEY}&units=metric&lang=es"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanza un error para respuestas 4xx/5xx
        data = response.json()
        descripcion = data['weather'][0]['description']
        temp_actual = data['main']['temp']
        sensacion = data['main']['feels_like']
        return f"El tiempo en {CIUDAD}: {descripcion}, {temp_actual:.1f}°C (sensación de {sensacion:.1f}°C)."
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión con la API del tiempo: {e}")
        return "No se pudo obtener el estado del tiempo."
    except KeyError:
        return "Respuesta inesperada de la API del tiempo."

# --- NOTICIAS ---
def obtener_titulares_noticias():
    """Obtiene los 3 titulares principales de NewsAPI."""
    url = f"https://newsapi.org/v2/top-headlines?country={PAIS}&apiKey={NEWSAPI_KEY}"
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

# --- GOOGLE CALENDAR ---
def obtener_eventos_google_calendar(fecha):
    """Obtiene los eventos del día desde Google Calendar."""
    return "La función de Google Calendar está desactivada."
    # creds = None
    # # El archivo token.pickle almacena los tokens de acceso y refresco del usuario.
    # # Se crea automáticamente la primera vez que se completa la autorización.
    # if os.path.exists('token.pickle'):
    #     with open('token.pickle', 'rb') as token:
    #         creds = pickle.load(token)
            
    # # Si no hay credenciales (válidas), permite que el usuario inicie sesión.
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         try:
    #             creds.refresh(Request())
    #         except Exception as e:
    #             print(f"Error al refrescar el token de Google: {e}")
    #             os.remove('token.pickle') # Borra el token dañado
    #             return "Error de autenticación con Google Calendar. Por favor, vuelve a ejecutar el script."
    #     else:
    #         try:
    #             flow = InstalledAppFlow.from_client_secrets_file(
    #                 'credentials.json', SCOPES)
    #             creds = flow.run_local_server(port=0)
    #         except FileNotFoundError:
    #             return "No se encontró 'credentials.json'. Revisa las instrucciones en README.md."
    #     # Guarda las credenciales para la próxima ejecución
    #     with open('token.pickle', 'wb') as token:
    #         pickle.dump(creds, token)

    # try:
    #     service = build('calendar', 'v3', credentials=creds)

    #     # Configura el rango de tiempo para el día completo
    #     tmin = datetime.datetime.combine(fecha, datetime.time.min).isoformat() + 'Z'
    #     tmax = datetime.datetime.combine(fecha, datetime.time.max).isoformat() + 'Z'

    #     events_result = service.events().list(
    #         calendarId='primary',
    #         timeMin=tmin,
    #         timeMax=tmax,
    #         singleEvents=True,
    #         orderBy='startTime'
    #     ).execute()
    #     events = events_result.get('items', [])

    #     if not events:
    #         return "No hay eventos programados para hoy."

    #     eventos_formateados = []
    #     for event in events:
    #         start = event['start'].get('dateTime', event['start'].get('date'))
    #         # Formatea la hora si es un evento con hora específica
    #         if 'T' in start:
    #             hora = datetime.datetime.fromisoformat(start).strftime('%H:%M')
    #             eventos_formateados.append(f"- {hora}: {event['summary']}")
    #         else: # Evento de día completo
    #             eventos_formateados.append(f"- Todo el día: {event['summary']}")
        
    #     return "Agenda de hoy:\n" + "\n".join(eventos_formateados)

    # except Exception as e:
    #     print(f"Error al conectar con la API de Google Calendar: {e}")
    #     return "No se pudo obtener la agenda de Google Calendar."

# --- PROMPT ---
def construir_prompt_diario(fecha):
    """Construye el prompt final con toda la información del día."""
    resumen_tiempo = obtener_resumen_tiempo()
    resumen_noticias = obtener_titulares_noticias()
    # resumen_eventos = obtener_eventos_google_calendar(fecha) # Comentado

    prompt = f"""
Crea un resumen del día {fecha.strftime('%A, %d de %B de %Y')} en formato de diario personal,
usando la siguiente información contextual. Sé un poco reflexivo y conecta las ideas de forma natural.

**Contexto del día:**
- **Clima:** {resumen_tiempo}
- **Actualidad:** {resumen_noticias}

Basándote en esto, escribe una entrada de diario en primera persona que comience con "Querido diario:".
"""
    return prompt

# --- EJECUCIÓN ---
if __name__ == '__main__':
    fecha_hoy = datetime.date.today()
    prompt_completo = construir_prompt_diario(fecha_hoy)
    print("--- PROMPT GENERADO PARA OLLAMA ---")
    print(prompt_completo)


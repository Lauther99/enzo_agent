from firebase_admin import credentials, initialize_app, firestore
from google_auth_oauthlib.flow import InstalledAppFlow
from google.cloud import firestore as fs
from src.firebase.users_manager import UserManager
from src.settings.settings import Config
from google.auth.transport.requests import Request as GoogleRequest
from datetime import datetime
from google.oauth2.credentials import Credentials
from src.google.utils import encode_state 
from googleapiclient.discovery import build
import traceback
import base64
import logging
import random
import string
from src.utils.utils import convert_to_timezone, generate_random_string
from src.google.types import CalendarEvent


scopes = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/meetings.space.created",
    "https://www.googleapis.com/auth/calendar"
]

# Inicializa Firebase Admin
cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
firebase_app = initialize_app(cred)

db: fs.Client = firestore.client(app=firebase_app)

flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file(
    Config.CLIENT_SECRET_PATH,  # Archivo descargado desde Google Cloud Console
    scopes=scopes,
    redirect_uri=f"{Config.REDIRECT_URI}/callback",
)

def google_login(user_manager: UserManager):
    # Generar URL de autenticación y redirigir al usuario
    encoded = encode_state(user_manager.user_phone)
    state = encoded
    authorization_url, state = flow.authorization_url(
        state=state, access_type="offline", prompt="consent"
    )

    short_id = ''.join(random.choices(string.ascii_letters + string.digits, k=20))

    new_map = {short_id: authorization_url}
    user_manager.user_document.url_map.update(new_map)

    short_url = f"{Config.REDIRECT_URI}/google-auth?user={user_manager.user_phone}&to={short_id}"
    return {"auth_url": short_url}

def refresh_access_token(credentials: Credentials) -> Credentials | None:
    # Verificar si la fecha de expiración está disponible
    if credentials and credentials.expiry:
        # Convertir la cadena de expiración en un objeto datetime
        # expiry_time = datetime.strptime(credentials.expiry, '%Y-%m-%d %H:%M:%S.%f')
        expiry_time = credentials.expiry
        # Obtener la hora actual en UTC
        current_time = datetime.now()
        # Comparar si el token ha expirado
        if expiry_time <= current_time:
            logging.error("El token ha expirado, renovando...")
            # Intentar renovar el token usando el refresh_token
            if credentials.refresh_token:
                credentials.refresh(GoogleRequest())
                logging.error("Token renovado exitosamente.")
                return credentials
            else:
                logging.error("No se puede renovar el token, no hay refresh_token disponible.")
                return None
        else:
            logging.error("El token todavía es válido.")
            return credentials
    else:
        logging.error("La expiración del token no está disponible.")
        return None
    
def send_google_email(c: Credentials, to_emails: str, subject: str, body: str):
    service = build("gmail", "v1", credentials=c)
    from_email = "me"
    to_emails = to_emails.split(",")
    to_emails = [email.strip() for email in to_emails]

    try:
        for to_email in to_emails:
            # Configurar el mensaje para cada destinatario
            message = (
                f"From: {from_email}\nTo: {to_email}\nSubject: {subject}\n\n{body}"
            )
            raw_message = base64.urlsafe_b64encode(message.encode("utf-8")).decode(
                "utf-8"
            )

            # Enviar el correo
            service.users().messages().send(
                userId="me", body={"raw": raw_message}
            ).execute()
            logging.info(f"Correo enviado a {to_email}")
        return {"success": True, "message": f"Correo enviado a: {', '.join(to_emails)}"}
    except Exception as e:
        traceback.logging.error_exc()
        return {"success": False,"message": str(e)}

def list_calendar_events(
    creds: Credentials, calendar_id="primary", *, date_min: str, date_max: str
):
    """
    Retrieves events from a user's Google Calendar.

    Args:
        calendar_id (str): The ID of the calendar to retrieve events from. Defaults to 'primary', which refers to the user's primary calendar.
        date_after (str): The date after events occur in 'YYYY-MM-DD' format.
        date_before (str): The date before events occur in 'YYYY-MM-DD' format. 
    Returns:
        list: A list of calendar events, where each event is represented as a dictionary containing event details.
    """

    try:
        # Crear credenciales desde el diccionario
        # Construir el servicio de la API de Google Calendar
        service = build("calendar", "v3", credentials=creds)

        # Llamar a la API para obtener eventos
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=date_min,
                timeMax=date_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        events_formated = [CalendarEvent.from_dict(ev) for ev in events]
        
        return events_formated

    except Exception as e:
        logging.error(f"Error al recuperar eventos: {e}")
        traceback.logging.error_exc()
        return None
    
def edit_calendar_event(
    user_credentials: Credentials,
    event_id: str,
    summary: str = None,
    description: str = None,
    datetime_start: str = None,
    datetime_end: str = None,
    attendees_emails: list[str] = None,
    has_conference: bool = True,
    calendar_id="primary",
):
    updated_data = {}
    if summary and summary.strip():
        updated_data["summary"] = summary
    if description and description.strip():
        updated_data["description"] = description
    if datetime_start and datetime_start.strip():
        updated_data["start"] = {
            "dateTime": convert_to_timezone(datetime_start),  # Nueva hora de inicio
            "timeZone": Config.TIMEZONE,
        }
    if datetime_end and datetime_end.strip():
        updated_data["end"] ={
            "dateTime": convert_to_timezone(datetime_end),  # Nueva hora de fin
            "timeZone": Config.TIMEZONE,
        }
    if attendees_emails:
        updated_data["attendees"] = {
        "attendees": [{"email": e for e in attendees_emails}],
    }

    if has_conference:
        conference_data = {
        "conferenceData": {
            "createRequest": {
                "requestId": generate_random_string(20),  # Debe ser único por solicitud
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }
        updated_data.update(conference_data)

    try:
        # Construir el servicio de la API de Google Calendar
        service = build("calendar", "v3", credentials=user_credentials)

        # Recuperar el evento existente
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        # Actualizar los campos necesarios
        for key, value in updated_data.items():
            event[key] = value

            if not has_conference and event.get("conferenceData"):
                event["conferenceData"] = None

        # Actualizar el evento en el calendario
        updated_event = (
            service.events()
            .update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event,
                sendUpdates="all",
                conferenceDataVersion=1,
            )
            .execute()
        )

        return CalendarEvent.from_dict(updated_event)

    except Exception as e:
        logging.error(f"Error al actualizar el evento: {e}")
        return None

def create_calendar_event(
    user_credentials: Credentials,
    summary: str,
    description: str,
    datetime_start: str,
    datetime_end: str,
    attendees_emails: list[str] = [],
    calendar_id="primary",
):
    event_data = {}
    if summary and summary.strip():
        event_data["summary"] = summary
    if description and description.strip():
        event_data["description"] = description
    if datetime_start and datetime_start.strip():
        event_data["start"] = {
            "dateTime": convert_to_timezone(datetime_start),  # Nueva hora de inicio
            "timeZone": Config.TIMEZONE,
        }
    if datetime_end and datetime_end.strip():
        event_data["end"] ={
            "dateTime": convert_to_timezone(datetime_end),  # Nueva hora de fin
            "timeZone": Config.TIMEZONE,
        }
    if attendees_emails:
        event_data["attendees"] = {
        "attendees": [{"email": e for e in attendees_emails}],
    }

    try:
        # Construir el servicio de la API de Google Calendar
        service = build("calendar", "v3", credentials=user_credentials)

        # Crear el evento en el calendario
        created_event = (
            service.events()
            .insert(
                calendarId=calendar_id,
                body=event_data,
                sendUpdates="all",
                conferenceDataVersion=1,  # Habilita la integración con Google Meet
            )
            .execute()
        )

        created_event_formatted = CalendarEvent.from_dict(created_event)

        hangout_added = edit_calendar_event(user_credentials, created_event_formatted.event_id)

        return hangout_added

    except Exception as e:
        logging.error(f"Error al crear el evento: {e}")
        return None
    
def list_calendars_types(user_credentials: Credentials):
    service = build("calendar", "v3", credentials=user_credentials)

    # Obtener la lista de calendarios
    try:
        calendars = service.calendarList().list().execute()

        res = [
            f"""Nombre: {calendar['summary']}, ID: {calendar['id']}, is_primary: {calendar.get("primary", False)}"""
            for calendar in calendars["items"]
        ]

        return res
    except Exception as e:
        logging.error(f"Error al listar los calendarios: {e}")
        return []

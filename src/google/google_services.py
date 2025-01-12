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

scopes = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.send",
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

    # user_doc = user_ref.get().to_dict()
    new_map = {short_id: authorization_url}
    user_manager.user_document.url_map.update(new_map)

    # current_url_maps[short_id] = authorization_url

    # user_ref.update(
    #         {
    #             "url_map": current_url_maps,
    #         }
    #     )
    
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
            print("El token ha expirado, renovando...")
            # Intentar renovar el token usando el refresh_token
            if credentials.refresh_token:
                credentials.refresh(GoogleRequest())
                print("Token renovado exitosamente.")
                return credentials
            else:
                print("No se puede renovar el token, no hay refresh_token disponible.")
                return None
        else:
            print("El token todavía es válido.")
            return credentials
    else:
        print("La expiración del token no está disponible.")
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
        traceback.print_exc()
        return {"success": False,"message": str(e)}
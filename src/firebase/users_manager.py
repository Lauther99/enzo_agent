from google.cloud import firestore
from typing import Optional
import src.firebase.types as usr_collection_types
import logging
from datetime import datetime, timezone
from src.google.utils import encode_creds, decode_creds
from google.oauth2.credentials import Credentials

class CredsResponse:
    def __init__(self, need_login, response):
        self.need_login = need_login
        self.response: Credentials | str = response

def save_jwt_to_firebase(db: firestore.Client, user_phone, credentials: Credentials):
    credentials_obj = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "expiry": str(credentials.expiry),
    }
    jwt_token = encode_creds(credentials_obj)
    # Guardar el token en Firestore
    db.collection("users").document(user_phone).update({"google_auth": jwt_token})


def get_creds_from_firebase(db: firestore.Client, user_phone) -> CredsResponse:
    try:
        # Obtener el documento del usuario
        user_doc = db.collection("users").document(user_phone).get()
        if not user_doc.exists:
            return CredsResponse(True, "El usuario debe loguearse.")

        # Extraer el token
        token = user_doc.to_dict().get("google_auth", None)
        if token:
            decoded_token = decode_creds(token)
            if decoded_token.is_valid:
                credentials = Credentials(**decoded_token.response)
                credentials.expiry = datetime.strptime(credentials.expiry, '%Y-%m-%d %H:%M:%S.%f')
                # return {"credentials": credentials, "message": "Usuario autenticado"}
                return CredsResponse(False, credentials)
            # return {"credentials": None, "message": decoded_token.response}
            return CredsResponse(True, decoded_token.response)
        # return {"credentials": None, "message": "Usuario no autenticado"}
        return CredsResponse(True, "Token expirado, el usuario debe hacer login.")

    except Exception as e:
        print(f"Error inesperado: {e}")
        return CredsResponse(True, f"Error inesperado: {e}")



def find_contact_by_user_phone(
    db: firestore.Client, user_phone: str
) -> firestore.DocumentReference:
    try:
        # Referencia al documento en la colección "contacts"
        user_ref = db.collection("users").document(user_phone)
        # Obtiene el documento
        return user_ref

    except Exception as error:
        print(f"Error en find_contact_by_user_phone: {error}")
        return None, None
    
def find_short_url(
    db: firestore.Client, user_phone: str, short_id: str
) -> str | None:
    try:
        # Referencia al documento en la colección "contacts"
        user_ref = db.collection("users").document(user_phone)
        user_doc = user_ref.get()

        if user_doc.exists:
            user_dic = user_doc.to_dict()
            url_map: dict = user_dic.get("url_map", None)
            if not url_map:
                return None
            auth_url = url_map[short_id]
            return auth_url

    except Exception as error:
        print(f"Error en find_contact_by_user_phone: {error}")
        return None, None



def get_initial_conversation_messages(
    user_phone: str,
    sender_phone: str,
    message: str,
    waid: str,
    system_message: str,
):
    try:
        logging.info(f"El usuario con teléfono {user_phone} no existe.")
        system_message_ = usr_collection_types.MessageDataType(
            sender="system",
            content=system_message,
            role="system",
            created_at=datetime.now().isoformat(),  # Fecha actual en formato UTC
            waid="system",
        )

        new_message = usr_collection_types.MessageDataType(
            sender=sender_phone,
            content=message,
            role="user",
            created_at=datetime.now().isoformat(),  # Fecha actual en formato UTC
            waid=waid,
        )
        return [system_message_, new_message]

    except Exception as error:
        logging.info(f"Error al guardar el mensaje: {error}")
        return []


def create_new_user_chat(
    user_ref: firestore.DocumentReference,
    messages: list[usr_collection_types.MessageDataType],
    last_message: usr_collection_types.MessageDataType,
    user_phone: str,
):
    try:
        user_ref.create(
            {
                "last_interaction": datetime.now().isoformat(),
                "last_message": last_message.to_json(),
                "messages": [m.to_json() for m in messages],
                "phone_number": user_phone,
            }
        )
        logging.info("Conversación creada")

    except Exception as error:
        logging.info(f"Error al guardar el mensaje: {error}")
        return


def save_to_chat(
    user_ref: firestore.DocumentReference,
    current_messages: list[usr_collection_types.MessageDataType],
):
    try:
        # Referencia al documento en la colección "contacts"

        user_ref.update(
            {
                "last_interaction": datetime.now().isoformat(),
                "last_message": current_messages[-1].to_json(),
                "messages": [
                    msg.to_json() for msg in current_messages
                ],  # Convertir los mensajes a JSON antes de guardarlos
            }
        )
        logging.info("Mensaje guardado exitosamente.")
        return

    except Exception as error:
        logging.info(f"Error al guardar el mensaje: {error}")
        return

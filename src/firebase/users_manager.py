from google.cloud import firestore
import src.firebase.types as usr_collection_types
import logging
from datetime import datetime
from src.google.utils import encode_creds, decode_creds
from google.oauth2.credentials import Credentials


class CredsResponse:
    def __init__(self, need_login, response):
        self.need_login = need_login
        self.response: Credentials | str = response


# @dataclass
class UserManager:
    def __init__(self, db, user_phone, bot_phone=None, current_waid=None):
        self.db: firestore.Client = db
        self.user_phone: str = user_phone
        self.bot_phone: str = bot_phone
        self.current_waid: str = current_waid

        self.user_document: usr_collection_types.UsersCollection = None
        self.user_ref: firestore.DocumentReference = None

        self.user_document, self.user_ref, self.user_exists = self.find_contact_by_user_phone()

    def find_contact_by_user_phone(self) -> firestore.DocumentReference:
        user_doc = usr_collection_types.UsersCollection(
            phone=self.user_phone,
            bot_phone=self.bot_phone,
            last_interaction=str(datetime.now()),
        )
        user_ref = self.db.collection("users").document(self.user_phone)

        try:
            # Referencia al documento en la colección "contacts"
            user_snapshot = user_ref.get()

            if user_snapshot.exists:
                user_doc = usr_collection_types.UsersCollection.from_json(
                    user_snapshot.to_dict()
                )
                return user_doc, user_ref, True

        except Exception as error:
            logging.error(f"Error en find_contact_by_user_phone: {error}")

        return user_doc, user_ref, False

    def save_jwt_to_firebase(self, credentials: Credentials):
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

        self.user_document.google_auth = jwt_token
        # db.collection("users").document(user_phone).update({"google_auth": jwt_token})

    def get_creds_from_firebase(self) -> CredsResponse:
        try:
            # Obtener el documento del usuario
            # user_doc = db.collection("users").document(user_phone).get()
            # if not user_doc.exists:
            #     return CredsResponse(True, "El usuario debe loguearse.")

            # Extraer el token
            # token = user_doc.to_dict().get("google_auth", None)
            token = self.user_document.google_auth
            if token:
                decoded_token = decode_creds(token)
                if decoded_token.is_valid:
                    credentials = Credentials(**decoded_token.response)
                    credentials.expiry = datetime.strptime(
                        credentials.expiry, "%Y-%m-%d %H:%M:%S.%f"
                    )
                    # return {"credentials": credentials, "message": "Usuario autenticado"}
                    return CredsResponse(False, credentials)
                # return {"credentials": None, "message": decoded_token.response}
                return CredsResponse(True, decoded_token.response)
            # return {"credentials": None, "message": "Usuario no autenticado"}
            return CredsResponse(True, "Token expirado, el usuario debe hacer login.")

        except Exception as e:
            print(f"Error inesperado: {e}")
            return CredsResponse(True, f"Error inesperado: {e}")

    def find_short_url(self, short_id: str) -> str | None:
        try:
            # Referencia al documento en la colección "contacts"
            # user_ref = db.collection("users").document(user_phone)
            # user_doc = user_ref.get()
            if self.user_document:
                user_dic = self.user_document.to_json()
                url_map: dict = user_dic.get("url_map", None)
                if not url_map:
                    return None
                auth_url = url_map[short_id]
                return auth_url

        except Exception as error:
            print(f"Error en find_contact_by_user_phone: {error}")
            return None, None

    def get_initial_conversation_messages(
        self,
        message,
        system_message: str,
    ):
        try:
            logging.info(f"El usuario con teléfono {self.user_phone} no existe.")
            system_message_ = usr_collection_types.MessageDataType(
                sender="system",
                content=system_message,
                role="system",
                created_at=datetime.now().isoformat(),  # Fecha actual en formato UTC
                waid="system",
            )

            new_message = usr_collection_types.MessageDataType(
                sender=self.user_phone,
                content=message,
                role="user",
                created_at=datetime.now().isoformat(),  # Fecha actual en formato UTC
                waid=self.current_waid,
            )
            return [system_message_, new_message]

        except Exception as error:
            logging.info(f"Error al guardar el mensaje: {error}")
            return []

    def create_new_user_chat(
        self,
        # user_ref: firestore.DocumentReference,
        messages: list[usr_collection_types.MessageDataType],
        last_message: usr_collection_types.MessageDataType,
        # user_phone: str,
        # waid: str,
    ):
        try:
            self.user_document.last_interaction = datetime.now().isoformat()
            self.user_document.last_message = last_message
            self.user_document.messages = messages
            self.user_document.phone = self.user_phone
            self.user_document.bot_phone = self.bot_phone
            # self.user_document.current_waids = [self.current_waid]

            # user_ref.create(
            #     {
            #         "last_interaction": datetime.now().isoformat(),
            #         "last_message": last_message.to_json(),
            #         "messages": [m.to_json() for m in messages],
            #         "phone": user_phone,
            #         "current_waids": [waid],
            #     }
            # )
            logging.info("Conversación creada")

        except Exception as error:
            logging.info(f"Error al guardar el mensaje: {error}")
            return

    def save_to_chat(self):

        try:
            # Referencia al documento en la colección "contacts"
            log_message = f"""\n------------------------ USER CHAT ------------------------\n------------------------ USER CHAT ------------------------\n{self.user_document.to_json()}\n------------------------ USER CHAT ------------------------\n------------------------ USER CHAT ------------------------"""

            logging.info(log_message)

            if self.user_exists:
                self.user_ref.update(self.user_document.to_json())
                logging.info("Mensaje guardado exitosamente.")
                return
            else:
                self.user_ref.create(self.user_document.to_json())
                logging.info("Conversación creada")

        except Exception as error:
            logging.info(f"Error al guardar el mensaje: {error}")
            return


def _save_jwt_to_firebase(db: firestore.Client, user_phone, credentials: Credentials):
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


def _get_creds_from_firebase(db: firestore.Client, user_phone) -> CredsResponse:
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
                credentials.expiry = datetime.strptime(
                    credentials.expiry, "%Y-%m-%d %H:%M:%S.%f"
                )
                # return {"credentials": credentials, "message": "Usuario autenticado"}
                return CredsResponse(False, credentials)
            # return {"credentials": None, "message": decoded_token.response}
            return CredsResponse(True, decoded_token.response)
        # return {"credentials": None, "message": "Usuario no autenticado"}
        return CredsResponse(True, "Token expirado, el usuario debe hacer login.")

    except Exception as e:
        print(f"Error inesperado: {e}")
        return CredsResponse(True, f"Error inesperado: {e}")


def _find_contact_by_user_phone(
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


def _find_short_url(db: firestore.Client, user_phone: str, short_id: str) -> str | None:
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


def _get_initial_conversation_messages(
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


def _create_new_user_chat(
    user_ref: firestore.DocumentReference,
    messages: list[usr_collection_types.MessageDataType],
    last_message: usr_collection_types.MessageDataType,
    user_phone: str,
    waid: str,
):
    try:
        user_ref.create(
            {
                "last_interaction": datetime.now().isoformat(),
                "last_message": last_message.to_json(),
                "messages": [m.to_json() for m in messages],
                "phone_number": user_phone,
                "current_waids": [waid],
            }
        )
        logging.info("Conversación creada")

    except Exception as error:
        logging.info(f"Error al guardar el mensaje: {error}")
        return


def _save_to_chat(
    user_ref: firestore.DocumentReference,
    current_messages: list[usr_collection_types.MessageDataType],
    current_waids: list[str],
):
    try:
        # Referencia al documento en la colección "contacts"

        user_ref.update(
            {
                "last_interaction": datetime.now().isoformat(),
                "last_message": current_messages[-1].to_json(),
                "current_waids": current_waids,
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

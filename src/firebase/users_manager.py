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
            # Snapshot en la colección "users"
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
        # Guardar el token
        self.user_document.google_auth = jwt_token

    def get_creds_from_firebase(self) -> CredsResponse:
        try:
            # Obtener el documento del usuario
            token = self.user_document.google_auth
            
            if token:
                decoded_token = decode_creds(token)
                if decoded_token.is_valid:
                    credentials = Credentials(**decoded_token.response)
                    credentials.expiry = datetime.strptime(
                        credentials.expiry, "%Y-%m-%d %H:%M:%S.%f"
                    )
                    return CredsResponse(False, credentials)
                return CredsResponse(True, decoded_token.response)
            return CredsResponse(True, "Token expirado, el usuario debe hacer login.")

        except Exception as e:
            print(f"Error inesperado: {e}")
            return CredsResponse(True, f"Error inesperado: {e}")

    def find_short_url(self, short_id: str) -> str | None:
        try:
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
                created_at=datetime.now().isoformat(),
                waid="system",
            )

            new_message = usr_collection_types.MessageDataType(
                sender=self.user_phone,
                content=message,
                role="user",
                created_at=datetime.now().isoformat(),
                waid=self.current_waid,
            )
            return [system_message_, new_message]

        except Exception as error:
            logging.info(f"Error al guardar el mensaje: {error}")
            return []

    def create_new_user_chat(
        self,
        messages: list[usr_collection_types.MessageDataType],
        last_message: usr_collection_types.MessageDataType,
    ):
        try:
            self.user_document.last_interaction = datetime.now().isoformat()
            self.user_document.last_message = last_message
            self.user_document.messages = messages
            self.user_document.phone = self.user_phone
            self.user_document.bot_phone = self.bot_phone
            logging.info("Conversación creada")

        except Exception as error:
            logging.info(f"Error al guardar el mensaje: {error}")
            return

    def save_to_chat(self):

        try:
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



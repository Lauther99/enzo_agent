
from src.settings.settings import Config
from datetime import datetime, timedelta
import jwt
from src.google.types import DecodeJWTResponse

SECRET_KEY = Config.SECRET_KEY

def encode_state(phone_number):
    # Crear los datos del JWT
    payload = {
        "phone_number": phone_number,
        "exp": datetime.now() + timedelta(days=1),  # Expira en 5 dias
        "iat": datetime.now(),  # Fecha de emisión
    }

    # Generar el JWT
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def decode_state(state):
    try:
        # Decodificar y validar el JWT
        payload = jwt.decode(state, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "El token ha expirado"}
    except jwt.InvalidTokenError:
        return {"error": "Token inválido"}

def decode_creds(token) -> DecodeJWTResponse:
    try:
        # Decodificar y validar el JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        creds = payload.get("credentials", None)
        if not creds:
            return DecodeJWTResponse(False, "Credenciales no encontradas")
        return DecodeJWTResponse(True, creds)

    except jwt.ExpiredSignatureError:
        return DecodeJWTResponse(False, "El token ha expirado")
    except jwt.InvalidTokenError:
        return DecodeJWTResponse(False, "Token inválido")

def encode_creds(credentials):
    # Crear los datos del JWT
    payload = {
        "credentials": credentials,
        "exp": datetime.now() + timedelta(days=5),  # Expira en 5 dias
        "iat": datetime.now(),  # Fecha de emisión
    }

    # Generar el JWT
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


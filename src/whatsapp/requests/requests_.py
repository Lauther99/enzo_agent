import requests
from src.settings.settings import Config

# Define el URL base y el token
WHATSAPP_TOKEN = Config.META_TOKEN

# Configura una sesión personalizada
WhatsAppSession = requests.Session()
WhatsAppSession.headers.update({
    "Content-Type": "application/json",
    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
})

import environ

env = environ.Env()
environ.Env.read_env()

class Config:
    GROQ_API_KEY = env("GROQ_API_KEY")
    HF_TOKEN = env("HF_TOKEN")
    SECRET_KEY = env("SECRET_KEY")
    FIREBASE_CREDENTIALS_PATH = env("FIREBASE_CREDENTIALS_PATH")
    CLIENT_SECRET_PATH = env("CLIENT_SECRET_PATH")
    REDIRECT_URI = env("REDIRECT_URI")
    WHATSAPP_URL = env("WHATSAPP_URL")
    META_TOKEN = env("META_TOKEN")
    TIMEZONE = env("TIMEZONE")


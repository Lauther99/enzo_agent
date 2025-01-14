from src.agent.tools.collectors import Collector
from src.components.tool import BaseTool
import src.whatsapp.types as wsp_types
from google.cloud import firestore
from src.agent.tools.email_scheduler import email_scheduler
from src.agent.tools.google_auth import google_auth_url
from src.agent.tools.calendar_events import list_events, manage_events
from src.settings.settings import Config
from src.components.memory import Memory
from src.agent.agent_ import AgentExecutor, default_agent, default_llms
from src.whatsapp.requests.requests_ import WhatsAppSession, requests
from src.firebase.users_manager import UserManager
import logging

tools: dict[str, BaseTool] = {
    "email_scheduler": email_scheduler,
    "google_auth_url": google_auth_url,
    "list_events": list_events,
    "manage_events": manage_events,
}


def send_whatsapp_message(
    *,
    to_phone: str,
    message: str,
) -> str:
    url = f"{Config.META_BASE_ENDPOINT}/{Config.META_ID}/messages"
    try:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": message[:4094],
            },
        }
        response = WhatsAppSession.post(url, json=data)

        if response.status_code == 200:
            r = response.json()
            waid = r["messages"][0]["id"]

            print("Mensaje enviado:", response.json())
            return waid
        else:
            print(f"Error {response.status_code}: {response.text}")

            return ""

    except Exception as e:
        logging.error(e)
        return ""


def download_whatsapp_voice_note(audio_id: str, user_id):
    url = f"{Config.META_BASE_ENDPOINT}/{audio_id}"
    response = WhatsAppSession.get(url)
    # WhatsAppSession.headers.update(
    #     {
    #         "Content-Type": "audio/ogg",
    #     }
    # )

    if response.status_code == 200:
        media_url = response.json().get("url")
        # Step 2: Download the media
        media_response = requests.get(
            media_url,
            headers={
                "Authorization": f"Bearer {Config.META_TOKEN}",  # Si la URL no incluye la autorización
            },
        )
        if media_response.status_code == 200:
            import os

            save_path = f"../../media/users/{user_id}"
            os.makedirs(save_path, exist_ok=True)

            # Construir la ruta completa
            file_path = os.path.join(save_path, f"{audio_id}.ogg")
            with open(file_path, "wb") as audio_file:
                audio_file.write(media_response.content)
            logging.info(f"Audio downloaded successfully as {audio_id}.ogg")
            full_file_path = os.path.abspath(file_path)
            return full_file_path
        else:
            logging.error(media_response.status_code)
            logging.error(media_response.text)
            logging.error("Audio couldn't be downloaded")
            return None
    else:
        logging.error(f"Failed to get media URL: {response.text}")
        return None


def chat_manager(db: firestore.Client, message_data: wsp_types.Props):
    content = message_data.messageInfo.content
    message_type = message_data.messageInfo.type

    user_phone = message_data.userPhoneNumber
    bot_phone = message_data.botPhoneNumber
    waid = message_data.id

    user_manager = UserManager(db, user_phone, bot_phone, waid)
    memory = Memory(tools=tools, user_manager=user_manager)
    collector = Collector()

    agent_executor = AgentExecutor(
                agent=default_agent, tools=tools, memory=memory, collector=collector
            )

    if message_type == "text":
        if waid not in user_manager.user_document.current_waids:
            memory.add_user_message(content, waid)
            response = agent_executor.invoke()

            waid = send_whatsapp_message(
                to_phone=memory.user_manager.user_phone,
                message=response.final_answer,
            )
            memory.add_assistant_message(response.content, waid)
            user_manager.save_to_chat()
            return

    elif message_type == "audio":
        voice_note_path = download_whatsapp_voice_note(content, user_phone)

        if voice_note_path:
            audio_transcription = default_llms[
                "from_groq_whisper_large"
            ].audio_transcription_llm(file_path=voice_note_path)
            logging.info(f"Audio transcription: {audio_transcription}")

            memory.add_user_message(audio_transcription, waid)
            response = agent_executor.invoke()

            waid = send_whatsapp_message(
                to_phone=memory.user_manager.user_phone,
                message=response.final_answer,
            )

            memory.add_assistant_message(response.content, waid)
            user_manager.save_to_chat()
            return

        return
    
    return 

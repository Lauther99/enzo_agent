from src.agent.tools.collectors import Collector
from src.components.tool import BaseTool
import src.whatsapp.types as wsp_types
from google.cloud import firestore
from src.agent.tools.email_scheduler import email_scheduler
from src.agent.tools.google_auth import google_auth_url
from src.agent.tools.calendar_events import list_events, manage_events
from src.settings.settings import Config
from src.components.memory import Memory
from src.agent.agent_ import AgentExecutor, default_agent
from src.whatsapp.requests.requests_ import WhatsAppSession
from src.firebase.users_manager import UserManager
import logging

tools: dict[str, BaseTool] = {
    "email_scheduler": email_scheduler,
    "google_auth_url": google_auth_url,
    "list_events": list_events,
    "manage_events": manage_events,
}

WHATSAPP_URL = Config.WHATSAPP_URL


def send_whatsapp_message(
    *,
    to_phone: str,
    message: str,
) -> str:
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
        response = WhatsAppSession.post(f"{WHATSAPP_URL}/messages", json=data)

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


def chat_manager(db: firestore.Client, message_data: wsp_types.Props):
    message = message_data.messageInfo.content
    message_type = message_data.messageInfo.type

    user_phone = message_data.userPhoneNumber
    bot_phone = message_data.botPhoneNumber
    waid = message_data.id

    user_manager = UserManager(db, user_phone, bot_phone, waid)
    memory = Memory(tools=tools, user_manager=user_manager)
    collector = Collector()

    if message_type == "text":

        if waid not in user_manager.user_document.current_waids:
            memory.add_user_message(message, waid)
            
            agent_executor = AgentExecutor(
                agent=default_agent, tools=tools, memory=memory, collector=collector
            )

            response = agent_executor.invoke()

            waid = send_whatsapp_message(
                to_phone=memory.user_manager.user_phone,
                message=response.final_answer,
            )
            memory.add_assistant_message(response.content, waid)
            user_manager.save_to_chat()
        return

    elif message_type == "audio":
        logging.info(message_data.to_json())

        return

        # txt, messages_list, usage  = chat(llm=model_1, chat_messages=m_list, has_stream=True)
        # logging.info(txt)

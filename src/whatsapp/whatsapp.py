from src.agent.tools.collectors import Collector
from src.components.tool import BaseTool
import src.whatsapp.types as wsp_types
from google.cloud import firestore
from src.agent.tools.email_scheduler import email_scheduler
from src.agent.tools.google_auth import google_auth_url
from src.settings.settings import Config
from src.components.memory import Memory
from src.agent.agent_ import Agent, AgentExecutor
from src.firebase.users_manager import UserManager

tools: dict[str, BaseTool] = {
    "email_scheduler": email_scheduler,
    "google_auth_url": google_auth_url,
}

GROQ_API_KEY = Config.GROQ_API_KEY
HF_API_KEY = Config.HF_TOKEN


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
            # memory.save_memory()
            "hay que implementar el objeto para un mejor manejor de lo que se va guardando"
            agent = Agent.from_HF_llama3_3_70b_instruct(HF_API_KEY, memory, collector)
            agent_executor = AgentExecutor(agent=agent, tools=tools)

            agent_executor.invoke()

            user_manager.save_to_chat()
        return

        # txt, messages_list, usage  = chat(llm=model_1, chat_messages=m_list, has_stream=True)
        # logging.info(txt)

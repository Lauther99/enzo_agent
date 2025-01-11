from src.agent.tools.collectors import Collector
from src.components.tool import BaseTool
import src.whatsapp.types as wsp_types
from google.cloud import firestore
from src.agent.tools.email_scheduler import email_scheduler
from src.settings.settings import Config
from src.components.memory import Memory
from src.agent.agent_ import Agent, AgentExecutor
from huggingface_hub import InferenceClient

tools: dict[str, BaseTool] = {
    "email_scheduler": email_scheduler,
}

GROQ_API_KEY = Config.GROQ_API_KEY
HF_API_KEY = Config.HF_TOKEN


async def chat_manager(db: firestore.Client, msg_data: wsp_types.Props):
    message = msg_data.messageInfo.content
    message_type = msg_data.messageInfo.type
    user_phone = msg_data.userPhoneNumber
    waid = msg_data.id

    memory = Memory(
        tools=tools,
        db=db,
        user_phone=user_phone,
    )

    collector = Collector()

    if message_type == "text":
        memory.add_user_message(message, waid)
        memory.save_memory()
        
        agent = Agent.from_HF_llama3_3_70b_instruct(HF_API_KEY, memory, collector)
        agent_executor = AgentExecutor(agent=agent, tools=tools)

        agent_executor.invoke()

        agent_executor.save_memory()
        
        # txt, messages_list, usage  = chat(llm=model_1, chat_messages=m_list, has_stream=True)
        # logging.info(txt)



def chat_manager_2(db: firestore.Client, msg_data: wsp_types.Props, client: InferenceClient):
    message = msg_data.messageInfo.content
    message_type = msg_data.messageInfo.type
    user_phone = msg_data.userPhoneNumber
    waid = msg_data.id

    memory = Memory(
        tools=tools,
        db=db,
        user_phone=user_phone,
    )

    collector = Collector()

    if message_type == "text":
        # chat_template = memory.get_messages_chat_template()
        memory.add_user_message(message, waid)
        memory.save_memory()
        
        agent = Agent.from_HF_llama3_3_70b_instruct(HF_API_KEY, memory, collector)
        agent_executor = AgentExecutor(agent=agent, tools=tools)

        agent_executor.invoke()

        agent_executor.save_memory()
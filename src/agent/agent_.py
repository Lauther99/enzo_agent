from src.agent.tools.collectors import Collector
from src.components.memory import Memory
from src.components.llms import BaseGenericLLM, GenericLLM
from src.components.prompt import ChatTemplate
from src.components.tool import BaseTool
import uuid
import logging
import json
from typing import Dict
from src.agent.types import Base_Agent_Response, Base_LLM_Response, BaseToolResponse
from src.whatsapp.requests.requests_ import WhatsAppSession
from src.settings.settings import Config


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
                "body": message[:4094],  # Limitamos a 4094 caracteres
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
    
def chat(
    *,
    llm: BaseGenericLLM,
    model_name: str = None,
    chat_messages: ChatTemplate,
    max_tokens=1500,
    has_stream=False,
):
    txt = ""
    usage = {}
    messages_list = []

    try:
        for c, m, u in llm.chat_llm(
            model_name=model_name,
            messages=chat_messages,
            max_tokens=max_tokens,
            has_stream=has_stream,
        ):
            if c:
                # logging.info(f"{c}")
                txt += c
            if u:
                usage.update(u)
            if m:
                messages_list = m
        return txt, messages_list, usage

    except Exception as e:
        return e, messages_list, usage

def base_agent_chat_generation_2(
    llm: BaseGenericLLM,
    chat_template: ChatTemplate,
    response_type="agent-generation",
    max_tokens=700,
    stream=False,
) -> Base_Agent_Response:
    llm_call_id = f"""llm-call--{uuid.uuid4().hex}"""
    model_name = llm.default_model_name
    logging.info(f"{response_type} -- {llm.default_model_name} -- {llm_call_id}")

    content_, messages_list, usage = chat(
        llm=llm,
        model_name=model_name,
        chat_messages=chat_template,
        max_tokens=max_tokens,
        has_stream=stream,
    )
    logging.info(content_)

    cleaned_content = f"""{content_.split("<end_action>")[0].strip()}<end_action>"""

    thought = cleaned_content.split("Action:")[0].strip()
    action_txt = cleaned_content.split("Action:")[1].split("<end_action>")[0].strip()
    action_json = json.loads(action_txt)

    action = action_json["action"]
    parameters = action_json["action_input"]

    final_answer = action_json["action_input"]["answer"] if action == "final_answer" else ""
    markdown_info = ""

    current_scratchpad = """"""
    if thought.strip():
        current_scratchpad += f"Thought: {thought}\n"
    if action.strip():
        current_scratchpad += f"Action: {action}\n"
    if parameters:
        current_scratchpad += f"Parameters: {parameters}\n"
    if final_answer.strip():
        current_scratchpad += f"Answer: {final_answer}\n"
    if markdown_info.strip():
        current_scratchpad += f"Markdown info: {markdown_info}\n"

    print(current_scratchpad, "\n\n")

    response_dict = Base_Agent_Response(
        thought=thought,
        action=action.replace("[", "")
        .replace("]", "")
        .replace("<", "")
        .replace(">", "")
        .strip(),
        parameters=parameters,
        final_answer=final_answer,
        markdown_info=markdown_info,
        content=cleaned_content,
        usage=usage,
        llm_call_id=llm_call_id,
    )

    output = Base_LLM_Response(
        type=response_type,
        messages_list=messages_list,
        llm_response=cleaned_content.strip(),
        formated_response=response_dict.to_dict(),
        model_name=llm.default_model_name,
        llm_call_id=llm_call_id,
        usage=usage,
    )

    return response_dict

class Agent:
    def __init__(self):
        self.llm_model: BaseGenericLLM = None
        self.memory: Memory = None
        self.collector: Collector | None = None

    @classmethod
    def from_groq_llama3_3_70b(
        cls,
        api_key: str,
        memory: Memory,
        collector: Collector,
    ):
        agent_instance = cls()
        agent_instance.memory = memory
        agent_instance.collector = collector

        agent_instance.llm_model = GenericLLM.from_groq_llama3_3_70b(api_key=api_key)
        return agent_instance
    
    @classmethod
    def from_HF_llama3_3_70b_instruct(
        cls,
        api_key: str,
        memory: Memory,
        collector: Collector,
    ):
        agent_instance = cls()
        agent_instance.memory = memory
        agent_instance.collector = collector

        agent_instance.llm_model = GenericLLM.from_HF_llama3_3_70b_instruct(api_key=api_key)
        return agent_instance
    

    def agent_loop_2(
        self,
        tools: dict[str, BaseTool],
        max_iterarions=5,
        current_iteration=1,
    ):
        response_dict: Base_Agent_Response = base_agent_chat_generation_2(
            llm=self.llm_model,
            chat_template=self.memory.get_messages_chat_template(),
            max_tokens=1000,
            stream=False,
        )

        logging.info("\n\n\nresponse_dict:")
        logging.info(response_dict.to_dict())
        logging.info("\n\n\n")

        if response_dict.action == "final_answer":
            waid = send_whatsapp_message(
                to_phone=self.memory.user_manager.user_phone,
                message=response_dict.final_answer,
            )

            self.memory.add_assistant_message(response_dict.content, waid)
            return  # Aqui termina el loop

        else:
            action_name = response_dict.action
            action_input = response_dict.parameters

            self.memory.add_assistant_message(response_dict.content, "tool")
            logging.info(f"Action: {action_name}")

            if action_name in tools:
                action = tools[action_name]
                logging.info(f"{action_input}\n\n")

                parameters = action_input

                try:
                    parameters["collector"] = self.collector
                    parameters["memory"] = self.memory
                    parameters["user_phone"] = self.memory.user_manager.user_phone
                    parameters["db"] = self.memory.user_manager.db


                except Exception as e:
                    message = f"Error al ingresar los parametros en el action: {e}\n"
                    self.memory.add_tool_message(message, action_name)
                    logging.debug(message)

                    return self.agent_loop_2(
                        tools,
                        max_iterarions,
                        current_iteration + 1,
                    )

                try:
                    action_response: BaseToolResponse = action(**parameters)
                    action_response_message = action_response.tool_friendly_response
                    
                    logging.info(action_response_message)

                    self.memory.add_tool_message(action_response_message, action_name)
                    # tool_message = self.memory.add_tool_message(action_response, tool_name=str(action_name), replied_message_id=assistant_message_id)
                    # tool_message_id = tool_message.metadata["message_id"]

                except Exception as e:
                    # tool_message = self.memory.add_tool_message(e, tool_name=str(action), replied_message_id=assistant_message_id)
                    # tool_message_id = tool_message.metadata["message_id"]
                    message = f"Action Response: {e}\n"
                    logging.debug(message)
                    self.memory.add_tool_message(message, action_name)

                    return self.agent_loop_2(
                        tools,
                        max_iterarions,
                        current_iteration + 1,
                    )

                if current_iteration < max_iterarions:
                    return self.agent_loop_2(
                        tools,
                        max_iterarions,
                        current_iteration + 1,
                    )
                else:
                    waid = send_whatsapp_message(
                        to_phone=self.memory.user_manager.user_phone,
                        message="Exceed number of iterations, try again later.",
                    )
                    
                    self.memory.add_assistant_message(
                        message="Exceed number of iterations, try again later.",
                        waid=waid
                    )

                    return


class AgentExecutor:
    def __init__(self, agent: Agent, tools: Dict[str, BaseTool]):
        self.agent = agent
        self.tools = tools

    def invoke(self, *, max_iterations=10):
        max_iterations = max_iterations or 10

        self.agent.agent_loop_2(
            tools=self.tools,
            max_iterarions=max_iterations,
        )

from src.components.prompt import ChatTemplate
from google.cloud import firestore
import src.firebase.types as usr_collection_types
import logging
from src.firebase.users_manager import UserManager
from datetime import datetime, timezone
from src.agent.prompt.prompt import get_agent_prompt_2, get_task_prompt
from src.components.tool import BaseTool

now = datetime.now().strftime(
    "Today's date is %B %d, %Y, and the current time is %H:%M:%S."
)

user_message_mask = """{now}
User current message is: 
{user_message}
Interact with him in spanish."""

tool_message_mask = """Action executed: **{action_name}**\nResponse:\n{message}"""


class Memory:
    def __init__(
        self,
        *,
        tools: dict[str, BaseTool],
        user_manager: UserManager
    ):
        self.tools = tools
        self.user_manager = user_manager

        self.update_if_new_chat()

    def update_if_new_chat(self):
        if not self.user_manager.user_document.messages:
            system_message_ = usr_collection_types.MessageDataType(
                sender="system",
                content=get_task_prompt(tools=self.tools),
                role="system",
                created_at=datetime.now(
                    timezone.utc
                ).isoformat(),
                waid="system",
            )
            self.user_manager.user_document.messages.append(system_message_)

    def add_user_message(self, message, waid):
        new_message = usr_collection_types.MessageDataType(
            sender=self.user_manager.user_phone,
            content=user_message_mask.format(now=now, user_message=message),
            role="user",
            created_at=datetime.now(
                timezone.utc
            ).isoformat(),
            waid=waid,
        )
        self.user_manager.user_document.messages.append(new_message)
        self.user_manager.user_document.current_waids.append(waid)
        self.user_manager.user_document.last_message = new_message

    def add_assistant_message(self, message, waid):
        new_message = usr_collection_types.MessageDataType(
            sender="assistant",
            content=message,
            role="assistant",
            created_at=datetime.now(
                timezone.utc
            ).isoformat(),
            waid=waid,
        )
        self.user_manager.user_document.messages.append(new_message)
        self.user_manager.user_document.current_waids.append(waid)
        self.user_manager.user_document.last_message = new_message

    def add_tool_message(self, message, action_name):
        new_message = usr_collection_types.MessageDataType(
            sender="tool",
            content=tool_message_mask.format(action_name=action_name, message=message),
            role="tool",
            created_at=datetime.now(
                timezone.utc
            ).isoformat(),
            waid="tool",
        )
        self.user_manager.user_document.messages.append(new_message)
        self.user_manager.user_document.last_message = new_message

    def get_messages_chat_template(self) -> ChatTemplate:
        messages = [msg.get_llm_legible_message() for msg in self.user_manager.user_document.messages]
        return ChatTemplate(messages=messages)

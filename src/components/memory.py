from src.components.prompt import ChatTemplate
from src.firebase.users_manager import (
    save_to_chat,
)
from google.cloud import firestore
import src.firebase.types as usr_collection_types
import logging
from src.firebase.users_manager import (
    find_contact_by_user_phone,
    save_to_chat,
    create_new_user_chat,
)
from datetime import datetime, timezone
from src.agent.prompt.prompt import get_agent_prompt_2, get_task_prompt
from src.components.tool import BaseTool
# from transformers import Tool

now = datetime.now().strftime("Today's date is %B %d, %Y, and the current time is %H:%M:%S.")

user_message_mask = """{now}
User task is: 
{user_message}"""

tool_message_mask = """Action executed: **{action_name}**\nResponse:\n{message}"""

class Memory:
    def __init__(
        self,
        *,
        tools: dict[str, BaseTool],
        db: firestore.Client,
        user_phone: str,
    ):
        self.tools = tools
        self.db = db
        self.user_phone = user_phone

        self.user_ref = find_contact_by_user_phone(db, user_phone)
        self.is_new_user = self._is_new_user()
        self.current_msgs_history = self._get_current_messages()

    def _is_new_user(self):
        user_snapshot = self.user_ref.get()
        self.user_snapshot = user_snapshot
        return user_snapshot.exists is False

    def _get_current_messages(self):
        if self.is_new_user:
            system_message_ = usr_collection_types.MessageDataType(
                sender="system",
                content=get_task_prompt(tools=self.tools),
                role="system",
                created_at=datetime.now(
                    timezone.utc
                ).isoformat(),  # Fecha actual en formato UTC
                waid="system",
            )
            return [system_message_]
        else:
            user_doc = usr_collection_types.UsersCollection.from_json(
                self.user_snapshot.to_dict()
            )
            return user_doc.messages

    def add_user_message(self, message, waid):
        new_message = usr_collection_types.MessageDataType(
            sender=self.user_phone,
            content=user_message_mask.format(now=now, user_message=message),
            role="user",
            created_at=datetime.now(
                timezone.utc
            ).isoformat(),  # Fecha actual en formato UTC
            waid=waid,
        )
        self.current_msgs_history.append(new_message)

    def add_assistant_message(self, message, waid):
        new_message = usr_collection_types.MessageDataType(
            sender="assistant",
            content=message,
            role="assistant",
            created_at=datetime.now(
                timezone.utc
            ).isoformat(),  # Fecha actual en formato UTC
            waid=waid,
        )
        self.current_msgs_history.append(new_message)

    def add_tool_message(self, message, action_name):
        new_message = usr_collection_types.MessageDataType(
            sender="tool",
            content=tool_message_mask.format(action_name=action_name, message=message),
            role="tool",
            created_at=datetime.now(
                timezone.utc
            ).isoformat(),  # Fecha actual en formato UTC
            waid="tool",
        )
        self.current_msgs_history.append(new_message)

    def save_memory(self):
        if self.is_new_user:
            create_new_user_chat(
                self.user_ref,
                self.current_msgs_history,
                self.current_msgs_history[-1],
                self.user_phone,
            )
            self.is_new_user = False
        else:
            save_to_chat(
                self.user_ref, self.current_msgs_history
            )

    def get_messages_chat_template(self) -> ChatTemplate:
        messages = [msg.get_llm_legible_message() for msg in self.current_msgs_history]
        return ChatTemplate(messages=messages)

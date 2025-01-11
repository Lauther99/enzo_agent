from typing import List, Optional
from datetime import datetime
from src.components.prompt import ChatMessage


class MessageDataType:
    def __init__(
        self,
        sender: str,
        content: str,
        role: str,
        created_at: str,
        waid: str,
    ):
        self.sender = sender
        self.content = content
        self.role = role
        self.created_at = created_at
        self.waid = waid

    @classmethod
    def from_json(cls, data: dict) -> "MessageDataType":
        """
        Crea una instancia de MessageDataType a partir de un diccionario JSON.
        """
        return cls(
            sender=data.get("sender", ""),
            content=data.get("content", ""),
            created_at=data.get("created_at", ""),
            waid=data.get("waid", ""),
            role=data.get("role", ""),
        )

    def to_json(self) -> dict:
        """
        Convierte la instancia de MessageDataType en un diccionario JSON.
        """
        return {
            "sender": self.sender,
            "content": self.content,
            "created_at": self.created_at,
            "waid": self.waid,
            "role": self.role,
        }

    def get_llm_legible_message(self) -> ChatMessage:
        return ChatMessage(
            role=self.role, content=self.content
        )

class UsersCollection:
    def __init__(
        self,
        name: str,
        phone: str,
        last_interaction: str,
        messages: List[MessageDataType],
        last_message: Optional[MessageDataType],
    ):
        self.name = name
        self.phone = phone
        self.last_interaction = last_interaction
        self.messages = messages
        self.last_message = last_message

    @classmethod
    def from_json(cls, data: dict) -> "UsersCollection":
        """
        Crea una instancia de UsersCollection a partir de un diccionario JSON.
        """
        return cls(
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            last_interaction=data.get("last_interaction", ""),
            messages=[
                MessageDataType.from_json(msg) for msg in data.get("messages", [])
            ],
            last_message=(
                MessageDataType.from_json(data.get("last_message"))
                if data.get("last_message")
                else None
            ),
        )

    def to_json(self) -> dict:
        """
        Convierte la instancia de UsersCollection en un diccionario JSON.
        """
        return {
            "name": self.name,
            "phone": self.phone,
            "last_interaction": self.last_interaction,
            "messages": [msg.to_json() for msg in self.messages],
            "last_message": self.last_message.to_json() if self.last_message else None,
        }

    # def get_messages_list_for_llm(self) -> list[ChatMessage]:
    #     messages = [msg.get_llm_legible_message() for msg in self.messages]

    #     return ChatTemplate(messages=messages)

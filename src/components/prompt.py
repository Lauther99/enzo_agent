
class ChatMessage:
    def __init__(self, role: str, content: str):
        self.role: str = role
        self.content: str = content
        
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content
        }

class ChatTemplate:
    def __init__(
        self,
        *,
        messages: list[ChatMessage],
    ):
        self.messages: list[ChatMessage] = messages
        
    def get_messages_dict(self):
        return [item.to_dict() for item in self.messages]
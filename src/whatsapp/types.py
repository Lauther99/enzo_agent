from typing import List, Optional, Union


class Profile:
    def __init__(self, name: str):
        self.name = name

    @classmethod
    def from_json(cls, data: dict):
        return cls(name=data.get("name", ""))
    
    def to_json(self):
        return {"name": self.name}


class Contact:
    def __init__(self, profile: Profile, wa_id: str):
        self.profile = profile
        self.wa_id = wa_id

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            profile=Profile.from_json(data.get("profile", {})),
            wa_id=data.get("wa_id", ""),
        )
    
    def to_json(self):
        return {
            "profile": Profile.to_json(self.profile),
            "wa_id": self.wa_id,
        }


class Context:
    def __init__(self, from_: str, id: str):
        self.from_ = from_
        self.id = id
    
    @classmethod
    def from_json(cls, data: dict):
        return cls(
            from_=data.get("from", ""),
            id=data.get("id", ""),
        )

    def to_json(self):
        return {
            "from": self.from_,
            "id": self.id,
        }


class Text:
    def __init__(self, body: str):
        self.body = body

    @classmethod
    def from_json(cls, data: dict):
        return cls(body=data.get("body", ""))
    
    def to_json(self):
        return {"body": self.body}


class Button:
    def __init__(self, text: str, payload: str):
        self.text = text
        self.payload = payload

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            text=data.get("text", ""),
            payload=data.get("payload", ""),
        )
    
    def to_json(self):
        return {
            "text": self.text,
            "payload": self.payload,
        }


class Image:
    def __init__(self, id: str, caption: str, mime_type: str, sha256: str):
        self.id = id
        self.caption = caption
        self.mime_type = mime_type
        self.sha256 = sha256
    
    @classmethod
    def from_json(cls, data: dict):
        return cls(
            id=data.get("id", ""),
            caption=data.get("caption", ""),
            mime_type=data.get("mime_type", ""),
            sha256=data.get("sha256", ""),
        )
    
    def to_json(self):
        return {
            "id": self.id,
            "caption": self.caption,
            "mime_type": self.mime_type,
            "sha256": self.sha256,
        }


class Message:
    def __init__(
        self,
        context: Context,
        from_: str,
        id: str,
        timestamp: str,
        text: Text,
        button: Button,
        type: str,
        image: Image,
    ):
        self.context = context
        self.from_ = from_
        self.id = id
        self.timestamp = timestamp
        self.text = text
        self.button = button
        self.type = type
        self.image = image
    
    @classmethod
    def from_json(cls, data: dict):
        return cls(
            context=Context.from_json(data.get("context", {})),
            from_=data.get("from", ""),
            id=data.get("id", ""),
            timestamp=data.get("timestamp", ""),
            text=Text.from_json(data.get("text", {})),
            button=Button.from_json(data.get("button", {})),
            type=data.get("type", ""),
            image=Image.from_json(data.get("image", {})),
        )
    
    def to_json(self):
        return {
            "context": Context.to_json(self.context),
            "from": self.from_,
            "id": self.id,
            "timestamp": self.timestamp,
            "text": Text.to_json(self.text),
            "button": Button.to_json(self.button),
            "type": self.type,
            "image": Image.to_json(self.image),
        }


class Status:
    def __init__(self, id: str):
        self.id = id

    @classmethod
    def from_json(cls, data: dict):
        return cls(id=data.get("id", ""))
    
    def to_json(self):
        return {"id": self.id}


class Metadata:
    def __init__(self, display_phone_number: str, phone_number_id: str):
        self.display_phone_number = display_phone_number
        self.phone_number_id = phone_number_id
    
    @classmethod
    def from_json(cls, data: dict):
        return cls(
            display_phone_number=data.get("display_phone_number", ""),
            phone_number_id=data.get("phone_number_id", ""),
        )
    
    def to_json(self):
        return {
            "display_phone_number": self.display_phone_number,
            "phone_number_id": self.phone_number_id,
        }


class Value:
    def __init__(
        self,
        messaging_product: str,
        metadata: Metadata,
        contacts: List[Contact],
        messages: List[Message],
        statuses: List[Status],
    ):
        self.messaging_product = messaging_product
        self.metadata = metadata
        self.contacts = contacts
        self.messages = messages
        self.statuses = statuses

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            messaging_product=data.get("messaging_product", ""),
            metadata=Metadata.from_json(data.get("metadata", {})),
            contacts=[Contact.from_json(contact) for contact in data.get("contacts", [])],
            messages=[Message.from_json(message) for message in data.get("messages", [])],
            statuses=[Status.from_json(status) for status in data.get("statuses", [])],
        )
    
    def to_json(self):
        return {
            "messaging_product": self.messaging_product,
            "metadata": Metadata.to_json(self.metadata),
            "contacts": [Contact.to_json(contact) for contact in self.contacts],
            "messages": [Message.to_json(message) for message in self.messages],
            "statuses": [Status.to_json(status) for status in self.statuses],
        }


class Change:
    def __init__(self, value: Value, field: str):
        self.value = value
        self.field = field

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            value=Value.from_json(data.get("value", {})),
            field=data.get("field", ""),
        )
    
    def to_json(self):
        return {
            "value": Value.to_json(self.value),
            "field": self.field,
        }

class Entry:
    def __init__(self, id: str, changes: List[Change]):
        self.id = id
        self.changes = changes
    
    @classmethod
    def from_json(cls, data: dict):
        return cls(
            id=data.get("id", ""),
            changes=[Change.from_json(change) for change in data.get("changes", [])],
        )
    
    def to_json(self):
        return {
            "id": self.id,
            "changes": [Change.to_json(change) for change in self.changes],
        }


class WhatsAppMessage:
    def __init__(self, object: str, entry: List[Entry]):
        self.object = object
        self.entry = entry
    
    @classmethod
    def from_json(cls, data: dict):
        return cls(
            object=data.get("object", ""),
            entry=[Entry.from_json(entry) for entry in data.get("entry", [])],
        )
    
    def to_json(self):
        return {
            "object": self.object,
            "entry": [Entry.to_json(entry) for entry in self.entry],
        }


class MessageInfo:
    def __init__(self, content: str, type: str, time: str, role: str, username: str):
        self.content = content
        self.type = type
        self.time = time
        self.role = role
        self.username = username

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            content=data.get("content", ""),
            type=data.get("type", ""),
            time=data.get("time", ""),
            role=data.get("role", ""),
            username=data.get("username", ""),
        )
    
    def to_json(self):
        return {
            "content": self.content,
            "type": self.type,
            "time": self.time,
            "role": self.role,
            "username": self.username,
        }


class Props:
    def __init__(
        self,
        id: str,
        context: Context,
        messageInfo: MessageInfo,
        userPhoneNumber: str,
        botPhoneNumber: str,
        botPhoneNumberId: str,
    ):
        self.id = id
        self.context = context
        self.messageInfo = messageInfo
        self.userPhoneNumber = userPhoneNumber
        self.botPhoneNumber = botPhoneNumber
        self.botPhoneNumberId = botPhoneNumberId

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            id=data.get("id", ""),
            context=Context.from_json(data.get("context", {})),
            messageInfo=MessageInfo.from_json(data.get("messageInfo", {})),
            userPhoneNumber=data.get("userPhoneNumber", ""),
            botPhoneNumber=data.get("botPhoneNumber", ""),
            botPhoneNumberId=data.get("botPhoneNumberId", ""),
        )
    
    def to_json(self):
        return {
            "id": self.id,
            "context": Context.to_json(self.context),
            "messageInfo": MessageInfo.to_json(self.messageInfo),
            "userPhoneNumber": self.userPhoneNumber,
            "botPhoneNumber": self.botPhoneNumber,
            "botPhoneNumberId": self.botPhoneNumberId,
        }
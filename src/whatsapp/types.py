import logging
from typing import List, Optional, Union
from typing import Optional, Any, Dict


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

class Audio:
    def __init__(self, mime_type: str, sha256: str, id: str, voice: bool):
        self.mime_type = mime_type
        self.sha256 = sha256
        self.id = id
        self.voice = voice

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            mime_type=data.get("mime_type", ""),
            sha256=data.get("sha256", ""),
            id=data.get("id", ""),
            voice=data.get("voice", ""),
        )

    def to_json(self):
        return {
            "mime_type": self.mime_type,
            "sha256": self.sha256,
            "id": self.id,
            "voice": self.voice,
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
        audio: Audio,
    ):
        self.context = context
        self.from_ = from_
        self.id = id
        self.timestamp = timestamp
        self.text = text
        self.button = button
        self.type = type
        self.image = image
        self.audio = audio
    
    @classmethod
    def from_json(cls, data: dict):
        return cls(
            context=Context.from_json(data.get("context", {})),
            from_=data.get("from", ""),
            id=data.get("id", ""),
            timestamp=data.get("timestamp", ""),
            type=data.get("type", ""),
            text=Text.from_json(data.get("text", {})),
            button=Button.from_json(data.get("button", {})),
            image=Image.from_json(data.get("image", {})),
            audio=Audio.from_json(data.get("audio", {})),
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
            "audio": Audio.to_json(self.audio),
        }
    
    def get_important_content(self) -> str:
        if self.type == "button":
            return self.text
        if self.type == "text":
            return self.text.body
        if self.type == "interactive":
            return "interactive"
        if self.type == "audio":
            return self.audio.id
            # interactive = message.get("interactive", {})
            # if "button_reply" in interactive:
            #     return interactive["button_reply"].get("title", "")
            # if "list_reply" in interactive:
            #     return interactive["list_reply"].get("title", "")
        return ""


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
    
    @classmethod
    def is_notification(cls, body_dict: Dict[str, Any]):
        body = cls.from_json(body_dict)
        try:
            for entry in body.entry:
                for change in entry.changes:
                    if not change.value.messages:
                        # no message, it's a notification
                        logging.info("Notification received, skipping")
                        return True
        except Exception as error:
            logging.error("isNotification failed", exc_info=True)
            return False
        return False

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
        id: str = None,
        context: Context = None,
        messageInfo: MessageInfo = None,
        userPhoneNumber: str = None,
        botPhoneNumber: str = None,
        botPhoneNumberId: str = None,
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
    
    @classmethod
    def filter_message_data(cls, body_json: Dict[str, Any]) -> "Props":
        bot_phone_number = ""
        bot_phone_number_id = ""
        user_phone_number = ""
        user_name = ""
        local_message = None
        context = None
        id = ""

        body = WhatsAppMessage.from_json(body_json)

        try:
            for entry in body.entry:
                for change in entry.changes:
                    if not change.value.messages:
                        continue

                    for message in change.value.messages:
                        if message.context:
                            context = {
                                "from": message.context.from_,
                                "id": message.context.id,
                            }

                        user_name = change.value.contacts[0].profile.name
                        user_phone_number = message.from_
                        bot_phone_number = change.value.metadata.display_phone_number
                        bot_phone_number_id = change.value.metadata.phone_number_id
                        id = message.id
                        local_message = message

                        if message.type not in ["text", "button", "interactive", "audio"]:
                            props_dict = {
                                "messageInfo": {
                                    "content": "not-allowed",
                                    "type": local_message.type if local_message else "",
                                    "time": (
                                        local_message.timestamp if local_message else ""
                                    ),
                                    "role": "user",
                                    "username": user_name,
                                },
                                "id": id,
                                "userPhoneNumber": user_phone_number,
                                "botPhoneNumber": bot_phone_number,
                                "botPhoneNumberId": bot_phone_number_id,
                            }

                            return cls.from_json(props_dict)
                        else:
                            message_info = {
                                "content": message.get_important_content(),
                                "type": message.type,
                                "time": message.timestamp,
                                "username": user_name,
                                "role": "user",
                            }
                            props_dict = {
                                "context": context,
                                "messageInfo": message_info,
                                "userPhoneNumber": user_phone_number,
                                "botPhoneNumber": bot_phone_number,
                                "botPhoneNumberId": bot_phone_number_id,
                                "id": id,
                            }
                            return cls.from_json(props_dict)

        except Exception as e:
            print("isAllowedTypeMessage failed", e)

            props_dict = {
                "messageInfo": {
                    "content": "not-allowed",
                    "type": local_message.type if local_message else "",
                    "time": local_message.timestamp if local_message else "",
                    "username": user_name,
                    "role": "user",
                },
                "id": id,
                "userPhoneNumber": user_phone_number,
                "botPhoneNumber": bot_phone_number,
                "botPhoneNumberId": bot_phone_number_id,
            }

        return cls.from_json(props_dict)

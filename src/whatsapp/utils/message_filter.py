from typing import Optional, Any, Dict
import src.whatsapp.types as wsp_types


def get_text_from_message(message: wsp_types.Message) -> str:
    if message and message.type == "button":
        return message.button.text
    if message and message.type == "text":
        return message.text.body
    if message and message.type == "interactive":
        return "interactive"
        # interactive = message.get("interactive", {})
        # if "button_reply" in interactive:
        #     return interactive["button_reply"].get("title", "")
        # if "list_reply" in interactive:
        #     return interactive["list_reply"].get("title", "")
    return ""


def filter_message_data(body_json: Dict[str, Any]) -> wsp_types.Props:
    bot_phone_number = ""
    bot_phone_number_id = ""
    user_phone_number = ""
    user_name = ""
    local_message = None
    context = None
    id = ""

    body = wsp_types.WhatsAppMessage.from_json(body_json)

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

                    if message.type not in ["text", "button", "interactive"]:
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

                        return wsp_types.Props.from_json(props_dict)
                    else:
                        message_info = {
                            "content": get_text_from_message(message),
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
                        return wsp_types.Props.from_json(props_dict)

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

    return wsp_types.Props.from_json(props_dict)

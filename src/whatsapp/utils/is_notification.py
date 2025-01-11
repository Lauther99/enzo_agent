
import logging
from typing import Optional, Any, Dict
import src.whatsapp.types as wsp_types


def is_notification(body_dict: Dict[str, Any]):
    body = wsp_types.WhatsAppMessage.from_json(body_dict)

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
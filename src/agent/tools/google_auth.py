from src.agent.tools.collectors import Collector, GoogleAuthToolCollector
from src.components.tool import set_action
import logging
import uuid
import time as time_library
from src.components.memory import Memory
from src.firebase.users_manager import UserManager
from src.google.google_services import (
    google_login,
)


def tool_workflow(memory: Memory):
    user_manager: UserManager = memory.user_manager
    auth_url = google_login(user_manager)
    message = f"Para que el usuario pueda autenticarse con google, pídele que ingrese al siguiente URL: {auth_url}"
    logging.info(message)

    return {"response": message}


@set_action
def google_auth_url(need_login: bool, **kwargs) -> dict:
    """
    To generate a Google authentication URL for user login or re-authentication.
    Use this tool only when the user or a tool asks to authenticate or reauthenticate with Google.
    It returns a dictionary containing the authentication URL.

    Args:
        need_login: A boolean indicating whether the user needs to log in (True) or if login is optional (False).
    """
    call_id = f"""tool-call--{uuid.uuid4().hex}"""

    collector: Collector = kwargs.get("collector", Collector())
    collector.add_tool_collector(GoogleAuthToolCollector, call_id)
    collector.set_last_tool_call_id(call_id=call_id)

    memory: Memory = kwargs.get("memory")

    res_dict = tool_workflow(memory)

    tool_collector: GoogleAuthToolCollector = collector.ToolsCollector[call_id]

    params = {
        "call_id": call_id,
        "tool_name": "google_auth_url",
    }
    start_time = time_library.time()
    try:
        params["tool_response"] = res_dict
        params["tool_friendly_response"] = res_dict
        params["response_type"] = str
    except Exception as e:
        params.update(
            {
                "tool_response": f"response: {str(e)}",
                "response_type": Exception,
                "tool_friendly_response": {"response": {e}},
            }
        )
        logging.info(f"Error en la tool 'google_auth_url': {e}")

    finally:
        c = tool_collector or GoogleAuthToolCollector()
        end_time = time_library.time()
        elapsed_time = end_time - start_time
        params["usage"] = {"response_time": elapsed_time}

        tool_response = c.add_tool_response(**params)
        return tool_response

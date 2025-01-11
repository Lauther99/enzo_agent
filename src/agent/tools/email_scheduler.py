from src.agent.tools.collectors import Collector, EmailScheduleToolCollector
from src.components.tool import set_action
import logging
import uuid
import time as time_library
from google.cloud import firestore
from src.components.memory import Memory
from src.firebase.users_manager import get_creds_from_firebase, CredsResponse
from src.google.google_services import (
    refresh_access_token,
    google_login,
    send_google_email,
)
from google.oauth2.credentials import Credentials


def tool_workflow(
    db: firestore.Client,
    phone_number,
    memory: Memory,
    *,
    to_emails: str,
    subject: str,
    body: str,
    date: str,
    time: str,
):
    firebase_response: CredsResponse = get_creds_from_firebase(db, phone_number)
    user_ref = memory.user_ref
    res = send_email(
        db,
        phone_number,
        user_ref,
        need_login=firebase_response.need_login,
        credentials=firebase_response.response,
        to_emails=to_emails,
        subject=subject,
        body=body,
        date=date,
        time=time
    )
    return res


def send_email(
    db,
    phone_number,
    user_ref,
    *,
    need_login=False,
    credentials: Credentials = None,
    to_emails: str,
    subject: str,
    body: str,
    date: str,
    time: str,
):
    if need_login:
        auth_url = google_login(user_ref, phone_number)
        message = f"""User must login, please ask him to got to this url: {auth_url}"""
        return {"response": message}
    else:
        credentials = refresh_access_token(credentials)
        if not credentials:
            send_email(db, phone_number, True)
        r = send_google_email(credentials, to_emails, subject, body)
        return r


@set_action
def email_scheduler(
    to_emails: str, date: str, time:str, subject: str, body: str, **kwargs
) -> dict:
    """
    To schedule and send an email to one or more guests using an email API.
    Only call this tool if user has provided all arguments necessary, else you should ask him.
    Always ask for a confirmation before sending the email.
    It returns a response object from the email API.

    Args:
        to_emails: Comma separated list of guest email addresses.
        date: Scheduled date and time in YYYY-MM-DD format or use NOW to send at the moment.
        time: Scheduled time in HH:MM:SS format or use NOW to send at the moment.
        subject: The subject line of the email.
        body: A **markdown** content for the body of the email.
    """
    call_id = f"""tool-call--{uuid.uuid4().hex}"""

    collector: Collector = kwargs.get("collector", Collector())
    collector.add_tool_collector(EmailScheduleToolCollector, call_id)
    collector.set_last_tool_call_id(call_id=call_id)

    phone_number = kwargs.get("user_phone", Collector())
    db: firestore.Client = kwargs.get("db", Collector())
    memory: Memory = kwargs.get("memory")

    res_dict = tool_workflow(
        db,
        phone_number,
        memory,
        to_emails=to_emails,
        subject=subject,
        body=body,
        date=date,
        time=time
    )

    # res_dict = tool_workflow_from_variables(
    #     measurement_system_name, measurement_system_tag, variable_name, date
    # )

    tool_collector: EmailScheduleToolCollector = collector.ToolsCollector[call_id]

    params = {
        "call_id": call_id,
        "tool_name": "EmailSchedule",
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
        logging.info(f"Error en la tool 'EmailSchedule': {e}")

    finally:
        c = tool_collector or EmailScheduleToolCollector()
        end_time = time_library.time()
        elapsed_time = end_time - start_time
        params["usage"] = {"response_time": elapsed_time}

        tool_response = c.add_tool_response(**params)
        return tool_response

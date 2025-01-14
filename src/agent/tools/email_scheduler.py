from src.agent.tools.collectors import Collector, BaseToolCollector
from src.components.tool import set_action
import logging
import uuid
import time as time_library
from src.components.memory import Memory
from src.firebase.users_manager import CredsResponse, UserManager
from src.google.google_services import (
    refresh_access_token,
    google_login,
    send_google_email,
)
from google.oauth2.credentials import Credentials
from src.scheduler.scheduler import schedule_task
from src.utils.utils import convertir_a_datetime
from datetime import datetime
import re


def tool_workflow(
    memory: Memory,
    *,
    to_emails: str,
    subject: str,
    body: str,
    date_time: datetime,
):
    user_manager: UserManager = memory.user_manager
    firebase_response: CredsResponse = user_manager.get_creds_from_firebase()

    res = tool_callback(
        user_manager,
        need_login=firebase_response.need_login,
        credentials=firebase_response.response,
        to_emails=to_emails,
        subject=subject,
        body=body,
        scheduled_time=date_time,
    )
    return res


def tool_callback(
    user_manager: UserManager,
    *,
    need_login=False,
    credentials: Credentials = None,
    to_emails: str,
    subject: str,
    body: str,
    scheduled_time: datetime,
):
    now = datetime.now()

    try:
        # Autenticación si es necesario
        if need_login:
            auth_url = google_login(user_manager)
            message = f"El usuario se debe autenticar en google, por favor pídele que ingrese al siguiente URL para que pueda atenticarse en google: {auth_url}"
            logging.info(message)
            return {"response": message}

        credentials = refresh_access_token(credentials)
        user_manager.save_jwt_to_firebase(credentials)

        if not credentials:
            logging.error(
                "Credenciales no disponibles o no válidas. Requiere inicio de sesión."
            )
            return tool_callback(
                user_manager=user_manager,
                need_login=True,
                to_emails=to_emails,
                subject=subject,
                body=body,
                scheduled_time=scheduled_time,
            )

        # Preparar argumentos para enviar el correo
        kwargs = {
            "c": credentials,
            "to_emails": to_emails,
            "subject": subject,
            "body": body,
        }

        # Enviar inmediatamente si la hora ya pasó
        if scheduled_time <= now:
            logging.info("El tiempo ya se venció. Correo enviado inmediatamente.")
            r = send_google_email(**kwargs)
            return r

        # Programar el correo

        s_response = schedule_task(
            func=send_google_email, kwargs=kwargs, date=scheduled_time
        )
        if s_response.success:
            logging.info(f"Correo agendado para {scheduled_time}.")
            return {
                "success": True,
                "message": f"Correo agendado, se enviará el {scheduled_time.strftime('día %B %d, %Y, a las %H:%M:%S')}",
            }
        else:
            logging.error(f"Error al agendar el correo: {s_response.message}")
            return {
                "success": False,
                "message": f"Un error ocurrió al momento de agendar el correo: {s_response.message}",
            }

    except Exception as e:
        logging.exception("Ocurrió un error inesperado en send_email.")
        return {"success": False, "message": f"Error inesperado: {str(e)}"}


@set_action
def email_scheduler(
    to_emails: str, date: str, time: str, subject: str, body: str, **kwargs
) -> dict:
    """To schedule and send an email to one or more guests using an email API.
Only call this tool if user has provided all arguments necessary, else you should ask him.
Always ask for a confirmation before sending the email.
It returns a response object from the email API.

Args:
    to_emails: Comma separated list of guest email addresses.
    date: Scheduled date and time in YYYY-MM-DD format or use NOW to send at the moment.
    time: Scheduled time in HH:MM:SS format or use NOW to send at the moment.
    subject: The subject line of the email.
    body: The content for the body of the email.
"""
    # Validamos argumentos
    is_valid, message = validate_args(
        to_emails=to_emails, date=date, time=time, subject=subject, body=body
    )

    # Generamos un call id
    call_id = f"tool-call--{uuid.uuid4().hex}"

    # Setup de los collectors
    collector: Collector = kwargs.get("collector", Collector())
    collector.add_tool_collector(BaseToolCollector, call_id)
    collector.set_last_tool_call_id(call_id=call_id)

    # Setup de la memoria y otros parametros
    memory: Memory = kwargs.get("memory")
    params = {
        "call_id": call_id,
        "tool_name": "email_scheduler",
    }

    if is_valid:
        # Preparacion antes del workflow
        tool_collector: BaseToolCollector = collector.ToolsCollector[call_id]
        date_time = convertir_a_datetime(date=date, time=time)
        start_time = time_library.time()

        try:
            # Execute workflow
            response_dict = tool_workflow(
                memory,
                to_emails=to_emails,
                subject=subject,
                body=body,
                date_time=date_time,
            )

            # Manejamos la respuesta
            params.update(
                {
                    "tool_response": response_dict,
                    "tool_friendly_response": response_dict,
                    "response_type": dict,
                }
            )

        except Exception as e:
            # Manejamos el error
            logging.error(f"Error in tool 'email_scheduler': {e}")
            params.update(
                {
                    "tool_response": f"response: {str(e)}",
                    "response_type": Exception,
                    "tool_friendly_response": {"response": str(e)},
                }
            )

        finally:
            # Toques finales
            end_time = time_library.time()
            elapsed_time = end_time - start_time
            params["usage"] = {"response_time": elapsed_time}
            return (tool_collector or BaseToolCollector()).add_tool_response(
                **params
            )

    else:
        # Manejando un input invalido
        params.update(
            {
                "tool_response": {"response": message},
                "tool_friendly_response": {"response": message},
                "response_type": dict,
            }
        )
        return (
            collector.ToolsCollector.get(call_id) or BaseToolCollector()
        ).add_tool_response(**params)


def validate_args(
    to_emails: str, date: str, time: str, subject: str, body: str
) -> tuple[bool, str]:
    
    # Check email
    if not to_emails:
        return False, "The 'to_emails' field cannot be empty."

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    email_list = to_emails.split(",")
    for email in email_list:
        email = email.strip()
        if not re.match(email_pattern, email):
            return False, f"Invalid email address: {email}"

    # Check date
    if date.upper() != "NOW":
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return False, "The 'date' field must be in YYYY-MM-DD format or 'NOW'."

    # Check time
    if time.upper() != "NOW":
        try:
            datetime.strptime(time, "%H:%M:%S")
        except ValueError:
            return False, "The 'time' field must be in HH:MM:SS format or 'NOW'."

    # Check subject
    if not subject.strip():
        return False, "The 'subject' field cannot be empty."

    # Check body
    if not body.strip():
        return False, "The 'body' field cannot be empty."

    return True, "Valid"

from src.agent.tools.collectors import Collector, EmailScheduleToolCollector
from src.components.tool import set_action
import logging
import uuid
import time as time_library
from google.cloud import firestore
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


def tool_workflow(
    db: firestore.Client,
    phone_number,
    memory: Memory,
    *,
    to_emails: str,
    subject: str,
    body: str,
    date_time: datetime,
):
    user_manager: UserManager = memory.user_manager
    firebase_response: CredsResponse = user_manager.get_creds_from_firebase()

    res = send_email(
        user_manager,
        need_login=firebase_response.need_login,
        credentials=firebase_response.response,
        to_emails=to_emails,
        subject=subject,
        body=body,
        scheduled_time=date_time,
    )
    return res


def send_email(
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
        if not credentials:
            logging.error("Credenciales no disponibles o no válidas. Requiere inicio de sesión.")
            return send_email(
                user_manager=user_manager,
                need_login=True, 
                to_emails=to_emails, 
                subject=subject, 
                body=body, 
                scheduled_time=scheduled_time
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


        s_response = schedule_task(func=send_google_email, kwargs=kwargs, date=scheduled_time)
        if s_response.response:
            logging.info(f"Correo agendado para {scheduled_time}.")
            return {
                "success": True,
                "message": f"Correo agendado, se enviará el {scheduled_time.strftime('día %B %d, %Y, a las %H:%M:%S')}",
            }
        else:
            logging.error(f"Error al agendar el correo: {s_response.message}")
            return {
                "failed": True,
                "message": f"Un error ocurrió al momento de agendar el correo: {s_response.message}",
            }

    except Exception as e:
        logging.exception("Ocurrió un error inesperado en send_email.")
        return {"failed": True, "message": f"Error inesperado: {str(e)}"}


@set_action
def email_scheduler(
    to_emails: str, date: str, time: str, subject: str, body: str, **kwargs
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

    date_time = convertir_a_datetime(date=date, time=time)

    res_dict = tool_workflow(
        db,
        phone_number,
        memory,
        to_emails=to_emails,
        subject=subject,
        body=body,
        date_time=date_time,
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

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
    list_calendar_events,
    edit_calendar_event,
    create_calendar_event,
)
from google.oauth2.credentials import Credentials
from src.utils.utils import convert_to_timezone
from datetime import datetime
from typing import Optional


def tool_workflow(
    memory: Memory,
    action: str,
    *,
    # Parametros para listar:
    date_min: str = None,
    date_max: str = None,
    # Parametros para editar/crear:
    event_id: str = None,
    summary: str = None,
    description: str = None,
    datetime_start: str = None,
    datetime_end: str = None,
    attendees_emails: str = None,
    has_conference: bool = True,
):
    user_manager: UserManager = memory.user_manager
    firebase_response: CredsResponse = user_manager.get_creds_from_firebase()

    res = tool_callback(
        user_manager,
        action,
        need_login=firebase_response.need_login,
        credentials=firebase_response.response,
        date_min=date_min,
        date_max=date_max,
        event_id=event_id,
        summary=summary,
        description=description,
        datetime_start=datetime_start,
        datetime_end=datetime_end,
        attendees_emails=attendees_emails,
        has_conference=has_conference,
    )

    return res


def tool_callback(
    user_manager: UserManager,
    action: str,
    *,
    need_login: bool = False,
    credentials: Credentials = None,
    # Parametros para listar:
    date_min: str = None,
    date_max: str = None,
    # Parametros para editar/crear:
    event_id: str = None,
    summary: str = None,
    description: str = None,
    datetime_start: str = None,
    datetime_end: str = None,
    attendees_emails: str = None,
    has_conference: bool = True,
):
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
                date_min=date_min,
                date_max=date_max,
            )

        if action == "list_events":
            # Preparar argumentos para listar eventos
            kwargs = {
                "creds": credentials,
                "date_min": date_min,
                "date_max": date_max,
            }
            events = list_calendar_events(**kwargs)

            if events:
                events_formatted_to_dict = [e.to_dict() for e in events]
                return {
                    "success": True,
                    "message": f"{len(events)} were found. Do not share the event ID with the user.",
                    "content": events_formatted_to_dict,
                }

            else:
                return {"success": True, "message": "No events found."}

        if action == "edit_event":
            # Preparar argumentos para listar eventos
            kwargs = {
                "user_credentials": credentials,
                "event_id": event_id,
                "summary": summary,
                "description": description,
                "datetime_start": datetime_start,
                "datetime_end": datetime_end,
                "attendees_emails": attendees_emails,
                "has_conference": has_conference,
            }
            event = edit_calendar_event(**kwargs)

            if event:
                event_formatted_to_dict = event.to_dict()
                return {
                    "success": True,
                    "message": f"The were updated. Do not share the event ID with the user.",
                    "content": event_formatted_to_dict,
                }

            else:
                return {
                    "success": False,
                    "message": "Error al actualizar el evento, contacte con el administrador.",
                }

        if action == "create_event":
            # Preparar argumentos para listar eventos
            kwargs = {
                "user_credentials": credentials,
                "summary": summary,
                "description": description,
                "datetime_start": datetime_start,
                "datetime_end": datetime_end,
                "attendees_emails": attendees_emails,
            }
            event_created = create_calendar_event(**kwargs)

            if event_created:
                event_formatted_to_dict = event_created.to_dict()
                return {
                    "success": True,
                    "message": f"The event has been created succesfully. Do not share the event ID with the user.",
                    "content": event_formatted_to_dict,
                }
            else:
                return {
                    "success": False,
                    "message": "Error al crear el evento, contacte con el administrador.",
                }

    except Exception as e:
        logging.exception(f"Ocurrió un error inesperado en en la funcion {action}.")
        return {"failed": True, "message": f"Error inesperado en {action}: {str(e)}"}


@set_action
def list_events(date_min: str, date_max: str, **kwargs) -> dict:
    """Retrieves a list of events from a user's Google Calendar within a specified date range. This function interacts with the Google Calendar API to fetch events occurring between the provided start and end dates.
    It returns a response object from the Calendar API. The response includes details such as event id, titles, times, attendees, and descriptions.

        Args:
            date_min: The earliest date to retrieve events, in 'YYYY-MM-DD' format. Only events occurring on or after this date will be included.
            date_max: The latest date to retrieve events, in 'YYYY-MM-DD' format. Only events occurring on or before this date will be included.
    """
    # Validamos argumentos
    is_valid, message = validate_list_events_args(date_min=date_min, date_max=date_max)

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
        "tool_name": "list_events",
    }

    if is_valid:
        # Preparacion antes del workflow
        tool_collector: BaseToolCollector = collector.ToolsCollector[call_id]
        start_time = time_library.time()

        try:
            # Execute workflow
            timeMin = convert_to_timezone(date_min)
            timeMax = convert_to_timezone(date_max)
            response_dict = tool_workflow(
                memory, "list_events", date_min=timeMin, date_max=timeMax
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
            return (tool_collector or BaseToolCollector()).add_tool_response(**params)

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


@set_action
def manage_events(
    action: str = "edit_event",
    datetime_start: str = None,
    datetime_end: str = None,
    event_id: Optional[str] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    attendees_emails: Optional[str] = None,
    has_conference: Optional[bool] = True,
    **kwargs,
) -> dict:
    """Manages calendar events in Google Calendar by editing or creating events.
    This function interacts with the Calendar API to either update an existing event or create a new one based on the specified action.
    It returns the updated or newly created event data from the Calendar API.

        Args:
            action: The operation to perform. Use 'edit_event' to edit an existing event this requires an `event_id`. However use 'create_event' to creates a new event in this case `event_id` should be None.
            datetime_start: The start date and time of the event in 'YYYY-MM-DD HH:MM:SS' format. Required for both actions.
            datetime_end: The end date and time of the event in 'YYYY-MM-DD HH:MM:SS' format. Required for both actions.
            event_id: The unique ID of the event to be edited. Required if `action` is 'edit_event'.
            summary: A short title or summary of the event.
            description: A detailed description of the event.
            attendees_emails: A comma-separated list of email addresses for the event attendees.
            has_conference: Indicates whether to include a conference link (e.g., Google Meet) in the event. Defaults to True.
    """

    # Validamos argumentos
    is_valid, message = validate_manage_events_args(
        action=action,
        event_id=event_id,
        datetime_start=datetime_start,
        datetime_end=datetime_end,
        attendees_emails=attendees_emails,
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
        "tool_name": "list_events",
    }

    if is_valid:
        # Preparacion antes del workflow
        tool_collector: BaseToolCollector = collector.ToolsCollector[call_id]
        start_time = time_library.time()

        try:
            # Execute workflow
            response_dict = tool_workflow(
                memory,
                action,
                event_id=event_id,
                summary=summary,
                description=description,
                datetime_start=datetime_start,
                datetime_end=datetime_end,
                attendees_emails=attendees_emails,
                has_conference=has_conference,
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
            return (tool_collector or BaseToolCollector()).add_tool_response(**params)

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


def validate_list_events_args(date_min: str, date_max: str) -> tuple:
    """
    Validates the arguments for the list_events function.

    Args:
        date_min (str): The earliest date to retrieve events, in 'YYYY-MM-DD' format.
        date_max (str): The latest date to retrieve events, in 'YYYY-MM-DD' format.

    Returns:
        tuple: A tuple containing a boolean indicating validity and a message.
    """
    # Check if both dates are provided
    if not date_min or not date_max:
        return False, "Both 'date_min' and 'date_max' must be provided."

    # Validate date format
    try:
        date_min_obj = datetime.strptime(date_min, "%Y-%m-%d")
        date_max_obj = datetime.strptime(date_max, "%Y-%m-%d")
    except ValueError:
        return False, "Dates must be in 'YYYY-MM-DD' format."

    # Check if date_min is not after date_max
    if date_min_obj > date_max_obj:
        return False, "'date_min' cannot be later than 'date_max'."

    return True, "Validation successful."


def validate_manage_events_args(
    action: str,
    event_id: Optional[str],
    datetime_start: Optional[str],
    datetime_end: Optional[str],
    attendees_emails: str,
    **kwargs
) -> tuple:
    """
    Validates the arguments for the manage_events function.

    Args:
        action (str): The operation to perform ('edit_event' or 'create_event').
        datetime_start (str, optional): The start date and time in 'YYYY-MM-DD HH:MM:SS' format.
        datetime_end (str, optional): The end date and time in 'YYYY-MM-DD HH:MM:SS' format.
        event_id (str, optional): The ID of the event to be edited. Required for 'edit_event'.

    Returns:
        tuple: A tuple containing a boolean indicating validity and a message.
    """

    # Validate action
    if action not in ["edit_event", "create_event"]:
        return False, "Invalid action. Use 'edit_event' or 'create_event'."

    # Validate datetime_start and datetime_end
    try:
        start = datetime.strptime(datetime_start, "%Y-%m-%d %H:%M:%S") if datetime_start else None
        end = datetime.strptime(datetime_end, "%Y-%m-%d %H:%M:%S") if datetime_end else None
        if start and end and start >= end:
            return False, "The start time must be earlier than the end time."
    except ValueError:
        return False, "Invalid date format. Use 'YYYY-MM-DD HH:MM:SS'."

    # Validate event_id for edit_event
    if action == "edit_event" and not event_id:
        return False, "'event_id' is required for action 'edit_event'."
    
    if attendees_emails:
        email_list = attendees_emails.split(",")
        for email in email_list:
            if "@" not in email or "." not in email:
                return False, f"Invalid email format: {email}"

    return True, "Validation successful."

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
import time
from typing import Callable, Any, Dict
import logging
from dataclasses import dataclass

scheduler = BackgroundScheduler()

@dataclass
class SchedulerResponse:
    response: bool
    message: str


def schedule_task(func: Callable[..., Any], kwargs: dict = {}, *, date: datetime) -> SchedulerResponse:
    try:
        # Validar que `func` es llamable
        if not callable(func):
            raise ValueError("El parámetro `func` debe ser una función llamable.")

        # Validar que `date` no esté en el pasado
        if date < datetime.now():
            raise ValueError("La fecha proporcionada está en el pasado.")

        # Agregar la tarea al scheduler
        scheduler.add_job(
            func,
            trigger=DateTrigger(run_date=date),
            kwargs=kwargs,  # Argumentos nombrados
        )
        m = f"Tarea programada para: {date}. Función: {func.__name__}, kwargs: {kwargs}"
        logging.info(m)

        return SchedulerResponse(response=True, message=m)

    except Exception as e:
        m = f"Error al programar la tarea: {str(e)}"
        logging.error(m)
        return SchedulerResponse(response=False, message=m)

def schedule_chat_manager(chat_manager: Callable[..., Any], db, message_data):
    logging.info("Agendando chat_manager para procesamiento en segundo plano.")
    now=datetime.now()
    scheduler.add_job(chat_manager, 'date', run_date=now, kwargs={'db': db, 'message_data': message_data})

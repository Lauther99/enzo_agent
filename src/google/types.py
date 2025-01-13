from datetime import datetime

class DecodeJWTResponse:
    def __init__(self, is_valid, response):
        self.is_valid = is_valid
        self.response = response


class CalendarEvent:
    def __init__(
        self,
        event_id: str,
        summary: str,
        description: str,
        start: str,
        end: str,
        attendees: list[str] = [],
        hangout_link: str | None = None,
    ):
        self.event_id = event_id
        self.summary = summary
        self.description = description
        self.start = start
        self.end = end
        self.attendees = attendees
        self.hangout_link = hangout_link

    def to_dict(self) -> dict:
        """
        Converts the CalendarEvent instance into a dictionary.

        Returns:
            dict: A dictionary representation of the CalendarEvent instance.
        """
        return {
            "event_id": self.event_id,
            "summary": self.summary,
            "description": self.description,
            "start": self._format_date(self.start, prefix="From"),
            "end": self._format_date(self.end, prefix="To"),
            "attendees": self.attendees,
            "hangout_link": self.hangout_link,
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        Creates a CalendarEvent instance from a dictionary.

        Args:
            data (dict): A dictionary containing the event data.

        Returns:
            CalendarEvent: An instance of the CalendarEvent class.
        """
        s=data.get("start", {}).get("dateTime", "")
        e=data.get("end", {}).get("dateTime", "")

        s = cls._format_date(s, prefix="From")
        e = cls._format_date(e, prefix="To")

        return cls(
            event_id=data.get("id", ""),
            summary=data.get("summary", ""),
            description=data.get("description", ""),
            start=s,
            end=e,
            attendees=data.get("attendees", []),
            hangout_link=data.get("hangoutLink", None),
        )
    
    @staticmethod
    def _format_date(date_str: str, prefix: str = "From") -> str:
        """
        Formats an ISO 8601 date string into a human-readable format in Spanish.
        
        Args:
            date_str (str): The date string in ISO 8601 format.
            prefix (str): A prefix like "Desde" or "Hasta".
        
        Returns:
            str: The formatted date string.
        """
        try:
            dt = datetime.fromisoformat(date_str)
            return f"{prefix} {dt.day}/{dt.strftime('%B')}/{dt.year} at {dt.strftime('%H:%M')}."
        except ValueError:
            return date_str

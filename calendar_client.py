"""
Google Calendar API client.
Creates events and invites all configured member emails.
"""

import os
import json
import logging
from datetime import datetime, timedelta, date

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Comma-separated list of member emails, e.g. "alice@gmail.com,bob@gmail.com"
MEMBER_EMAILS = [e.strip() for e in os.environ["MEMBER_EMAILS"].split(",") if e.strip()]

# The calendar to add events to (use 'primary' or a specific calendar ID)
CALENDAR_ID = os.environ.get("CALENDAR_ID", "primary")


def get_calendar_service():
    """Build Google Calendar service using service account credentials."""
    creds_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    creds_dict = json.loads(creds_json)

    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    service = build("calendar", "v3", credentials=creds)
    return service


def build_event_body(event_data: dict) -> dict:
    """Convert parsed event data into Google Calendar API event body."""

    title = event_data.get("title", "Event")
    date_str = event_data.get("date")  # YYYY-MM-DD
    time_str = event_data.get("time")  # HH:MM
    end_time_str = event_data.get("end_time")
    is_all_day = event_data.get("is_all_day", False)
    location = event_data.get("location")
    description = event_data.get("description")

    attendees = [{"email": email} for email in MEMBER_EMAILS]

    body = {
        "summary": title,
        "attendees": attendees,
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 60},
                {"method": "email", "minutes": 1440},  # 1 day before
            ],
        },
        "guestsCanSeeOtherGuests": True,
        "guestsCanInviteOthers": False,
    }

    if location:
        body["location"] = location

    if description:
        body["description"] = description

    if is_all_day or not time_str:
        # All-day event
        body["start"] = {"date": date_str}
        body["end"] = {"date": date_str}
    else:
        # Timed event
        start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

        if end_time_str:
            end_dt = datetime.strptime(f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M")
        else:
            end_dt = start_dt + timedelta(hours=1)

        # Use UTC — adjust if you want a specific timezone
        tz = os.environ.get("TIMEZONE", "Europe/Berlin")

        body["start"] = {"dateTime": start_dt.isoformat(), "timeZone": tz}
        body["end"] = {"dateTime": end_dt.isoformat(), "timeZone": tz}

    return body


def create_calendar_event(event_data: dict) -> tuple[str | None, str | None]:
    """
    Create a Google Calendar event.
    Returns (event_link, error_message).
    """
    try:
        service = get_calendar_service()
        body = build_event_body(event_data)

        logger.info(f"Creating calendar event: {body['summary']}")

        created_event = service.events().insert(
            calendarId=CALENDAR_ID,
            body=body,
            # Note: Service accounts can't send invites, but attendees are still added to the event
        ).execute()

        event_link = created_event.get("htmlLink", "https://calendar.google.com")
        logger.info(f"Event created: {event_link}")
        return event_link, None

    except HttpError as e:
        logger.error(f"Google Calendar API error: {e}")
        return None, f"Google Calendar error: {e.reason}"

    except Exception as e:
        logger.error(f"Unexpected error creating event: {e}")
        return None, str(e)

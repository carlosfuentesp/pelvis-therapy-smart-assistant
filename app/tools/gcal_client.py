import os
import json
import logging
import boto3
from datetime import timezone
from dateutil import parser as dtparser

from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
SECRET_NAME = os.environ.get("GCAL_SECRET_NAME", "pelvis/gcal/sa")
CALENDAR_ID = os.environ.get("GCAL_CALENDAR_ID", "")
TZ = os.environ.get("TZ", "America/Guayaquil")

_sa_cache = None
_svc_cache = None


def _get_sa():
    global _sa_cache
    if _sa_cache:
        return _sa_cache
    sm = boto3.client("secretsmanager")
    data = json.loads(sm.get_secret_value(SecretId=SECRET_NAME)["SecretString"])
    _sa_cache = service_account.Credentials.from_service_account_info(data, scopes=SCOPES)
    return _sa_cache


def _svc():
    global _svc_cache
    if _svc_cache:
        return _svc_cache
    _svc_cache = build("calendar", "v3", credentials=_get_sa(), cache_discovery=False)
    return _svc_cache


def iso_utc(s: str) -> str:
    """Normaliza a ISO UTC con 'Z'."""
    dt = dtparser.isoparse(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def is_free(start_iso_utc: str, end_iso_utc: str) -> bool:
    body = {
        "timeMin": start_iso_utc,
        "timeMax": end_iso_utc,
        "timeZone": TZ,
        "items": [{"id": CALENDAR_ID}],
    }
    resp = _svc().freebusy().query(body=body).execute()
    busy = resp["calendars"][CALENDAR_ID].get("busy", [])
    return len(busy) == 0


def create_event(
    summary: str, start_iso: str, end_iso: str, description: str, attendee_email: str | None = None
) -> dict:
    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_iso, "timeZone": TZ},
        "end": {"dateTime": end_iso, "timeZone": TZ},
    }
    if attendee_email:
        event["attendees"] = [{"email": attendee_email}]
    created = (
        _svc().events().insert(calendarId=CALENDAR_ID, body=event, sendUpdates="all").execute()
    )
    return {"id": created["id"], "htmlLink": created.get("htmlLink")}


def update_event(event_id: str, **fields) -> dict:
    ev = _svc().events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
    ev.update(fields)
    updated = (
        _svc()
        .events()
        .update(calendarId=CALENDAR_ID, eventId=event_id, body=ev, sendUpdates="all")
        .execute()
    )
    return {"id": updated["id"]}


def delete_event(event_id: str) -> None:
    _svc().events().delete(calendarId=CALENDAR_ID, eventId=event_id, sendUpdates="all").execute()

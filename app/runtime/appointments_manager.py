import os
import json
import logging
import boto3
from tools import gcal_client as gcal
from tools.whatsapp_owner import send_owner_template

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REMINDER_SCHEDULER_NAME = os.environ.get("REMINDER_SCHEDULER_NAME", "pt-dev-reminder-scheduler")

lambda_client = boto3.client("lambda")


def _invoke_scheduler(appt_id, patient_phone_e164, patient_name, appt_time_iso):
    payload = {
        "appointment_id": appt_id,
        "patient_phone_e164": patient_phone_e164,
        "patient_name": patient_name,
        "appt_time_iso": appt_time_iso,
    }
    lambda_client.invoke(
        FunctionName=REMINDER_SCHEDULER_NAME,
        InvocationType="Event",
        Payload=json.dumps(payload).encode("utf-8"),
    )


def handler(event, context):
    """
    event example:
    {
      "action": "create|update|cancel",
      "appointment_id": "appt-001",
      "patient_phone_e164": "+5939...",
      "patient_name": "Carlos",
      "start_iso": "2025-08-12T15:00:00",   # hora local, TZ env
      "end_iso":   "2025-08-12T16:00:00",
      "notes": "Evaluación inicial"
    }
    """
    logger.info("appointments_manager event: %s", json.dumps(event))
    action = event["action"]
    appt_id = event["appointment_id"]

    if action == "create":
        start_iso = event["start_iso"]
        end_iso = event["end_iso"]
        if not gcal.is_free(gcal.iso_utc(start_iso), gcal.iso_utc(end_iso)):
            return {"ok": False, "conflict": True}

        created = gcal.create_event(
            summary=f"Pelvis Therapy - {event.get('patient_name','Paciente')}",
            start_iso=start_iso,
            end_iso=end_iso,
            description=event.get("notes", ""),
            attendee_email=None,
        )
        # Notifica propietaria
        send_owner_template(
            paciente=event["patient_phone_e164"],
            fecha_hora=start_iso,
            estado=f"Agendado (eventId={created['id']})",
        )
        # Programa recordatorios
        _invoke_scheduler(
            appt_id,
            event["patient_phone_e164"],
            event.get("patient_name", "Paciente"),
            gcal.iso_utc(start_iso),
        )
        return {"ok": True, "event_id": created["id"]}

    if action == "update":
        event_id = event["event_id"]
        fields = {}
        if "start_iso" in event and "end_iso" in event:
            fields["start"] = {
                "dateTime": event["start_iso"],
                "timeZone": os.environ.get("TZ", "America/Guayaquil"),
            }
            fields["end"] = {
                "dateTime": event["end_iso"],
                "timeZone": os.environ.get("TZ", "America/Guayaquil"),
            }
        if "notes" in event:
            fields["description"] = event["notes"]
        gcal.update_event(event_id, **fields)
        send_owner_template(
            paciente=event.get("patient_phone_e164", ""),
            fecha_hora=event.get("start_iso", ""),
            estado=f"Actualizado (eventId={event_id})",
        )
        # Reprograma recordatorios (mismo appointment_id)
        if "start_iso" in event:
            _invoke_scheduler(
                appt_id,
                event.get("patient_phone_e164", ""),
                event.get("patient_name", "Paciente"),
                gcal.iso_utc(event["start_iso"]),
            )
        return {"ok": True}

    if action == "cancel":
        event_id = event["event_id"]
        gcal.delete_event(event_id)
        send_owner_template(
            paciente=event.get("patient_phone_e164", ""),
            fecha_hora=event.get("start_iso", ""),
            estado=f"Cancelado (eventId={event_id})",
        )
        # Opcional: cancelar schedules (puedes borrar r1/r2/esc por nombre si quieres)
        return {"ok": True}

    return {"ok": False, "error": "unknown_action"}

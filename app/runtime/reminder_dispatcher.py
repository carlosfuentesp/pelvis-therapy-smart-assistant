import json
import logging
import os

import boto3
from tools.whatsapp_owner import send_owner_template, send_patient_reminder

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
TABLE = dynamodb.Table(os.environ["DDB_TABLE"])
scheduler = boto3.client("scheduler")


def handler(event, context):
    logger.info("Reminder event: %s", json.dumps(event))
    appt_id = event["appointment_id"]
    phone = event["patient_phone_e164"]
    pname = event.get("patient_name", "Paciente")
    appt_iso = event["appt_time_iso"]
    action = event.get("action")

    # lee cita
    item = TABLE.get_item(Key={"pk": f"APPT#{appt_id}", "sk": f"APPT#{appt_id}"}).get("Item")
    if not item:
        logger.warning("Appointment not found: %s", appt_id)
        return {"skipped": "not_found"}

    confirmed = bool(item.get("confirmed_at"))

    if action == "first":
        # R1 siempre se envía
        send_patient_reminder(phone, pname, appt_iso, "Responde SI para confirmar")
        return {"sent": "r1"}

    if action == "second":
        # Sólo si aún no confirma
        if confirmed:
            return {"skipped": "already_confirmed"}
        send_patient_reminder(
            phone, pname, appt_iso, "Responde SI para confirmar (2do recordatorio)"
        )
        return {"sent": "r2"}

    if action == "escalation":
        # Si tras R2 sigue sin confirmar → avisa a propietaria
        if confirmed:
            return {"skipped": "already_confirmed"}
        send_owner_template(
            paciente=phone,
            fecha_hora=appt_iso,
            estado="Paciente aún NO confirma tras 2 recordatorios",
        )
        return {"sent": "owner_alert"}

    return {"skipped": "unknown_action"}

import json
import logging

from tools.whatsapp_owner import send_owner_template  # <-- sin app.

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info("Reminder event: %s", json.dumps(event))
    action = (event.get("action") or "unknown").replace("_", " ")
    patient = event.get("patient_phone_e164", "paciente")
    appt_id = event.get("appointment_id", "N/A")
    send_owner_template(
        paciente=patient, fecha_hora=f"cita {appt_id}", estado=f"recordatorio {action}"
    )
    return {"ok": True}

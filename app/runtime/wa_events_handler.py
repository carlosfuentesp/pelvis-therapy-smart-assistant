import json
import logging

from tools.whatsapp_owner import send_owner_template  # <-- antes: from app.tools...

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info("Incoming SNS event: %s", json.dumps(event))
    for record in event.get("Records", []):
        msg = record.get("Sns", {}).get("Message", "{}")
        try:
            payload = json.loads(msg)
        except json.JSONDecodeError:
            payload = {"raw": msg}

        # text = payload.get("text") or payload.get("message") or str(payload)
        from_ = payload.get("from") or "desconocido"

        send_owner_template(paciente=from_, fecha_hora="N/A", estado="mensaje entrante")
    return {"statusCode": 200, "body": "ok"}

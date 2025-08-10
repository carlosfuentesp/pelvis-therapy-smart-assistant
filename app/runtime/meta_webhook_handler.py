import base64
import json
import logging
import os

from tools.whatsapp_owner import send_owner_template, send_text

logger = logging.getLogger()
logger.setLevel(logging.INFO)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "PT_VERIFY_DEV")


def _ok(body="ok"):
    return {"statusCode": 200, "headers": {"Content-Type": "text/plain"}, "body": body}


def _forbidden():
    return {"statusCode": 403, "headers": {"Content-Type": "text/plain"}, "body": "forbidden"}


def handler(event, context):
    http = (event.get("requestContext") or {}).get("http") or {}
    method = http.get("method", "GET")

    # 1) Verificación inicial de Meta (GET /webhook?hub.*=...)
    if method == "GET":
        qs = event.get("queryStringParameters") or {}
        mode = qs.get("hub.mode")
        token = qs.get("hub.verify_token")
        challenge = qs.get("hub.challenge", "")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("Webhook verified OK")
            return _ok(challenge)
        logger.warning("Webhook verify failed: %s", qs)
        return _forbidden()

    # 2) Recepción de mensajes (POST /webhook)
    raw_body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw_body = base64.b64decode(raw_body).decode("utf-8")
    try:
        body = json.loads(raw_body)
    except Exception:
        logger.exception("JSON parse error")
        return _ok("ignored")

    logger.info("Incoming Meta payload: %s", json.dumps(body)[:2000])

    # Estructura: entry[].changes[].value.messages[]
    entries = body.get("entry") or []
    for entry in entries:
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages") or []
            for msg in messages:
                from_id = msg.get("from", "")  # "593..." (devuelve solo dígitos)
                # Normaliza a E.164 (con +)
                to_e164 = "+" + from_id if from_id and not from_id.startswith("+") else from_id
                text = (msg.get("text") or {}).get("body") or ""

                # (MVP) Notifica a la propietaria por plantilla
                send_owner_template(
                    paciente=to_e164 or "desconocido",
                    fecha_hora="N/A",
                    estado=f"mensaje entrante: {text[:80]}",
                )

                # (MVP) Auto-reply breve al usuario (para validar ida/vuelta)
                if to_e164:
                    send_text(
                        to_e164,
                        "¡Hola! Soy el asistente de Pelvis Therapy. "
                        "En breve te ayudo con tus citas o consultas. 🙌",
                    )

    return _ok()

import base64
import datetime as dt
import json
import logging
import os

import boto3
from boto3.dynamodb.conditions import Key
from tools.whatsapp_owner import send_owner_template, send_text

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Env
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "PT_VERIFY_DEV")
DDB_TABLE = os.environ["DDB_TABLE"]

# AWS clients
dynamodb = boto3.resource("dynamodb")
TABLE = dynamodb.Table(DDB_TABLE)
scheduler = boto3.client("scheduler")


def _ok(body="ok", content_type="text/plain"):
    return {"statusCode": 200, "headers": {"Content-Type": content_type}, "body": body}


def _forbidden():
    return {"statusCode": 403, "headers": {"Content-Type": "text/plain"}, "body": "forbidden"}


def _normalize_e164(maybe_num: str) -> str:
    """Meta suele enviar from='5939...' (sin '+'). Normaliza a E.164 con '+'."""
    if not maybe_num:
        return maybe_num
    return maybe_num if maybe_num.startswith("+") else f"+{maybe_num}"


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _mark_confirmed_and_cancel(phone_e164: str):
    """
    Busca la próxima cita futura del paciente por GSI1 (gsi1pk/gsi1sk),
    marca confirmación y cancela schedules r2/esc si existen.
    """
    now_iso = _now_iso()
    try:
        resp = TABLE.query(
            IndexName="gsi1",
            KeyConditionExpression=Key("gsi1pk").eq(f"PATIENT#{phone_e164}")
            & Key("gsi1sk").gt(now_iso),
            Limit=1,
            ScanIndexForward=True,  # más cercana primero
        )
        items = resp.get("Items", [])
    except Exception:
        logger.exception("DDB query failed for patient %s", phone_e164)
        return False, None

    if not items:
        return False, None

    appt = items[0]
    try:
        TABLE.update_item(
            Key={"pk": appt["pk"], "sk": appt["sk"]},
            UpdateExpression="SET confirmed_at=:c, #st=:s",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={":c": now_iso, ":s": "confirmed"},
        )
    except Exception:
        logger.exception("DDB update failed to mark confirmed for %s", appt.get("pk"))
        # seguimos intentando cancelar schedules igualmente

    # Cancela R2/ESC si estaban programados
    for k in ("r2_schedule_name", "esc_schedule_name"):
        name = appt.get(k)
        if name:
            try:
                scheduler.delete_schedule(Name=name)
                logger.info("Deleted schedule %s", name)
            except Exception as e:
                logger.warning("delete_schedule %s failed: %s", name, e)

    return True, appt


def handler(event, context):
    # HTTP API v2 payload
    http = (event.get("requestContext") or {}).get("http") or {}
    method = http.get("method", "GET")

    # ---- 1) Verificación de webhook (GET) ----
    if method == "GET":
        qs = event.get("queryStringParameters") or {}
        mode = qs.get("hub.mode")
        token = qs.get("hub.verify_token")
        challenge = qs.get("hub.challenge", "")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("Webhook verified OK")
            return _ok(challenge)
        logger.warning("Webhook verify failed. mode=%s token_ok=%s", mode, token == VERIFY_TOKEN)
        return _forbidden()

    # ---- 2) Recepción de mensajes (POST) ----
    raw_body = event.get("body") or "{}"
    if event.get("isBase64Encoded") is True or event.get("isBase64Encoded") == "true":
        raw_body = base64.b64decode(raw_body).decode("utf-8")

    try:
        body = json.loads(raw_body)
    except Exception:
        logger.exception("JSON parse error")
        return _ok("ignored")

    logger.info("Incoming Meta payload: %s", json.dumps(body)[:2000])

    entries = body.get("entry") or []
    for entry in entries:
        changes = entry.get("changes") or []
        for change in changes:
            value = change.get("value", {})
            # Log de estados (opcional)
            statuses = value.get("statuses") or []
            if statuses:
                logger.info("Statuses: %s", json.dumps(statuses)[:1000])

            messages = value.get("messages") or []
            for msg in messages:
                # Solo texto para MVP
                msg_type = msg.get("type")
                if msg_type != "text":
                    continue

                from_id = msg.get("from", "")  # "5939..." sin '+'
                user_e164 = _normalize_e164(from_id)  # "+5939..."
                text = (msg.get("text") or {}).get("body") or ""
                normalized = text.strip().lower()

                # 2.1 Notifica a propietaria (siempre que llega un entrante)
                try:
                    send_owner_template(
                        paciente=user_e164 or "desconocido",
                        fecha_hora="N/A",
                        estado=f"mensaje entrante: {text[:80]}",
                    )
                except Exception:
                    logger.exception("Owner notification failed")

                # 2.2 Confirmación por palabras clave
                if normalized in {"si", "sí", "si.", "sí.", "ok", "listo", "confirmo", "confirmar"}:
                    ok, appt = _mark_confirmed_and_cancel(user_e164)
                    if ok:
                        try:
                            send_text(user_e164, "¡Gracias! Tu cita ha sido confirmada ✅")
                            # Aviso opcional a propietaria
                            send_owner_template(
                                paciente=user_e164,
                                fecha_hora=appt.get("appt_time_iso", "N/A"),
                                estado="Paciente confirmó",
                            )
                        except Exception:
                            logger.exception("Post-confirmation messages failed")
                    else:
                        send_text(
                            user_e164,
                            "Gracias. No encontré una cita pendiente. Si deseas agendar, cuéntame tu disponibilidad.",
                        )
                else:
                    # 2.3 Auto-respuesta básica (MVP)
                    try:
                        send_text(
                            user_e164,
                            "¡Hola! Soy el asistente de Pelvis Therapy. "
                            "Puedo ayudarte a agendar/confirmar tu cita. Escribe 'SI' para confirmar.",
                        )
                    except Exception:
                        logger.exception("Auto-reply failed")

    return _ok()

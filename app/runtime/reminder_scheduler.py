import datetime as dt
import json
import logging
import os

import boto3
import botocore.exceptions as bex

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ===== Entorno =====
DDB_TABLE = os.environ["DDB_TABLE"]
SCHEDULER_ROLE_ARN = os.environ["SCHEDULER_ROLE_ARN"]
REMINDER_DISPATCHER_ARN = os.environ["REMINDER_DISPATCHER_ARN"]
STAGE = os.environ.get("STAGE", "dev")
FAST_MODE = os.environ.get("FAST_MODE", "0") == "1"

# ===== AWS clients =====
dynamodb = boto3.resource("dynamodb")
TABLE = dynamodb.Table(DDB_TABLE)
scheduler = boto3.client("scheduler")


def _fmt_noz(d: dt.datetime) -> str:
    """EventBridge Scheduler espera at(YYYY-MM-DDThh:mm:ss) sin 'Z'."""
    return d.strftime("%Y-%m-%dT%H:%M:%S")


def _isoz(d: dt.datetime) -> str:
    """ISO con sufijo Z (para devolver en la respuesta/logs)."""
    return d.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_future(d: dt.datetime, seconds_ahead: int = 60) -> dt.datetime:
    """
    Si la hora quedó en el pasado (o muy cerca), muévela un poco al futuro
    para evitar ValidationException.
    """
    now = dt.datetime.now(dt.timezone.utc)
    if d <= now:
        return now + dt.timedelta(seconds=seconds_ahead)
    return d


def _upsert_schedule(name: str, when_utc: dt.datetime, action: str, payload: dict):
    """
    Crea/actualiza un schedule 'at(...)' en UTC que invoca REMINDER_DISPATCHER_ARN.
    """
    when_utc = _ensure_future(when_utc)
    when_str = _fmt_noz(when_utc)

    target = {
        "Arn": REMINDER_DISPATCHER_ARN,
        "RoleArn": SCHEDULER_ROLE_ARN,
        "Input": json.dumps(payload),
    }

    try:
        scheduler.create_schedule(
            Name=name,
            FlexibleTimeWindow={"Mode": "OFF"},
            ScheduleExpression=f"at({when_str})",  # sin 'Z'
            ScheduleExpressionTimezone="UTC",  # explícito
            Target=target,
        )
        logger.info("Created schedule %s at %s UTC (%s)", name, when_str, action)
    except bex.ClientError as e:
        # Si ya existe, lo actualizamos
        if e.response.get("Error", {}).get("Code") in {
            "ConflictException",
            "ResourceAlreadyExistsException",
        } or "already exists" in str(e):
            scheduler.update_schedule(
                Name=name,
                FlexibleTimeWindow={"Mode": "OFF"},
                ScheduleExpression=f"at({when_str})",
                ScheduleExpressionTimezone="UTC",
                Target=target,
            )
            logger.info("Updated schedule %s at %s UTC (%s)", name, when_str, action)
        else:
            logger.error("create_schedule failed for %s: %s", name, e)
            raise


def handler(event, context):
    """
    event = {
      "appointment_id": "appt-123",
      "patient_phone_e164": "+5939...",
      "patient_name": "Carlos",
      "appt_time_iso": "2025-08-11T15:00:00Z"   # siempre en UTC con 'Z'
    }
    """
    logger.info("Schedule request: %s", json.dumps(event))

    appt_id = event["appointment_id"]
    phone = event["patient_phone_e164"]
    pname = event.get("patient_name", "Paciente")
    appt_iso = event["appt_time_iso"]

    # Parseo ISO → UTC
    try:
        appt_dt = dt.datetime.fromisoformat(appt_iso.replace("Z", "+00:00")).astimezone(
            dt.timezone.utc
        )
    except ValueError as e:
        logger.exception("Invalid appt_time_iso %s: %s", appt_iso, e)
        raise

    # Tiempos (modo normal vs. modo rápido de pruebas)
    if FAST_MODE:
        now = dt.datetime.now(dt.timezone.utc)
        r1_dt = now + dt.timedelta(minutes=1)
        r2_dt = now + dt.timedelta(minutes=5)
        esc_dt = now + dt.timedelta(minutes=9)
    else:
        r1_dt = appt_dt - dt.timedelta(hours=24)  # primer recordatorio
        r2_dt = appt_dt - dt.timedelta(hours=20)  # segundo recordatorio (+4h)
        esc_dt = appt_dt - dt.timedelta(hours=19)  # escalación (1h luego del 2do)

    base = f"pt-{STAGE}-{appt_id}"
    r1_name, r2_name, esc_name = f"{base}-r1", f"{base}-r2", f"{base}-esc"

    # Payload común que recibirá el dispatcher
    base_payload = {
        "appointment_id": appt_id,
        "patient_phone_e164": phone,
        "patient_name": pname,
        "appt_time_iso": appt_iso,
    }

    # Upsert de los 3 schedules
    _upsert_schedule(r1_name, r1_dt, "first", {**base_payload, "action": "first"})
    _upsert_schedule(r2_name, r2_dt, "second", {**base_payload, "action": "second"})
    _upsert_schedule(esc_name, esc_dt, "escalation", {**base_payload, "action": "escalation"})

    # Persistimos/actualizamos la cita en DDB
    TABLE.update_item(
        Key={"pk": f"APPT#{appt_id}", "sk": f"APPT#{appt_id}"},
        UpdateExpression=(
            "SET patient_phone_e164=:p, appt_time_iso=:t, #st=:s, "
            "gsi1pk=:g1, gsi1sk=:g2, "
            "r1_schedule_name=:r1, r2_schedule_name=:r2, esc_schedule_name=:esc"
        ),
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={
            ":p": phone,
            ":t": _isoz(appt_dt),
            ":s": "scheduled",
            ":g1": f"PATIENT#{phone}",
            ":g2": _isoz(appt_dt),
            ":r1": r1_name,
            ":r2": r2_name,
            ":esc": esc_name,
        },
    )

    return {
        "ok": True,
        "r1": _isoz(r1_dt),
        "r2": _isoz(r2_dt),
        "esc": _isoz(esc_dt),
        "fast_mode": FAST_MODE,
    }

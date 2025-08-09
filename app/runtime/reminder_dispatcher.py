import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SNS_OWNER_TOPIC_ARN = os.environ.get("OWNER_TOPIC", "")

sns = boto3.client("sns")


def handler(event, context):
    """
    Espera payload con:
    {
      "appointment_id": "...",
      "patient_phone_e164": "+5939...",
      "action": "first_reminder" | "second_reminder" | "owner_escalation"
    }
    """
    logger.info("Reminder event: %s", json.dumps(event))
    if SNS_OWNER_TOPIC_ARN:
        sns.publish(
            TopicArn=SNS_OWNER_TOPIC_ARN,
            Message=f"[Pelvis Therapy] Scheduler ejecutó acción: {json.dumps(event)}",
        )
    return {"ok": True}

import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SNS_OWNER_TOPIC_ARN = os.environ.get("OWNER_TOPIC", "")

sns = boto3.client("sns")


def handler(event, context):
    # Evento desde SNS (Message & event publishing de WhatsApp)
    # Para probar: aws sns publish --topic-arn <...> --message '{"from":"+5939...","text":"Hola"}'
    logger.info("Incoming SNS event: %s", json.dumps(event))

    for record in event.get("Records", []):
        msg = record.get("Sns", {}).get("Message", "{}")
        try:
            payload = json.loads(msg)
        except json.JSONDecodeError:
            payload = {"raw": msg}

        # MVP: solo notifica a la propietaria por SMS que llegó un mensaje nuevo.
        text = payload.get("text") or payload.get("message") or str(payload)
        from_ = payload.get("from") or "desconocido"

        body = f"[Pelvis Therapy] Nuevo mensaje WA de {from_}: {text[:200]}"
        if SNS_OWNER_TOPIC_ARN:
            sns.publish(TopicArn=SNS_OWNER_TOPIC_ARN, Message=body)

    return {"statusCode": 200, "body": "ok"}

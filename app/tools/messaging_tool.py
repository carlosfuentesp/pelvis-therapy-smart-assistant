"""Send WhatsApp or SMS messages using AWS clients."""
import boto3
from strands import tool


@tool
def send_whatsapp(to_e164: str, mensaje: str) -> dict:
    """Send a WhatsApp message using the AWS social-messaging client."""
    client = boto3.client("social-messaging")
    return client.send_whatsapp_message(
        DestinationPhoneNumber=to_e164,
        MessageBody=mensaje,
    )


@tool
def send_sms(to_e164: str, mensaje: str) -> dict:
    """Send an SMS using Amazon SNS."""
    client = boto3.client("sns")
    resp = client.publish(PhoneNumber=to_e164, Message=mensaje)
    return {"MessageId": resp.get("MessageId")}

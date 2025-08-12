"""Notify the clinic owner via SMS using SNS."""
import os
import boto3
from strands import tool

OWNER_PHONE = os.environ.get("OWNER_PHONE", "")


@tool
def notify_owner(mensaje: str, telefono: str = OWNER_PHONE) -> dict:
    """Send an SMS message to the owner."""
    client = boto3.client("sns")
    return client.publish(PhoneNumber=telefono, Message=mensaje)

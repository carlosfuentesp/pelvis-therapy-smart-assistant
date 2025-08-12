from types import SimpleNamespace

from app.tools import messaging_tool


def test_send_whatsapp(monkeypatch):
    calls = {}

    class Client:
        def send_whatsapp_message(self, **kwargs):
            calls.update(kwargs)
            return {"MessageId": "1"}

    monkeypatch.setattr(
        messaging_tool, "boto3", SimpleNamespace(client=lambda name: Client())
    )
    messaging_tool.send_whatsapp("+593", "hola")
    assert calls["DestinationPhoneNumber"] == "+593"
    assert calls["MessageBody"] == "hola"


def test_send_sms(monkeypatch):
    calls = {}

    class SNSClient:
        def publish(self, **kwargs):
            calls.update(kwargs)
            return {"MessageId": "abc"}

    monkeypatch.setattr(
        messaging_tool, "boto3", SimpleNamespace(client=lambda name: SNSClient())
    )
    resp = messaging_tool.send_sms("+593", "hi")
    assert calls["PhoneNumber"] == "+593"
    assert resp["MessageId"] == "abc"

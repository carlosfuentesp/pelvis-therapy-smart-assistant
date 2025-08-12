from types import SimpleNamespace

from app.tools import notify_owner_tool


def test_notify_owner(monkeypatch):
    calls = {}

    class SNSClient:
        def publish(self, **kwargs):
            calls.update(kwargs)
            return {"MessageId": "1"}

    monkeypatch.setattr(
        notify_owner_tool, "boto3", SimpleNamespace(client=lambda name: SNSClient())
    )
    notify_owner_tool.notify_owner("hola", "+593")
    assert calls["PhoneNumber"] == "+593"
    assert calls["Message"] == "hola"

from types import SimpleNamespace

from app.tools import scheduler_tool


def test_schedule_reminders(monkeypatch):
    calls = []

    class Client:
        def create_schedule(self, **kwargs):
            calls.append(kwargs)
            return {"Name": kwargs["Name"]}

    monkeypatch.setattr(
        scheduler_tool, "boto3", SimpleNamespace(client=lambda name: Client())
    )
    scheduler_tool.schedule_reminders("ev1", "2024-01-02T10:00:00")
    assert len(calls) == 2
    names = {c["Name"] for c in calls}
    assert "ev1-24h" in names and "ev1-4h" in names

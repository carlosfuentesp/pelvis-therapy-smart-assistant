from app.agents.appointments_agent import agent as ag


def test_crear_cita_orquesta(monkeypatch):
    calls = {}

    monkeypatch.setattr(
        ag.google_calendar_tool, "crear_evento", lambda *a, **k: {"id": "evt"}
    )

    def save_state(*a, **k):
        calls["state"] = (a, k)

    def sched(*a, **k):
        calls["sched"] = (a, k)

    def wa(*a, **k):
        calls["wa"] = (a, k)

    def owner(*a, **k):
        calls["owner"] = (a, k)

    monkeypatch.setattr(ag.state_store, "save_state", save_state)
    monkeypatch.setattr(ag.scheduler_tool, "schedule_reminders", sched)
    monkeypatch.setattr(ag.messaging_tool, "send_whatsapp", wa)
    monkeypatch.setattr(ag.notify_owner_tool, "notify_owner", owner)

    eid = ag.crear_cita("Ana", "+593", "2024-01-02T10:00:00", "2024-01-02T11:00:00")
    assert eid == "evt"
    assert set(calls.keys()) == {"state", "sched", "wa", "owner"}

from app.tools import google_calendar_tool as gtool


def test_crear_evento_invoca_cliente(monkeypatch):
    llamado = {}

    def fake_create(summary, start, end, desc, attendee):
        llamado["args"] = (summary, start, end, desc, attendee)
        return {"id": "1"}

    monkeypatch.setattr(gtool.gcal_client, "create_event", fake_create)
    res = gtool.crear_evento("s", "a", "b", "d", "e")
    assert res["id"] == "1"
    assert llamado["args"] == ("s", "a", "b", "d", "e")


def test_actualizar_evento(monkeypatch):
    llamado = {}

    def fake_update(eid, **fields):
        llamado["eid"] = eid
        llamado["fields"] = fields
        return {"id": eid}

    monkeypatch.setattr(gtool.gcal_client, "update_event", fake_update)
    res = gtool.actualizar_evento("abc", foo=1)
    assert res["id"] == "abc"
    assert llamado == {"eid": "abc", "fields": {"foo": 1}}


def test_eliminar_evento(monkeypatch):
    llamado = {}

    def fake_delete(eid):
        llamado["eid"] = eid

    monkeypatch.setattr(gtool.gcal_client, "delete_event", fake_delete)
    eid = gtool.eliminar_evento("xyz")
    assert llamado["eid"] == "xyz"
    assert eid == "xyz"

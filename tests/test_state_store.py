from app.tools import state_store


def test_state_store_crud(monkeypatch):
    class Table:
        def __init__(self):
            self.items = {}

        def put_item(self, Item):
            self.items[Item["id"]] = Item

        def get_item(self, Key):
            return {"Item": self.items.get(Key["id"])}

        def delete_item(self, Key):
            self.items.pop(Key["id"], None)

    tbl = Table()
    monkeypatch.setattr(state_store, "_table", lambda: tbl)

    state_store.save_state("1", {"foo": "bar"})
    assert tbl.items["1"]["foo"] == "bar"
    item = state_store.get_state("1")
    assert item == {"id": "1", "foo": "bar"}
    state_store.delete_state("1")
    assert "1" not in tbl.items

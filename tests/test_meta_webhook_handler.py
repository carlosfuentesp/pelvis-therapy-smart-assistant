import os
import sys
from pathlib import Path

from botocore.exceptions import ClientError

# Ensure environment variable needed by module is set before import
os.environ.setdefault("DDB_TABLE", "dummy")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# Ensure project and app roots on path for imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "app"))

from app.runtime import meta_webhook_handler as mwh  # noqa: E402


def _client_error(op_name: str) -> ClientError:
    return ClientError({"Error": {"Code": "Boom", "Message": "boom"}}, op_name)


def test_mark_confirmed_query_failure(monkeypatch, caplog):
    def fake_query(**kwargs):
        raise _client_error("Query")

    monkeypatch.setattr(mwh.TABLE, "query", fake_query)

    with caplog.at_level("ERROR"):
        ok, appt = mwh._mark_confirmed_and_cancel("+5939")

    assert (ok, appt) == (False, None)
    assert "Boom" in caplog.text


def test_mark_confirmed_update_failure(monkeypatch, caplog):
    def fake_query(**kwargs):
        return {
            "Items": [
                {
                    "pk": "PK",
                    "sk": "SK",
                    "r2_schedule_name": "R2",
                    "esc_schedule_name": "ESC",
                }
            ]
        }

    def fake_update_item(**kwargs):
        raise _client_error("UpdateItem")

    deleted = []

    def fake_delete_schedule(Name):
        deleted.append(Name)

    monkeypatch.setattr(mwh.TABLE, "query", fake_query)
    monkeypatch.setattr(mwh.TABLE, "update_item", fake_update_item)
    monkeypatch.setattr(mwh.scheduler, "delete_schedule", fake_delete_schedule)

    with caplog.at_level("ERROR"):
        ok, appt = mwh._mark_confirmed_and_cancel("+5939")

    assert ok is True
    assert appt["pk"] == "PK"
    assert set(deleted) == {"R2", "ESC"}
    assert "Boom" in caplog.text

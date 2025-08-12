"""Simple DynamoDB based state storage."""
import os
import boto3
from strands import tool

TABLE_NAME = os.environ.get("STATE_TABLE", "appointments_state")
_table_cache = None


def _table():
    global _table_cache
    if _table_cache is None:
        _table_cache = boto3.resource("dynamodb").Table(TABLE_NAME)
    return _table_cache


@tool
def save_state(clave: str, datos: dict) -> None:
    """Persist conversation state in DynamoDB."""
    item = {"id": clave}
    item.update(datos)
    _table().put_item(Item=item)


@tool
def get_state(clave: str) -> dict | None:
    """Retrieve conversation state."""
    resp = _table().get_item(Key={"id": clave})
    return resp.get("Item")


@tool
def delete_state(clave: str) -> None:
    """Delete conversation state."""
    _table().delete_item(Key={"id": clave})

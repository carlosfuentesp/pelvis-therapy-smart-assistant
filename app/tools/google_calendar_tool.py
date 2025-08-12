"""Wrappers around Google Calendar client functions exposed as tools."""
from strands import tool
from . import gcal_client


@tool
def crear_evento(
    resumen: str,
    inicio_iso: str,
    fin_iso: str,
    descripcion: str,
    correo_asistente: str | None = None,
) -> dict:
    """Create an event in Google Calendar."""
    return gcal_client.create_event(
        resumen, inicio_iso, fin_iso, descripcion, correo_asistente
    )


@tool
def actualizar_evento(evento_id: str, **fields) -> dict:
    """Update an existing Google Calendar event."""
    return gcal_client.update_event(evento_id, **fields)


@tool
def eliminar_evento(evento_id: str) -> str:
    """Delete an event from Google Calendar."""
    gcal_client.delete_event(evento_id)
    return evento_id

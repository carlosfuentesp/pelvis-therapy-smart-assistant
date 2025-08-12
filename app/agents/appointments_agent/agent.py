"""Agent that orchestrates calendar, messaging and state tools for appointments."""
from strands import Agent, tool

from ...tools import (
    google_calendar_tool,
    messaging_tool,
    notify_owner_tool,
    scheduler_tool,
    state_store,
)


@tool
def crear_cita(
    paciente: str,
    telefono: str,
    inicio_iso: str,
    fin_iso: str,
    descripcion: str = "",
) -> str:
    """Create a new appointment and schedule reminders."""
    event = google_calendar_tool.crear_evento(
        paciente, inicio_iso, fin_iso, descripcion
    )
    state_store.save_state(
        event["id"],
        {"paciente": paciente, "telefono": telefono, "inicio": inicio_iso, "fin": fin_iso},
    )
    scheduler_tool.schedule_reminders(event["id"], inicio_iso)
    messaging_tool.send_whatsapp(
        telefono, f"Tu cita ha sido programada para {inicio_iso}."
    )
    notify_owner_tool.notify_owner(
        f"Nueva cita de {paciente} el {inicio_iso}"
    )
    return event["id"]


@tool
def actualizar_cita(evento_id: str, inicio_iso: str, fin_iso: str) -> str:
    """Update an existing appointment."""
    google_calendar_tool.actualizar_evento(
        evento_id, start={"dateTime": inicio_iso}, end={"dateTime": fin_iso}
    )
    state_store.save_state(evento_id, {"inicio": inicio_iso, "fin": fin_iso})
    scheduler_tool.schedule_reminders(evento_id, inicio_iso)
    return evento_id


@tool
def cancelar_cita(evento_id: str, telefono: str) -> str:
    """Cancel an appointment."""
    google_calendar_tool.eliminar_evento(evento_id)
    state_store.delete_state(evento_id)
    messaging_tool.send_whatsapp(telefono, "Tu cita ha sido cancelada.")
    notify_owner_tool.notify_owner(f"Cita cancelada {evento_id}")
    return evento_id


appointments_agent = Agent(
    system_prompt=(
        "Eres el asistente de Pelvis Therapy para gestionar citas. "
        "Usa las herramientas disponibles para crear, actualizar o cancelar citas."),
    tools=[crear_cita, actualizar_cita, cancelar_cita],
)

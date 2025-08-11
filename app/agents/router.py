import re
from .info_agent import info_agent

INTENT_RE = {
    "citas": re.compile(r"\b(cita|agendar|reservar|reprogram|cancelar)\b", re.I),
}


def route_intent(text: str) -> str:
    if INTENT_RE["citas"].search(text or ""):
        return "citas"
    return "info"


def handle_message(text: str) -> str:
    intent = route_intent(text)
    if intent == "info":
        res = info_agent(text)
        return str(res.message).strip()
    # placeholder para el siguiente paso (citas)
    return (
        "Puedo ayudarte a *agendar/actualizar/cancelar* tu cita. "
        "Dime, por ejemplo: 'Agendar el miércoles a las 10am'."
    )

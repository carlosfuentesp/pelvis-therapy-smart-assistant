# placeholder: clasificación de intención (info vs appointments)
def route_intent(user_text: str) -> str:
    return (
        "info"
        if "precio" in user_text.lower() or "servicio" in user_text.lower()
        else "appointments"
    )

import os
import yaml
import logging
from pathlib import Path
from strands import Agent, tool

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DATA = Path(os.getenv("PT_CONTENT_PATH", "content/pelvis/services.yml"))


@tool
def buscar_servicio(pregunta: str) -> str:
    """
    Devuelve texto breve con el/los servicios relevantes y datos de contacto.
    """
    data = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    svc = data.get("servicios", [])
    hits = []
    q = pregunta.lower()
    for s in svc:
        if any(k in q for k in (s["nombre"].lower().split())) or any(
            w in s["descripcion"].lower() for w in q.split()
        ):
            hits.append(f"- {s['nombre']} ({s['duracion']}): {s['descripcion']}")
    if not hits:
        # fallback: muestra catálogo
        hits = [f"- {s['nombre']} ({s['duracion']}): {s['descripcion']}" for s in svc[:3]]
    footer = f"\n\nDirección: {data['contacto']['direccion']}\nWhatsApp: {data['contacto']['whatsapp']}\nHorario: {data['contacto']['horario']}"
    return "Servicios recomendados:\n" + "\n".join(hits) + footer


info_agent = Agent(
    system_prompt=(
        "Eres el asistente de Pelvis Therapy. Responde claro y corto. "
        "Si preguntan por servicios, usa la herramienta buscar_servicio. "
        "No inventes precios."
    ),
    tools=[buscar_servicio],
)

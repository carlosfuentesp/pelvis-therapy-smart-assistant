import json
import logging
import os
import urllib.error
import urllib.request

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SECRETS_NAME = os.environ.get("META_WA_SECRET_NAME", "pelvis/wa/meta-owner")
OWNER_WA_E164 = os.environ.get("OWNER_WA_E164", "")
TEMPLATE_NAME = os.environ.get("OWNER_WA_TEMPLATE", "owner_alert_v2")
LANG_CODE = os.environ.get("OWNER_WA_LANG", "es_EC")

_secrets_cache = None


def _get_meta_creds():
    global _secrets_cache
    if _secrets_cache:
        return _secrets_cache
    sm = boto3.client("secretsmanager")
    resp = sm.get_secret_value(SecretId=SECRETS_NAME)
    data = json.loads(resp["SecretString"])
    _secrets_cache = {
        "access_token": data["access_token"],
        "phone_number_id": data["phone_number_id"],
    }
    return _secrets_cache


def send_owner_template(paciente: str, fecha_hora: str, estado: str) -> dict:
    if not OWNER_WA_E164:
        logger.warning("OWNER_WA_E164 vacío; no se envía WhatsApp.")
        return {"skipped": True, "reason": "no_owner_number"}

    creds = _get_meta_creds()
    url = f"https://graph.facebook.com/v20.0/{creds['phone_number_id']}/messages"
    headers = {
        "Authorization": f"Bearer {creds['access_token']}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": OWNER_WA_E164,
        "type": "template",
        "template": {
            "name": TEMPLATE_NAME,
            "language": {"code": LANG_CODE},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": paciente},
                        {"type": "text", "text": fecha_hora},
                        {"type": "text", "text": estado},
                    ],
                }
            ],
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            resp_txt = r.read().decode("utf-8")
            logger.info("WA owner OK: %s", resp_txt)
            try:
                return {"ok": True, "resp": json.loads(resp_txt)}
            except Exception:
                return {"ok": True, "resp_text": resp_txt}
    except urllib.error.HTTPError as e:
        err_txt = e.read().decode("utf-8") if e.fp else str(e)
        logger.error("Error WA owner %s: %s", e.code, err_txt)
        return {"ok": False, "status": e.code, "error": err_txt}
    except Exception as e:
        logger.exception("Error WA owner: %s", e)
        return {"ok": False, "error": str(e)}

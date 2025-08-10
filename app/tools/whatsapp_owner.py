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


def _post_messages(payload: dict) -> dict:
    creds = _get_meta_creds()
    url = f"https://graph.facebook.com/v20.0/{creds['phone_number_id']}/messages"
    headers = {
        "Authorization": f"Bearer {creds['access_token']}",
        "Content-Type": "application/json",
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            txt = r.read().decode("utf-8")
            logger.info("WA resp: %s", txt)
            try:
                return {"ok": True, "resp": json.loads(txt)}
            except Exception:
                return {"ok": True, "resp_text": txt}
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8") if e.fp else str(e)
        logger.error("WA error %s: %s", e.code, err)
        return {"ok": False, "status": e.code, "error": err}
    except Exception as e:
        logger.exception("WA error: %s", e)
        return {"ok": False, "error": str(e)}


def send_owner_template(paciente: str, fecha_hora: str, estado: str) -> dict:
    payload = {
        "messaging_product": "whatsapp",
        "to": OWNER_WA_E164[1:] if OWNER_WA_E164.startswith("+") else OWNER_WA_E164,
        "type": "template",
        "template": {
            "name": TEMPLATE_NAME,  # "owner_alert"
            "language": {"code": LANG_CODE},  # "es_EC"
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": paciente, "parameter_name": "paciente"},
                        {"type": "text", "text": fecha_hora, "parameter_name": "fecha_hora"},
                        {"type": "text", "text": estado, "parameter_name": "estado"},
                    ],
                }
            ],
        },
    }
    return _post_messages(payload)


def send_text(to_e164: str, text: str) -> dict:
    # Cloud API acepta número internacional (normalmente sin '+', pero con '+' también funciona).
    to = to_e164[1:] if to_e164.startswith("+") else to_e164
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text[:4000]},
    }
    return _post_messages(payload)

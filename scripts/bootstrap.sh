#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(pwd)"

mkdir -p app/{config/policies,agents/{info_agent,appointments_agent},tools,runtime,data} \
         infra/terraform/{envs/dev,modules/{lambda_function,api_http,dynamodb_table,eventbridge_scheduler,sns_sms,secrets_manager,s3_bucket,ecr_repo}} \
         scripts ops

# Archivos base
cat > .gitignore <<'EOF'
.venv/
__pycache__/
.pytype/
.mypy_cache/
.pytest_cache/
*.pyc
.env
.DS_Store
EOF

cat > README.md <<'EOF'
# Pelvis Therapy WhatsApp Assistant (MVP)
MVP multiagente (Strands + Amazon Bedrock AgentCore) para:
- FAQ/servicios
- Gestión de citas (Google Calendar)
- Recordatorios por WhatsApp + escalamiento SMS
EOF

cat > requirements.txt <<'EOF'
strands-agents
bedrock-agentcore
boto3
google-api-python-client
google-auth
google-auth-httplib2
pydantic-settings
tenacity
python-dateutil
orjson
EOF

cat > requirements-dev.txt <<'EOF'
pytest
pytest-cov
ruff
black
mypy
pre-commit
types-requests
EOF

cat > pyproject.toml <<'EOF'
[tool.black]
line-length = 100
target-version = ["py310"]

[tool.ruff]
line-length = 100
select = ["E","F","I","B","W","UP"]
ignore = []

[tool.pytest.ini_options]
addopts = "-q"
EOF

cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks: [{ id: black }]
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.8
    hooks: [{ id: ruff, args: ["--fix"] }]
EOF

cat > app/config/settings.py <<'EOF'
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    env: str = "dev"
    s3_faq_bucket: str = "pelvis-therapy-faq-dev"
    dynamodb_table: str = "pelvis-therapy-state-dev"
    owner_phone_e164: str = ""  # +593...
    google_sa_secret_name: str = "pelvis/google/service-account"  # Secrets Manager
    class Config:
        env_file = ".env"

settings = Settings()
EOF

cat > app/agents/router.py <<'EOF'
# placeholder: clasificación de intención (info vs appointments)
def route_intent(user_text: str) -> str:
    return "info" if "precio" in user_text.lower() or "servicio" in user_text.lower() else "appointments"
EOF

cat > app/agents/info_agent/agent.py <<'EOF'
# placeholder: carga YAML desde S3 y responde FAQs
EOF

cat > app/agents/appointments_agent/agent.py <<'EOF'
# placeholder: orquesta herramientas de Calendar
EOF

cat > app/tools/google_calendar_tool.py <<'EOF'
# placeholder: create/update/delete events con google-api-python-client
EOF

cat > app/tools/messaging_tool.py <<'EOF'
# placeholder: envío WhatsApp via AWS End User Messaging Social (boto3 client social-messaging)
EOF

cat > app/tools/notify_owner_tool.py <<'EOF'
# placeholder: SMS via SNS
EOF

cat > app/tools/scheduler_tool.py <<'EOF'
# placeholder: crea schedules one-time en EventBridge Scheduler (24h y +4h)
EOF

cat > app/tools/state_store.py <<'EOF'
# placeholder: CRUD en DynamoDB para estado conversación y confirmaciones
EOF

cat > app/runtime/handler_lambda.py <<'EOF'
# placeholder: handler Lambda - enruta a agentes
def handler(event, context):
    return {"statusCode": 200, "body": "ok"}
EOF

cat > app/data/faq_portafolio.yaml <<'EOF'
# placeholder: catálogo de servicios, indicaciones y precios de referencia
EOF

cat > infra/terraform/envs/dev/providers.tf <<'EOF'
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.60" }
  }
}

provider "aws" {
  region = var.region
}
EOF

cat > infra/terraform/envs/dev/backend.tf <<'EOF'
# Ajusta nombres de bucket y tabla de lock
terraform {
  backend "s3" {
    bucket         = "pelvis-therapy-tfstate-dev"
    key            = "infra/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "pelvis-therapy-tf-locks"
    encrypt        = true
  }
}
EOF

cat > infra/terraform/envs/dev/variables.tf <<'EOF'
variable "region" { type = string  default = "us-east-1" }
EOF

cat > infra/terraform/envs/dev/main.tf <<'EOF'
# Aquí invocarás módulos: lambda_function, api_http, dynamodb_table, eventbridge_scheduler, sns_sms, secrets_manager, s3_bucket, ecr_repo (opcional).
EOF

cat > ops/alarms.md <<'EOF'
# Alarmas (MVP)
- Lambda errors > 0 (5 min)
- DLQ > 0 (si se usa)
- Costo diario > umbral
EOF

cat > ops/runbooks.md <<'EOF'
# Runbooks (MVP)
- Mensaje no entregado por WhatsApp -> revisar Social Messaging + SNS
- Fallo Calendar -> revisar credenciales y permisos DWD
EOF

# Setup de entorno: uv si está disponible; si no, venv estándar
if command -v uv >/dev/null 2>&1; then
  uv python install 3.10 || true
  uv venv --python 3.10
  source .venv/bin/activate
  uv pip install -r requirements.txt
  uv pip install -r requirements-dev.txt
else
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt -r requirements-dev.txt
fi

pre-commit install || true

echo "Scaffold listo."
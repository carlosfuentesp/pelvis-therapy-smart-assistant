#!/usr/bin/env bash
# Bootstrap del scaffold para el MVP de Pelvis Therapy
# Uso:
#   bash scripts/bootstrap_scaffold.sh            # en el root del repo actual (recomendado)
#   bash scripts/bootstrap_scaffold.sh /ruta/proyecto  # opcional: crea/usa esa carpeta
# Variables opcionales:
#   AUTO_COMMIT=true|false   # por defecto true; hace el primer commit automáticamente

set -euo pipefail

PROJECT_DIR="${1:-.}"

say() { printf "\033[1;32m%s\033[0m\n" "$*"; }
warn() { printf "\033[1;33m%s\033[0m\n" "$*"; }

# 1) Crear/entrar al directorio del proyecto
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

say ">> Inicializando scaffold en: $(pwd)"

# 2) Estructura de carpetas base
say ">> Creando estructura de carpetas"
mkdir -p src/{api,agents,tools,orchestration,core,storage}
mkdir -p infra/terraform/envs/{dev,prod}
mkdir -p infra/terraform/modules/{api_gateway,lambda,dynamodb,eventbridge,step_functions,secrets_manager,bedrock_agentcore,iam}
mkdir -p tests docs scripts

# 3) Entorno virtual de Python
if [ ! -d .venv ]; then
  if ! command -v python3 >/dev/null 2>&1; then
    echo "Python3 no está instalado o no está en PATH" >&2
    exit 1
  fi
  say ">> Creando entorno virtual .venv"
  python3 -m venv .venv
else
  warn ":: .venv ya existe; se omite creación"
fi

# 4) Archivos base (solo si no existen)
create_file() {
  local path="$1"; shift
  if [ -e "$path" ]; then
    warn ":: ${path} ya existe; no se sobrescribe"
  else
    mkdir -p "$(dirname "$path")"
    cat >"$path" <<'EOF'
EOF
    # Rellenar contenido con el siguiente here-doc
  fi
}

# .gitignore
if [ ! -f .gitignore ]; then
  cat > .gitignore <<'EOF'
# Python
.venv/
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.so
.mypy_cache/
.pytest_cache/

# Mac / OS
.DS_Store

# Editor/Tools
.idea/
.vscode/
.env

# Terraform
*.tfstate
*.tfstate.*
.terraform/
.crash.log

# Node (si en el futuro se usa para CI/CD o tooling)
node_modules/
EOF
fi

# .env.example (sin secretos reales)
if [ ! -f .env.example ]; then
  cat > .env.example <<'EOF'
# WhatsApp Cloud API
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_BUSINESS_ID=
WHATSAPP_TOKEN=

# Google Calendar OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
GOOGLE_CALENDAR_ID=

# App config
APP_ENV=dev
REGION=us-east-1
EOF
fi

# README.md inicial
if [ ! -f README.md ]; then
  cat > README.md <<'EOF'
# Pelvis Therapy WhatsApp Assistant (MVP)

MVP de asistente multiagente para WhatsApp (información del centro y gestión de citas) usando **AWS Bedrock AgentCore + Strands Agents SDK**, con integración a **Google Calendar**. Infraestructura con **Terraform** y ejecución **serverless**.

## Estructura
```
src/
  api/            # Webhook/HTTP (FastAPI en Lambda) — sin código aún
  agents/         # Router/Agents (Strands) — sin código aún
  tools/          # Tools: WhatsApp, Google Calendar — sin código aún
  orchestration/  # Definiciones Step Functions/flows (ASL) — placeholders
  core/           # Config/logging/seguridad — sin código aún
  storage/        # Abstracciones de almacenamiento (DynamoDB) — sin código aún
infra/
  terraform/
    envs/{dev,prod}/
    modules/
      api_gateway lambda dynamodb eventbridge step_functions secrets_manager bedrock_agentcore iam
```

## Requisitos
- Python 3.10+
- Terraform 1.7+
- AWS CLI configurado

## Primeros pasos
1. Crear `.venv` (este script lo hace por ti) y activar:
   ```bash
   source .venv/bin/activate
   ```
2. Copiar `.env.example` a `.env` y completar valores cuando corresponda.
3. Inicializar Terraform más adelante en `infra/terraform/envs/dev`.

## Roadmap
- Conectar webhook de WhatsApp Cloud API
- Router de intención (INFO_CENTRO | GESTION_CITAS) con Strands
- Tool de Google Calendar (CRUD eventos)
- Orquestación de recordatorios con EventBridge + Step Functions
- Observabilidad (CloudWatch, X-Ray) y guardrails
EOF
fi

# pyproject.toml mínimo (sin dependencias aún)
if [ ! -f pyproject.toml ]; then
  cat > pyproject.toml <<'EOF'
[project]
name = "pelvis-therapy-whatsapp-assistant"
version = "0.1.0"
description = "MVP multiagente (WhatsApp) con AWS Bedrock AgentCore + Strands"
authors = [{ name = "Pelvis Therapy" }]
readme = "README.md"
requires-python = ">=3.10"
dependencies = []  # se definirán en la siguiente iteración

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"
EOF
fi

# Makefile mínimo
if [ ! -f Makefile ]; then
  cat > Makefile <<'EOF'
.PHONY: venv activate tf-init-dev tf-validate

venv:
	python3 -m venv .venv

activate:
	@echo "Ejecuta: source .venv/bin/activate"

tf-init-dev:
	cd infra/terraform/envs/dev && terraform init

tf-validate:
	cd infra/terraform/envs/dev && terraform validate || true
EOF
fi

# Placeholders en src (sin código funcional)
for d in src src/api src/agents src/tools src/orchestration src/core src/storage; do
  [ -f "$d/__init__.py" ] || echo "# placeholder" > "$d/__init__.py"
done

# Placeholder de Step Functions (ASL) — solo estructura vacía
if [ ! -f src/orchestration/reminders_sfn.asl.json ]; then
  cat > src/orchestration/reminders_sfn.asl.json <<'EOF'
{
  "Comment": "Recordatorios T-1 día y reintento a las 4 horas (placeholder)",
  "StartAt": "Placeholder",
  "States": {
    "Placeholder": {
      "Type": "Succeed"
    }
  }
}
EOF
fi

# Tests placeholders
if [ ! -f tests/test_placeholder.py ]; then
  cat > tests/test_placeholder.py <<'EOF'
def test_scaffold():
    assert True
EOF
fi

# Docs placeholders
if [ ! -f docs/architecture.md ]; then
  cat > docs/architecture.md <<'EOF'
# Arquitectura (MVP) — Borrador

Este documento se llenará en la siguiente iteración (diagrama lógico, flujo de mensajes, agentes, orquestación, almacenamiento y seguridad).
EOF
fi

if [ ! -f docs/runbook.md ]; then
  cat > docs/runbook.md <<'EOF'
# Runbook Operativo — Borrador

Procedimientos de despliegue, rotación de secretos, recuperación ante fallos, y tableros de observabilidad. Se completará en iteraciones.
EOF
fi

# Terraform envs: dev/prod stubs
for env in dev prod; do
  if [ ! -f "infra/terraform/envs/${env}/main.tf" ]; then
    cat > "infra/terraform/envs/${env}/main.tf" <<'EOF'
terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# Modules se agregarán cuando definamos recursos reales

EOF
  fi

  if [ ! -f "infra/terraform/envs/${env}/variables.tf" ]; then
    cat > "infra/terraform/envs/${env}/variables.tf" <<'EOF'
variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}
EOF
  fi

  if [ ! -f "infra/terraform/envs/${env}/backend.tf" ]; then
    cat > "infra/terraform/envs/${env}/backend.tf" <<'EOF'
# Backend remoto (S3 + DynamoDB) se configurará luego.
# Ejemplo (para activar más adelante):
# terraform {
#   backend "s3" {
#     bucket         = "<tu-bucket-terraform>"
#     key            = "pelvis-therapy/${env}/terraform.tfstate"
#     region         = "us-east-1"
#     dynamodb_table = "<tu-tabla-lock>"
#     encrypt        = true
#   }
# }
EOF
  fi

done

# Terraform modules: README placeholders
for mod in api_gateway lambda dynamodb eventbridge step_functions secrets_manager bedrock_agentcore iam; do
  if [ ! -f "infra/terraform/modules/${mod}/README.md" ]; then
    echo "# ${mod} module — placeholder" > "infra/terraform/modules/${mod}/README.md"
  fi
  if [ ! -f "infra/terraform/modules/${mod}/main.tf" ]; then
    cat > "infra/terraform/modules/${mod}/main.tf" <<'EOF'
# module placeholder — recursos se añadirán en siguientes iteraciones
EOF
  fi
  [ -f "infra/terraform/modules/${mod}/variables.tf" ] || touch "infra/terraform/modules/${mod}/variables.tf"
  [ -f "infra/terraform/modules/${mod}/outputs.tf" ]   || touch "infra/terraform/modules/${mod}/outputs.tf"
done

# 5) Git init + primer commit
if [ ! -d .git ]; then
  say ">> Inicializando repo Git"
  git init
fi

say ">> Listo. Activa el entorno con: source .venv/bin/activate"

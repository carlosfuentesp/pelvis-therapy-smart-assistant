# Pelvis Therapy WhatsApp Assistant (MVP)

MVP multiagente (Strands + Amazon Bedrock AgentCore) para:
- FAQ/servicios
- Gestión de citas (Google Calendar)
- Recordatorios por WhatsApp + escalamiento SMS

## Instalación
1. Clonar el repositorio y crear un entorno virtual.
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt -r requirements-dev.txt
   ```
2. Instalar *pre-commit*.
   ```bash
   pre-commit install
   ```

## Variables de entorno
Configuradas en `app/config/settings.py` usando *pydantic-settings*:

| Variable | Descripción |
| --- | --- |
| `AWS_REGION` | Región AWS (ej. `us-east-1`). |
| `ENV` | Entorno de despliegue (`dev`, `prod`, etc.). |
| `S3_FAQ_BUCKET` | Bucket S3 con FAQs. |
| `DYNAMODB_TABLE` | Tabla DynamoDB para estado de conversación. |
| `OWNER_PHONE_E164` | Teléfono del dueño en formato E.164. |
| `GOOGLE_SA_SECRET_NAME` | Nombre del secreto con credenciales de Google. |

## Estructura de carpetas
```
.
├── app/            # Código de agentes, herramientas y runtime de Lambda
├── content/        # Contenido de referencia (servicios, FAQ)
├── infra/          # Terraform (módulos y entornos)
├── layers/         # Lambda layers compartidas
├── ops/            # Documentación operacional
├── scripts/        # Scripts auxiliares (bootstrap, etc.)
└── README.md
```

## Flujo de trabajo
1. Asegúrate de tener el entorno virtual activo.
2. Realiza cambios en `app/` u otras carpetas según necesidad.
3. Ejecuta verificaciones locales y pruebas.
4. Despliega la infraestructura y función Lambda cuando sea necesario.

## Pruebas
```bash
pre-commit run --all-files
pytest
```

## Despliegue
### Terraform
```bash
terraform -chdir=infra/terraform/envs/dev init
terraform -chdir=infra/terraform/envs/dev plan
terraform -chdir=infra/terraform/envs/dev apply
```
### Actualización de Lambda
El módulo `lambda_function` empaca automáticamente el contenido de `app/`. Para actualizar solo el código:
```bash
zip -r lambda.zip app
aws lambda update-function-code --function-name <nombre> --zip-file fileb://lambda.zip
```

## Ops
- [Runbooks](ops/runbooks.md)
- [Alarmas](ops/alarms.md)

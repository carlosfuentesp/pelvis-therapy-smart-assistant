# Aquí invocarás módulos: lambda_function, api_http, dynamodb_table, eventbridge_scheduler, sns_sms, secrets_manager, s3_bucket, ecr_repo (opcional).
locals {
  tags = {
    Project = "PelvisTherapyWA"
    Env     = "dev"
    Owner   = "Carlos"
  }
}

module "s3" {
  source = "../../modules/s3_bucket"
  name   = "pelvis-therapy-faq-dev"
  tags   = local.tags
}

module "ddb" {
  source = "../../modules/dynamodb_table"
  name   = "pelvis-therapy-state-dev"
  tags   = local.tags
}

# Placeholder del secreto con JSON vacío; luego lo actualizas con el SA real.
module "google_sa" {
  source = "../../modules/secrets_manager"
  name   = "pelvis/google/service-account"
  value  = jsonencode({ placeholder = true })
  tags   = local.tags
}

module "sns" {
  source               = "../../modules/sns"
  project_prefix       = var.project_prefix
  tags                 = local.tags
  enable_owner_sms     = false
  sms_owner_phone_e164 = "" # ignorado cuando enable_owner_sms = false
}

module "scheduler" {
  source         = "../../modules/eventbridge_scheduler"
  project_prefix = var.project_prefix
  tags           = local.tags
}

module "api" {
  source         = "../../modules/api_http"
  project_prefix = var.project_prefix
  lambda_arn     = module.lambda_meta.lambda_arn
  tags           = local.tags
  routes         = ["GET /webhook", "POST /webhook"] # ← importante
}


resource "aws_lambda_permission" "allow_sns_wa" {
  statement_id  = "AllowSNSWAInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_wa.lambda_name
  principal     = "sns.amazonaws.com"
  source_arn    = module.sns.wa_events_topic_arn
}

resource "aws_sns_topic_subscription" "wa_events_to_lambda" {
  topic_arn = module.sns.wa_events_topic_arn
  protocol  = "lambda"
  endpoint  = module.lambda_wa.lambda_arn
}

module "lambda" {
  source         = "../../modules/lambda_function"
  project_prefix = var.project_prefix
  function_name  = "router-hello"
  source_dir     = "${path.root}/../../../../app"
  handler        = "runtime/handler_lambda.handler" # <-- antes app/runtime/...
  env_vars = {
    DDB_TABLE  = module.ddb.table_name
    FAQ_BUCKET = module.s3.bucket_name
  }
  tags = local.tags
}

module "lambda_wa" {
  source         = "../../modules/lambda_function"
  project_prefix = var.project_prefix
  function_name  = "wa-events-handler"
  source_dir     = "${path.root}/../../../../app"
  handler        = "runtime/wa_events_handler.handler" # <-- sin app/
  env_vars = {
    VERIFY_TOKEN        = "PT_VERIFY_DEV" # cámbialo si quieres
    OWNER_WA_E164       = var.owner_wa_e164
    META_WA_SECRET_NAME = "pelvis/wa/meta-owner"
    OWNER_WA_TEMPLATE   = "owner_alert_v2"
    OWNER_WA_LANG       = "es_EC"
  }
  tags = local.tags
}

module "lambda_reminder" {
  source         = "../../modules/lambda_function"
  project_prefix = var.project_prefix
  function_name  = "reminder-dispatcher"
  source_dir     = "${path.root}/../../../../app"
  handler        = "runtime/reminder_dispatcher.handler" # <-- sin app/
  env_vars = {
    OWNER_WA_E164       = var.owner_wa_e164
    META_WA_SECRET_NAME = "pelvis/wa/meta-owner"
    OWNER_WA_TEMPLATE   = "owner_alert"
    OWNER_WA_LANG       = "es_EC"
  }
  tags = local.tags
}

module "lambda_meta" {
  source         = "../../modules/lambda_function"
  project_prefix = var.project_prefix
  function_name  = "meta-webhook"
  source_dir     = "${path.root}/../../../../app"
  handler        = "runtime/meta_webhook_handler.handler"
  env_vars = {
    VERIFY_TOKEN        = "PT_VERIFY_DEV" # cámbialo si quieres
    OWNER_WA_E164       = var.owner_wa_e164
    META_WA_SECRET_NAME = "pelvis/wa/meta-owner"
    OWNER_WA_TEMPLATE   = "owner_alert"
    OWNER_WA_LANG       = "es_EC"
  }
  tags = local.tags
}
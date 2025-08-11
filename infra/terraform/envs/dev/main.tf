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
    DDB_TABLE           = module.ddb.table_name
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
    DDB_TABLE           = module.ddb.table_name
    VERIFY_TOKEN        = "PT_VERIFY_DEV" # cámbialo si quieres
    OWNER_WA_E164       = var.owner_wa_e164
    META_WA_SECRET_NAME = "pelvis/wa/meta-owner"
    OWNER_WA_TEMPLATE   = "owner_alert"
    OWNER_WA_LANG       = "es_EC"
  }
  tags = local.tags
}

module "lambda_scheduler" {
  source         = "../../modules/lambda_function"
  project_prefix = var.project_prefix
  function_name  = "reminder-scheduler"
  source_dir     = "${path.root}/../../../../app"
  handler        = "runtime/reminder_scheduler.handler"
  env_vars = {
    AWS_ACCOUNT_ID          = data.aws_caller_identity.current.account_id
    DDB_TABLE               = module.ddb.table_name
    SCHEDULER_ROLE_ARN      = aws_iam_role.scheduler_invoke_role.arn
    REMINDER_DISPATCHER_ARN = module.lambda_reminder.lambda_arn
    ESCALATION_DELAY_MIN    = "60"
    OWNER_WA_E164           = var.owner_wa_e164
    META_WA_SECRET_NAME     = "pelvis/wa/meta-owner"
    OWNER_WA_TEMPLATE       = "owner_alert"
    OWNER_WA_LANG           = "es_EC"
    STAGE                   = "dev"
    FAST_MODE               = "1"
  }
  tags = local.tags
}

module "layer_google" {
  source     = "../../modules/lambda_layer"
  layer_name = "${var.project_prefix}-google-deps"
  source_dir = "${path.root}/../../../../layers/google"
  tags       = local.tags
}

module "lambda_appts" {
  source         = "../../modules/lambda_function"
  project_prefix = var.project_prefix
  function_name  = "appointments-manager"
  handler        = "runtime/appointments_manager.handler"
  source_dir     = "${path.root}/../../../../app"
  layers         = [module.layer_google.layer_arn]
  env_vars = {
    GCAL_SECRET_NAME        = "pelvis/gcal/sa"
    GCAL_CALENDAR_ID        = var.gcal_calendar_id   # agrega esta var en variables.tf
    TZ                      = "America/Guayaquil"
    REMINDER_SCHEDULER_NAME = "pt-dev-reminder-scheduler"
    OWNER_WA_E164           = var.owner_wa_e164
    META_WA_SECRET_NAME     = "pelvis/wa/meta-owner"
    OWNER_WA_TEMPLATE       = "owner_alert"
    OWNER_WA_LANG           = "es_EC"
  }
  tags = local.tags
}

# Adjunta el layer de Google a la lambda_appts
resource "aws_lambda_function_event_invoke_config" "appts_async" {
  function_name                = module.lambda_appts.lambda_name
  maximum_event_age_in_seconds = 60
  maximum_retry_attempts       = 0
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "scheduler_invoke_role" {
  name = "${var.project_prefix}-scheduler-invoke"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "scheduler.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
  tags = local.tags
}

resource "aws_iam_role_policy" "scheduler_invoke_policy" {
  name = "${var.project_prefix}-scheduler-invoke-policy"
  role = aws_iam_role.scheduler_invoke_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect : "Allow",
      Action : ["lambda:InvokeFunction"],
      Resource : module.lambda_reminder.lambda_arn
    }]
  })
}
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
  source              = "../../modules/sns"
  project_prefix      = var.project_prefix
  sms_owner_phone_e164= var.owner_phone_e164
  tags                = local.tags
}

module "scheduler" {
  source         = "../../modules/eventbridge_scheduler"
  project_prefix = var.project_prefix
  tags           = local.tags
}

module "lambda" {
  source         = "../../modules/lambda_function"
  project_prefix = var.project_prefix
  function_name  = "router-hello"
  source_file    = abspath("${path.root}/../../../../app/runtime/handler_lambda.py")
  env_vars = {
    DDB_TABLE   = module.ddb.table_name
    FAQ_BUCKET  = module.s3.bucket_name
    OWNER_TOPIC = module.sns.owner_sms_topic_arn
    GOOGLE_SA_SECRET_ARN = module.google_sa.secret_arn
  }
  tags = local.tags
}

module "api" {
  source         = "../../modules/api_http"
  project_prefix = var.project_prefix
  lambda_arn     = module.lambda.lambda_arn
  tags           = local.tags
}

module "lambda_wa" {
  source         = "../../modules/lambda_function"
  project_prefix = var.project_prefix
  function_name  = "wa-events-handler"
  handler        = "wa_events_handler.handler"
  source_file    = abspath("${path.root}/../../../../app/runtime/wa_events_handler.py")
  env_vars = {
    OWNER_TOPIC = module.sns.owner_sms_topic_arn
  }
  tags = local.tags
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

module "lambda_reminder" {
  source         = "../../modules/lambda_function"
  project_prefix = var.project_prefix
  function_name  = "reminder-dispatcher"
  handler        = "reminder_dispatcher.handler"
  source_file    = abspath("${path.root}/../../../../app/runtime/reminder_dispatcher.py")
  env_vars = {
    OWNER_TOPIC = module.sns.owner_sms_topic_arn
  }
  tags = local.tags
}
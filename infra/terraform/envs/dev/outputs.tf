output "faq_bucket" { value = module.s3.bucket_name }
output "state_table" { value = module.ddb.table_name }
output "google_secret_arn" { value = module.google_sa.secret_arn }
output "wa_events_topic" { value = module.sns.wa_events_topic_arn }
output "owner_sms_topic" { value = module.sns.owner_sms_topic_arn }
output "http_api_endpoint" { value = module.api.http_api_endpoint }
output "lambda_name" { value = module.lambda.lambda_name }
output "scheduler_role" { value = module.scheduler.scheduler_role_arn }
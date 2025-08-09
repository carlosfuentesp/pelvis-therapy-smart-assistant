variable "project_prefix" { type = string }
variable "sms_owner_phone_e164" { type = string } # +593...
variable "tags" { type = map(string) }

resource "aws_sns_topic" "wa_events" {
  name = "${var.project_prefix}-wa-events"
  tags = var.tags
}

resource "aws_sns_topic" "owner_sms" {
  name = "${var.project_prefix}-owner-sms"
  tags = var.tags
}

resource "aws_sns_topic_subscription" "owner_sms_sub" {
  topic_arn = aws_sns_topic.owner_sms.arn
  protocol  = "sms"
  endpoint  = var.sms_owner_phone_e164
}

resource "aws_sns_sms_preferences" "prefs" {
  default_sms_type = "Transactional"
}

output "wa_events_topic_arn" { value = aws_sns_topic.wa_events.arn }
output "owner_sms_topic_arn" { value = aws_sns_topic.owner_sms.arn }

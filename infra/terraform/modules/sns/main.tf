variable "project_prefix" {
  type = string
}

variable "tags" {
  type = map(string)
}

# Nuevo: controla si se crea el topic + suscripción SMS del propietario
variable "enable_owner_sms" {
  type    = bool
  default = false
}

# Nuevo: número E.164 solo si enable_owner_sms = true
variable "sms_owner_phone_e164" {
  type    = string
  default = ""
}

# Topic para eventos entrantes de WhatsApp (AWS End User Messaging Social -> SNS)
resource "aws_sns_topic" "wa_events" {
  name = "${var.project_prefix}-wa-events"
  tags = var.tags
}

# Topic/Suscripción SMS (opcional)
resource "aws_sns_topic" "owner_sms" {
  count = var.enable_owner_sms ? 1 : 0
  name  = "${var.project_prefix}-owner-sms"
  tags  = var.tags
}

resource "aws_sns_topic_subscription" "owner_sms_sub" {
  count     = var.enable_owner_sms ? 1 : 0
  topic_arn = aws_sns_topic.owner_sms[0].arn
  protocol  = "sms"
  endpoint  = var.sms_owner_phone_e164
}

resource "aws_sns_sms_preferences" "prefs" {
  count             = var.enable_owner_sms ? 1 : 0
  default_sms_type  = "Transactional"
}

output "wa_events_topic_arn" {
  value = aws_sns_topic.wa_events.arn
}

output "owner_sms_topic_arn" {
  value = var.enable_owner_sms ? aws_sns_topic.owner_sms[0].arn : null
}
variable "project_prefix" { type = string }
variable "sms_owner_phone_e164" { type = string } # +593...
variable "tags" { type = map(string) }

# Topic para eventos entrantes de WhatsApp (AWS End User Messaging Social -> SNS)
resource "aws_sns_topic" "wa_events" {
  name = "${var.project_prefix}-wa-events"
  tags = var.tags
}

# Topic para notificar a la propietaria por SMS
resource "aws_sns_topic" "owner_sms" {
  name = "${var.project_prefix}-owner-sms"
  tags = var.tags
}

# Suscripción SMS a la propietaria
resource "aws_sns_topic_subscription" "owner_sms_sub" {
  topic_arn = aws_sns_topic.owner_sms.arn
  protocol  = "sms"
  endpoint  = var.sms_owner_phone_e164
}

# (Opcional) Preferencias globales SMS (ajusta si quieres tipos/limites)
resource "aws_sns_sms_preferences" "prefs" {
  default_sms_type = "Transactional"
}

output "wa_events_topic_arn" { value = aws_sns_topic.wa_events.arn }
output "owner_sms_topic_arn" { value = aws_sns_topic.owner_sms.arn }
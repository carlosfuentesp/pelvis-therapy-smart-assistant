variable "region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region para despliegue"
}

variable "project_prefix" {
  type    = string
  default = "pt-dev"
}

variable "owner_phone_e164" {
  type        = string
  default     = ""
  description = "Número E.164 de la propietaria (+593XXXXXXXXX)"
}

variable "owner_wa_e164" {
  type    = string
  default = "+5939XXXXXXXX"
}

variable "gcal_calendar_id" {
  type        = string
  description = "Calendar ID de Pelvis Therapy"
}
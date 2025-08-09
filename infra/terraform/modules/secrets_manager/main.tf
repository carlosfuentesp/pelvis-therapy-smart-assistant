variable "name"  { type = string }
variable "value" { type = string }
variable "tags"  { type = map(string) }

resource "aws_secretsmanager_secret" "this" {
  name = var.name
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "v1" {
  secret_id     = aws_secretsmanager_secret.this.id
  secret_string = var.value
}

output "secret_arn" { value = aws_secretsmanager_secret.this.arn }
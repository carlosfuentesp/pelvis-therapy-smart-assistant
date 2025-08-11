variable "name" { type = string }
variable "tags" { type = map(string) }

resource "aws_dynamodb_table" "this" {
  name         = var.name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # Nuevos atributos para el GSI
  attribute {
    name = "gsi1pk"
    type = "S"
  }
  attribute {
    name = "gsi1sk"
    type = "S"
  }

  # GSI para buscar próximas citas por paciente
  global_secondary_index {
    name            = "gsi1"
    hash_key        = "gsi1pk"   # PATIENT#+5939...
    range_key       = "gsi1sk"   # ISO de la cita (UTC)
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = var.tags
}

output "table_name" { value = aws_dynamodb_table.this.name }

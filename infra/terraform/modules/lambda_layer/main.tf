variable "layer_name" {
  type = string
}

variable "source_dir" {
  type        = string
  default     = ""
  description = "Directorio con carpeta python/ en la raíz. Opcional si usas source_zip_path."
}

variable "source_zip_path" {
  type    = string
  default = ""
}

variable "tags" {
  type = map(string)
}

variable "s3_bucket_name" {
  type = string
}

variable "kms_key_arn" {
  type    = string
  default = ""
}

# Solo empaqueta si NO envías un ZIP preconstruido
data "archive_file" "zip" {
  count       = var.source_zip_path == "" && var.source_dir != "" ? 1 : 0
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.module}/layer.zip"
}

locals {
  zip_path = var.source_zip_path != "" ? var.source_zip_path : data.archive_file.zip[0].output_path
}

resource "aws_s3_object" "layer_zip" {
  bucket                 = var.s3_bucket_name
  key                    = "${var.layer_name}.zip"
  source                 = local.zip_path
  etag                   = filemd5(local.zip_path)
  content_type           = "application/zip"
  server_side_encryption = var.kms_key_arn != "" ? "aws:kms" : "AES256"
  kms_key_id             = var.kms_key_arn != "" ? var.kms_key_arn : null
}

resource "aws_lambda_layer_version" "this" {
  layer_name          = var.layer_name
  description         = "Lambda layer for ${var.layer_name}"
  compatible_runtimes = ["python3.12"]
  s3_bucket           = var.s3_bucket_name
  s3_key              = aws_s3_object.layer_zip.key
}

output "layer_arn" {
  value = aws_lambda_layer_version.this.arn
}
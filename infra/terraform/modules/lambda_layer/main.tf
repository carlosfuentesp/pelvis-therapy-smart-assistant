variable "layer_name"   { type = string }
variable "source_dir"   { type = string }
variable "tags"         { type = map(string) }
variable "s3_bucket_name" { type = string }  # <- ahora es obligatorio
variable "kms_key_arn"  { 
  type = string
  default = "" 
}

data "archive_file" "zip" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.module}/layer.zip"
}

resource "aws_s3_object" "layer_zip" {
  bucket                 = var.s3_bucket_name
  key                    = "${var.layer_name}.zip"
  source                 = data.archive_file.zip.output_path
  etag                   = filemd5(data.archive_file.zip.output_path)
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
  # opcional: license_info, description más larga, etc.
}

output "layer_arn" { value = aws_lambda_layer_version.this.arn }
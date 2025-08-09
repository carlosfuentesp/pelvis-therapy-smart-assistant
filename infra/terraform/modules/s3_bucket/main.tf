variable "name" { type = string }
variable "tags" { type = map(string) }

resource "aws_s3_bucket" "this" {
  bucket = var.name
  tags   = var.tags
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

# Mantener objetos de /faq por 365 días (ajustable)
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    id     = "faq-retention"
    status = "Enabled"
    filter { prefix = "faq/" }
    expiration { days = 365 }
  }
}

output "bucket_name" { value = aws_s3_bucket.this.bucket }
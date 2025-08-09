# Backend remoto (S3 + DynamoDB) se configurará luego.
# Ejemplo (para activar más adelante):
# terraform {
#   backend "s3" {
#     bucket         = "<tu-bucket-terraform>"
#     key            = "pelvis-therapy/${env}/terraform.tfstate"
#     region         = "us-east-1"
#     dynamodb_table = "<tu-tabla-lock>"
#     encrypt        = true
#   }
# }

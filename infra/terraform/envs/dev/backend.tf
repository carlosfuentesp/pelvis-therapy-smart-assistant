# Ajusta nombres de bucket y tabla de lock
terraform {
  backend "s3" {
    bucket         = "pelvis-therapy-tfstate-dev"
    key            = "infra/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "pelvis-therapy-tf-locks"
    encrypt        = true
  }
}

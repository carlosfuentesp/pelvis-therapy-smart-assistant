variable "project_prefix" {
  type = string
}

variable "function_name" {
  type = string
}

variable "runtime" {
  type    = string
  default = "python3.12"
}

# Pasado desde envs/dev: ruta a la carpeta "app" (zip completa)
variable "source_dir" {
  type    = string
  default = ""
}

# Handler debe incluir el prefijo "app/..."
variable "handler" {
  type    = string
  default = "app/runtime/handler_lambda.handler"
}

variable "env_vars" {
  type    = map(string)
  default = {}
}

variable "tags" {
  type = map(string)
}

data "archive_file" "zip" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.module}/lambda.zip"
}

data "aws_iam_policy_document" "assume" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "${var.project_prefix}-${var.function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "lambda_inline" {
  statement {
    sid     = "Logs"
    effect  = "Allow"
    actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }

  statement {
    sid     = "DDBBasic"
    effect  = "Allow"
    actions = ["dynamodb:GetItem","dynamodb:PutItem","dynamodb:UpdateItem","dynamodb:DeleteItem","dynamodb:Query"]
    resources = ["*"]
  }

  statement {
    sid     = "S3ReadFAQ"
    effect  = "Allow"
    actions = ["s3:GetObject","s3:ListBucket"]
    resources = ["*"]
  }

  statement {
    sid     = "SecretsRead"
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]
    resources = ["*"]
  }

  statement {
    sid     = "SNSPublish"
    effect  = "Allow"
    actions = ["sns:Publish"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "lambda_policy" {
  name   = "${var.project_prefix}-${var.function_name}-policy"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.lambda_inline.json
}

resource "aws_lambda_function" "this" {
  function_name    = "${var.project_prefix}-${var.function_name}"
  role             = aws_iam_role.lambda_role.arn
  filename         = data.archive_file.zip.output_path
  source_code_hash = data.archive_file.zip.output_base64sha256
  runtime          = var.runtime
  handler          = var.handler
  timeout          = 10

  environment {
    variables = var.env_vars
  }

  tags = var.tags
}

output "lambda_arn" {
  value = aws_lambda_function.this.arn
}

output "lambda_name" {
  value = aws_lambda_function.this.function_name
}
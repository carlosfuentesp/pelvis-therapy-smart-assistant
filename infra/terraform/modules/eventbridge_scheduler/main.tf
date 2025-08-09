variable "project_prefix" { type = string }
variable "tags" { type = map(string) }

data "aws_iam_policy_document" "scheduler_trust" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "scheduler_invoke_lambda" {
  name               = "${var.project_prefix}-scheduler-invoke-lambda"
  assume_role_policy = data.aws_iam_policy_document.scheduler_trust.json
  tags               = var.tags
}

data "aws_iam_policy_document" "scheduler_policy_doc" {
  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction",
      "lambda:InvokeAsync"
    ]
    resources = ["*"] # Afinar por ARN de Lambda cuando la tengamos
  }
}

resource "aws_iam_policy" "scheduler_policy" {
  name   = "${var.project_prefix}-scheduler-policy"
  policy = data.aws_iam_policy_document.scheduler_policy_doc.json
}

resource "aws_iam_role_policy_attachment" "attach" {
  role       = aws_iam_role.scheduler_invoke_lambda.name
  policy_arn = aws_iam_policy.scheduler_policy.arn
}

output "scheduler_role_arn" { value = aws_iam_role.scheduler_invoke_lambda.arn }

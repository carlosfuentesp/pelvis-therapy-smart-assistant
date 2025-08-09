variable "project_prefix" { type = string }
variable "lambda_arn"     { type = string }
variable "tags"           { type = map(string) }

resource "aws_apigatewayv2_api" "http" {
  name          = "${var.project_prefix}-http"
  protocol_type = "HTTP"
  tags          = var.tags
}

resource "aws_apigatewayv2_stage" "dev" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "dev"
  auto_deploy = true
  tags        = var.tags
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = var.lambda_arn
  payload_format_version = "2.0"
}

# Ruta de webhook (luego la conectaremos a WhatsApp/SNS si decides usar API, por ahora hello)
resource "aws_apigatewayv2_route" "any_webhook" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "POST /webhook"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Permiso para que API Gateway invoque Lambda
resource "aws_lambda_permission" "allow_apigw" {
  statement_id  = "AllowAPIGwInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

output "http_api_endpoint" { value = aws_apigatewayv2_stage.dev.invoke_url }
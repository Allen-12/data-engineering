resource "aws_cloudwatch_log_group" "pipeline" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 14
}

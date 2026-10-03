output "function_name" {
  value = aws_lambda_function.pipeline.function_name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.pipeline.repository_url
}

output "schedule_rule" {
  value = aws_cloudwatch_event_rule.daily.name
}

resource "aws_lambda_function" "pipeline" {
  function_name = var.function_name
  role          = aws_iam_role.pipeline.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.pipeline.repository_url}@${docker_registry_image.pipeline.sha256_digest}"
  architectures = ["arm64"]
  memory_size   = 1024
  timeout       = 300

  # AWS_REGION is reserved: Lambda sets it automatically, so it must not be listed here.
  # POLARS_TEMP_DIR: Lambda has no $HOME and only /tmp is writable, but Polars chmods its
  # temp dir and can't do that to /tmp itself, so it needs a subdirectory it can own.
  environment {
    variables = {
      POLARS_TEMP_DIR = "/tmp/polars"
      DEST_BUCKET     = var.dest_bucket_name
      DEST_PREFIX     = var.dest_prefix
      SOURCE_BUCKET   = var.source_bucket
      SOURCE_YEAR     = tostring(var.source_year)
      SAMPLE_SIZE     = tostring(var.sample_size)
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.pipeline,
    aws_iam_role_policy.pipeline,
  ]
}

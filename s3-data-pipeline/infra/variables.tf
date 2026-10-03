variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "aws_profile" {
  description = "Named AWS CLI profile with permission to create the resources (the deployer, not the pipeline user)."
  type        = string
  default     = "terraform-deployer"
}

variable "docker_host" {
  description = "Docker daemon socket. Empty means Docker Desktop's per-user macOS socket."
  type        = string
  default     = ""
}

variable "function_name" {
  type    = string
  default = "s3-data-pipeline-dev"
}

variable "dest_bucket_name" {
  description = "Existing S3 bucket the pipeline writes to. Created manually, not managed by Terraform."
  type        = string
}

variable "dest_prefix" {
  type    = string
  default = "processed/noaa-gsod"
}

variable "source_bucket" {
  type    = string
  default = "noaa-gsod-pds"
}

variable "source_year" {
  type    = number
  default = 2024
}

variable "sample_size" {
  type    = number
  default = 50
}

variable "schedule_enabled" {
  description = "Whether the EventBridge schedule actually triggers the Lambda. Off while testing."
  type        = bool
  default     = false
}

variable "schedule_expression" {
  description = "EventBridge schedule. Default: daily at 06:00 UTC."
  type        = string
  default     = "cron(0 6 * * ? *)"
}

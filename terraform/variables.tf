variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-2"
}

variable "bucket_name" {
  description = "Recording bucket name"
  type        = string
}
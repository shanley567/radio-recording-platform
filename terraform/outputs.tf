output "bucket_name" {
  value = aws_s3_bucket.recordings.bucket
}

output "bucket_arn" {
  value = aws_s3_bucket.recordings.arn
}

output "ecr_repository_url" {
  value = aws_ecr_repository.generator.repository_url
}
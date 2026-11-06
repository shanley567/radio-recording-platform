resource "aws_s3_bucket" "recordings" {
  bucket = var.bucket_name

  tags = {
    Project     = "radio-recording-platform"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "recordings" {

  bucket = aws_s3_bucket.recordings.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "recordings" {

  bucket = aws_s3_bucket.recordings.id
  # Rule to encrypt all objects at rest
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Prevent accidental public access to the S3 bucket 
# by blocking public ACLs and policies
resource "aws_s3_bucket_public_access_block" "recordings" {

  bucket = aws_s3_bucket.recordings.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
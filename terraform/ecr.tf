resource "aws_ecr_repository" "generator" {

  name = "synthetic-generator"

  image_scanning_configuration {
    scan_on_push = true
  }

  force_delete = true
}
locals {
  oidc_provider_url = replace(
    module.eks.cluster_oidc_issuer_url,
    "https://",
    ""
  )
}

resource "aws_iam_policy" "generator_s3_upload" {
  name = "RadioPlatformS3UploadPolicy"

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "s3:PutObject",
          "s3:AbortMultipartUpload"
        ]

        Resource = "${aws_s3_bucket.recordings.arn}/*"
      }
    ]
  })
}

data "aws_iam_policy_document" "generator_assume_role" {
  statement {
    effect = "Allow"

    actions = [
      "sts:AssumeRoleWithWebIdentity"
    ]

    principals {
      type = "Federated"

      identifiers = [
        module.eks.oidc_provider_arn
      ]
    }

    condition {
      test = "StringEquals"

      variable = "${local.oidc_provider_url}:sub"

      values = [
        "system:serviceaccount:radio-platform:synthetic-generator"
      ]
    }
  }
}

resource "aws_iam_role" "generator" {
  name               = "radio-platform-generator"
  assume_role_policy = data.aws_iam_policy_document.generator_assume_role.json
}

resource "aws_iam_role_policy_attachment" "generator_s3" {
  role       = aws_iam_role.generator.name
  policy_arn = aws_iam_policy.generator_s3_upload.arn
}
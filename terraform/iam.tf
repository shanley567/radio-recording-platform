locals {
  oidc_provider_url = replace(
    data.aws_eks_cluster.this.identity[0].oidc[0].issuer,
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

data "aws_eks_cluster" "this" {
  name = module.eks.cluster_name
}

data "aws_iam_openid_connect_provider" "eks" {
  url = data.aws_eks_cluster.this.identity[0].oidc[0].issuer
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
        data.aws_iam_openid_connect_provider.eks.arn
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

  name = "radio-platform-generator"

  assume_role_policy = data.aws_iam_policy_document.generator_assume_role.json
}


resource "aws_iam_role_policy_attachment" "generator_s3" {

  role = aws_iam_role.generator.name

  policy_arn = aws_iam_policy.generator_s3_upload.arn
}
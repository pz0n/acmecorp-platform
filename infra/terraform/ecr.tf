resource "aws_ecr_repository" "payments_api" {
  name                 = "acmecorp/payments-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project     = "acmecorp-platform"
    Environment = "dev"
    Service     = "payments-api"
  }
}
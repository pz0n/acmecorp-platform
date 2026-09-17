output "payments_api_ecr_url" {
  description = "ECR repository URL for the Payments API"
  value       = aws_ecr_repository.payments_api.repository_url
}
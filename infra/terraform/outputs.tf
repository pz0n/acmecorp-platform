output "vpc_id" {
  description = "ID of the AcmeCorp VPC"
  value       = aws_vpc.acmecorp.id
}

output "public_subnet_ids" {
  description = "IDs of the AcmeCorp public subnets"
  value = [
    aws_subnet.public_a.id,
    aws_subnet.public_b.id
  ]
}

output "private_subnet_ids" {
  description = "IDs of the AcmeCorp private subnets"
  value = [
    aws_subnet.private_a.id,
    aws_subnet.private_b.id
  ]
}

output "payments_api_ecr_url" {
  description = "ECR repository URL for the payments API"
  value       = aws_ecr_repository.payments_api.repository_url
}

output "ecs_cluster_name" {
  description = "Name of the AcmeCorp ECS cluster"
  value       = aws_ecs_cluster.acmecorp.name
}

output "payments_api_task_definition_arn" {
  description = "ARN of the payments API ECS task definition"
  value       = aws_ecs_task_definition.payments_api.arn
}
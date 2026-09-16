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
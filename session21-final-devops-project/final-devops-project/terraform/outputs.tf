output "vpc_id" {
  value = aws_vpc.this.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "ingress_security_group_id" {
  value = aws_security_group.ingress.id
}

output "nodes_security_group_id" {
  value = aws_security_group.nodes.id
}

output "ecr_repository_url" {
  description = "Push the scanned image here (image.repository in the Helm values)"
  value       = aws_ecr_repository.app.repository_url
}

output "artifacts_bucket" {
  value = aws_s3_bucket.artifacts.bucket
}

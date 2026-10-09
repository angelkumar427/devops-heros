output "region" {
  value = var.region
}

output "vpc_id" {
  value = aws_vpc.this.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "cluster_version" {
  value = aws_eks_cluster.this.version
}

output "cluster_endpoint" {
  value = aws_eks_cluster.this.endpoint
}

output "node_group" {
  value = "${aws_eks_node_group.default.node_group_name} (${join(",", var.node_instance_types)}, desired ${var.node_desired_size})"
}

output "configure_kubectl" {
  description = "Point kubectl at the new cluster"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${aws_eks_cluster.this.name}"
}

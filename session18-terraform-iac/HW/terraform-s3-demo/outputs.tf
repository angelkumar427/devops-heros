output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.this.arn
}

output "bucket_region" {
  description = "Region the bucket lives in"
  value       = aws_s3_bucket.this.region
}

output "versioning_status" {
  description = "Versioning state of the bucket"
  value       = aws_s3_bucket_versioning.this.versioning_configuration[0].status
}

output "sample_object" {
  description = "S3 URI of the sample object"
  value       = "s3://${aws_s3_bucket.this.id}/${aws_s3_object.readme.key}"
}

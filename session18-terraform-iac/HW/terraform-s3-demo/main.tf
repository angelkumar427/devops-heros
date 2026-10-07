# Bucket names are globally unique in AWS, so a random suffix avoids collisions.
resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "this" {
  bucket = "${var.project_name}-${var.environment}-${random_id.suffix.hex}"

  # A VERSIONED bucket keeps every old version and delete marker, so a plain
  # destroy fails with BucketNotEmpty. force_destroy purges all versions first.
  # It is deliberately OFF for prod, where wiping data must never be automatic.
  force_destroy = var.environment != "prod"

  tags = {
    Name        = "${var.project_name}-${var.environment}"
    Environment = var.environment
  }
}

# Keep every previous version of every object (protects against overwrite/delete).
resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# Encrypt every object at rest by default.
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block every form of public access - the single most important S3 setting.
resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# A sample object, so the demo shows data actually landing in the bucket.
resource "aws_s3_object" "readme" {
  bucket       = aws_s3_bucket.this.id
  key          = "welcome.txt"
  content      = "Created by Terraform for ${var.project_name} (${var.environment})\n"
  content_type = "text/plain"

  # Create the object only AFTER versioning is enabled, and on destroy remove it
  # BEFORE versioning is suspended - otherwise its first version can be written
  # unversioned, and teardown can leave versions stranded in a suspended bucket.
  depends_on = [aws_s3_bucket_versioning.this]
}

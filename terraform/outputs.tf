output "s3_bucket_name" {
  value = aws_s3_bucket.data_pipeline_bucket.id
}
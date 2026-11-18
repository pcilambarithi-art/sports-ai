output "app_public_ip" {
  description = "Public IPv4 address of the ApexPulse EC2 application server"
  value       = aws_instance.app.public_ip
}

output "app_url" {
  description = "HTTP URL for the deployed ApexPulse frontend"
  value       = "http://${aws_instance.app.public_ip}"
}

output "rds_postgres_endpoint" {
  description = "Private Amazon RDS PostgreSQL 16 endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "artifacts_s3_bucket" {
  description = "S3 bucket storing your trained model artifacts (read-only copy) and uploaded videos"
  value       = aws_s3_bucket.artifacts.bucket
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for application logs"
  value       = aws_cloudwatch_log_group.app.name
}

output "model_upload_command" {
  description = "Run this AWS CLI command to upload your existing D:\\V3 model and dataset to S3"
  value       = "aws s3 sync D:\\V3\\trained_models s3://${aws_s3_bucket.artifacts.bucket}/trained_models/ && aws s3 cp D:\\V3\\preprocessed_workout_dataset.csv s3://${aws_s3_bucket.artifacts.bucket}/dataset/preprocessed_workout_dataset.csv"
}

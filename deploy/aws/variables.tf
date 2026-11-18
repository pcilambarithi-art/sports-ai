variable "project_name" {
  description = "Project prefix for AWS resource names"
  type        = string
  default     = "apexpulse-sports"
}

variable "environment" {
  description = "Deployment environment (staging or production)"
  type        = string
  default     = "staging"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "ec2_instance_type" {
  description = "EC2 instance type (minimum 16 GB RAM recommended for 2.93 GB ExtraTrees model)"
  type        = string
  default     = "m6i.xlarge"
}

variable "ec2_key_name" {
  description = "Optional existing EC2 SSH key pair name"
  type        = string
  default     = ""
}

variable "admin_cidr" {
  description = "CIDR block permitted for SSH and direct API admin access (e.g., YOUR.IP.ADDR.ESS/32)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "db_instance_class" {
  description = "RDS PostgreSQL instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "sports_coaching"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "apexpulse_admin"
}

variable "db_password" {
  description = "PostgreSQL master password (min 12 chars)"
  type        = string
  sensitive   = true
}

variable "app_secret_key" {
  description = "JWT signing secret key (min 32 random chars)"
  type        = string
  sensitive   = true
}

variable "sensor_api_key" {
  description = "API key for wearable / IoT telemetry webhook ingestion"
  type        = string
  sensitive   = true
}

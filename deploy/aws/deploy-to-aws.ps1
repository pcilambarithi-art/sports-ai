<#
.SYNOPSIS
  Guided AWS deployment script for ApexPulse AI-Powered Sports Coaching System.
.DESCRIPTION
  1. Verifies AWS CLI credentials and Terraform installation.
  2. Validates and plans/applies Terraform infrastructure (VPC, RDS PostgreSQL 16, S3, EC2 16GB RAM, CloudWatch).
  3. Copies D:\V3\trained_models and D:\V3\preprocessed_workout_dataset.csv to S3 (READ-ONLY copy; D:\V3 is never modified).
#>

param(
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$AwsDir = "D:\sports-coaching-system\deploy\aws"

Write-Host "=== Step 1: Verifying AWS Credentials ===" -ForegroundColor Cyan
aws sts get-caller-identity | Out-Host

if (-not (Test-Path "$AwsDir\terraform.tfvars")) {
    Write-Host "terraform.tfvars not found. Copy terraform.tfvars.example -> terraform.tfvars and set strong secrets first." -ForegroundColor Yellow
    exit 1
}

Push-Location $AwsDir
try {
    Write-Host "`n=== Step 2: Terraform Init & Validate ===" -ForegroundColor Cyan
    terraform init
    terraform validate

    if ($Apply) {
        Write-Host "`n=== Step 3: Applying AWS Infrastructure ===" -ForegroundColor Cyan
        terraform apply

        $Bucket = terraform output -raw artifacts_s3_bucket
        Write-Host "`n=== Step 4: Uploading Existing Trained Model & Dataset to S3 ($Bucket) ===" -ForegroundColor Green
        aws s3 sync "D:\V3\trained_models" "s3://$Bucket/trained_models/"
        aws s3 cp "D:\V3\preprocessed_workout_dataset.csv" "s3://$Bucket/dataset/preprocessed_workout_dataset.csv"
        Write-Host "`nDeployment artifacts uploaded! Public URL:" -ForegroundColor Green
        terraform output app_url
    } else {
        Write-Host "`n=== Step 3: Terraform Plan (Dry Run) ===" -ForegroundColor Cyan
        terraform plan
        Write-Host "`nDry-run plan complete. Re-run with -Apply to provision AWS resources." -ForegroundColor Yellow
    }
} finally {
    Pop-Location
}

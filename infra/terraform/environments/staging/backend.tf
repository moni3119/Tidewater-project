terraform {
  backend "s3" {
    bucket         = "tidewater-terraform-state-849381699036"
    key            = "tidewater/staging/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "tidewater-terraform-lock"
    encrypt        = true
  }
}

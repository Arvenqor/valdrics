variable "gcp_project_id" {
  description = "Google Cloud project ID that owns the Terraform state bucket."
  type        = string
}

variable "gcp_region" {
  description = "Default Google Cloud region for provider operations."
  type        = string
  default     = "europe-west2"
}

variable "state_bucket_name" {
  description = "Globally unique Cloud Storage bucket name for Terraform state."
  type        = string
}

variable "state_bucket_location" {
  description = "Cloud Storage bucket location for Terraform state."
  type        = string
  default     = "EUROPE-WEST2"
}

variable "terraform_state_principals" {
  description = "IAM principals allowed to read and write Terraform state objects."
  type        = set(string)
  default     = []
}

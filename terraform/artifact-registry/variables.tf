variable "gcp_project_id" {
  description = "Google Cloud project ID that owns Artifact Registry."
  type        = string
}

variable "gcp_region" {
  description = "Google Cloud region for the Artifact Registry repository."
  type        = string
}

variable "artifact_registry_repository_id" {
  description = "Artifact Registry Docker repository ID that stores backend images."
  type        = string
  default     = "valdrics-runtime"
}

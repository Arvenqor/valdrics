output "artifact_registry_repository" {
  value = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.runtime.repository_id}"
}

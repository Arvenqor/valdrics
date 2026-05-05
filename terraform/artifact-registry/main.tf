resource "google_project_service" "artifact_registry" {
  project            = var.gcp_project_id
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "runtime" {
  project       = var.gcp_project_id
  location      = var.gcp_region
  repository_id = var.artifact_registry_repository_id
  description   = "Digest-pinned Valdrics backend images"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry]
}

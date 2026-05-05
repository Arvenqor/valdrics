resource "google_project_service" "storage" {
  project            = var.gcp_project_id
  service            = "storage.googleapis.com"
  disable_on_destroy = false
}

resource "google_storage_bucket" "terraform_state" {
  name                        = var.state_bucket_name
  location                    = var.state_bucket_location
  project                     = var.gcp_project_id
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  labels = {
    managed_by = "terraform"
    purpose    = "terraform-state"
  }

  versioning {
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [google_project_service.storage]
}

resource "google_storage_bucket_iam_member" "terraform_state_object_admin" {
  for_each = var.terraform_state_principals

  bucket = google_storage_bucket.terraform_state.name
  role   = "roles/storage.objectAdmin"
  member = each.value
}

resource "google_storage_bucket_iam_member" "terraform_state_bucket_reader" {
  for_each = var.terraform_state_principals

  bucket = google_storage_bucket.terraform_state.name
  role   = "roles/storage.legacyBucketReader"
  member = each.value
}

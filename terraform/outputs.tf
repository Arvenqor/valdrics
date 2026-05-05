output "api_service_name" {
  value = google_cloud_run_v2_service.api.name
}

output "api_service_uri" {
  value = google_cloud_run_v2_service.api.uri
}

output "api_edge_public_ip" {
  value = google_compute_global_address.api_edge.address
}

output "api_public_hostname" {
  value = cloudflare_dns_record.api.name
}

output "batch_job_name" {
  value = google_cloud_run_v2_job.batch.name
}

output "cloud_tasks_queue_name" {
  value = google_cloud_tasks_queue.runtime.name
}

output "runtime_service_account_email" {
  value = google_service_account.runtime.email
}

output "batch_service_account_email" {
  value = google_service_account.batch.email
}

output "internal_invoker_service_account_email" {
  value = google_service_account.internal_invoker.email
}

output "scheduler_invoker_service_account_email" {
  value = google_service_account.scheduler_invoker.email
}

output "scheduler_job_names" {
  value = sort([for job in google_cloud_scheduler_job.managed : job.name])
}

output "secret_manager_secret_ids" {
  value     = { for key, secret in google_secret_manager_secret.runtime : key => secret.secret_id }
  sensitive = true
}

output "cloudflare_pages_project_name" {
  value = cloudflare_pages_project.dashboard.name
}

output "cloudflare_pages_subdomain" {
  value = cloudflare_pages_project.dashboard.subdomain
}

output "cloudflare_api_dns_record_id" {
  value = cloudflare_dns_record.api.id
}

output "supabase_project_ref" {
  value = supabase_project.platform.id
}

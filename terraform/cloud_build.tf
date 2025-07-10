# Cloud Build triggers (uncomment and configure after GitHub connection)
# Note: GitHub connection must be set up manually in GCP Console first

resource "google_cloudbuild_trigger" "main_branch" {
  name            = "${var.app_name}-main-trigger"
  description     = "Trigger for main branch pushes"
  service_account = google_service_account.cloud_build.id
  
  github {
    owner = "Higashi-Masafumi"  # Replace with your GitHub username
    name  = "jaXiv"        # Replace with your repo name
    push {
      branch = "^main$"
    }
  }
  
  filename = "cloudbuild.yaml"
  
  depends_on = [google_project_service.required_apis]
}

# Output Cloud Build service account email for reference
output "cloud_build_service_account" {
  description = "Cloud Build service account email"
  value       = google_service_account.cloud_build.email
} 
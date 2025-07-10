# Artifact Registry repository for storing Docker images
resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = "${var.app_name}-images"
  description   = "Docker images for ${var.app_name} application"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
} 
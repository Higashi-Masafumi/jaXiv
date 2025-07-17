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
  
  # Terraformで管理される環境変数をCloud Build Triggerに注入
  substitutions = {
    _REGION                = var.region
    _REPOSITORY           = google_artifact_registry_repository.main.name
    _BACKEND_SERVICE_NAME = google_cloud_run_v2_service.backend.name
    _FRONTEND_SERVICE_NAME = google_cloud_run_v2_service.frontend.name
    _CLOUD_RUN_SA         = google_service_account.cloud_run.email
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_cloudbuild_trigger" "manual_base_image_build" {
  name            = "manual-build-backend-base-image"
  description     = "Manually trigger to build the backend base image with TeX Live."
  service_account = google_service_account.cloud_build.id
  filename        = "cloudbuild-base.yaml"

  # Same GitHub configuration as main_branch trigger
  github {
    owner = "Higashi-Masafumi"  # Same as main_branch trigger
    name  = "jaXiv"             # Same as main_branch trigger

    pull_request {
      branch = "^main$"
    }
  }

  substitutions = {
    _REGION                = var.region
    _REPOSITORY            = google_artifact_registry_repository.main.name
    _BACKEND_SERVICE_NAME  = google_cloud_run_v2_service.backend.name
    _FRONTEND_SERVICE_NAME = google_cloud_run_v2_service.frontend.name
    _CLOUD_RUN_SA          = google_service_account.cloud_run.email
  }

  depends_on = [google_project_service.required_apis]
}

# Output moved to outputs.tf 
# Backend Cloud Run service
resource "google_cloud_run_v2_service" "backend" {
  name               = "${var.app_name}-backend"
  location           = var.region

  template {
    service_account = google_service_account.cloud_run.email
    
    containers {
      image = var.backend_image

      ports {
        container_port = 8000
      }

      env {
        name = "SUPABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.supabase_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "SUPABASE_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.supabase_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "POSTGRES_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "BUCKET_NAME"
        value = "translated-arxiv-bucket"  # Supabaseのバケット名
      }

      env {
        name = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name = "MISTRAL_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.mistral_api_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Frontend Cloud Run service
resource "google_cloud_run_v2_service" "frontend" {
  name               = "${var.app_name}-frontend"
  location           = var.region

  template {
    service_account = google_service_account.cloud_run.email
    
    containers {
      image = var.frontend_image

      ports {
        container_port = 3000
      }

      env {
        name = "VITE_BACKEND_BASE_URL"
        value = google_cloud_run_v2_service.backend.uri
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
  }

  depends_on = [google_project_service.required_apis]
}

# IAM policy for public access to services
resource "google_cloud_run_service_iam_policy" "backend_noauth" {
  location = google_cloud_run_v2_service.backend.location
  project  = google_cloud_run_v2_service.backend.project
  service  = google_cloud_run_v2_service.backend.name

  policy_data = data.google_iam_policy.noauth.policy_data
}

resource "google_cloud_run_service_iam_policy" "frontend_noauth" {
  location = google_cloud_run_v2_service.frontend.location
  project  = google_cloud_run_v2_service.frontend.project
  service  = google_cloud_run_v2_service.frontend.name

  policy_data = data.google_iam_policy.noauth.policy_data
} 
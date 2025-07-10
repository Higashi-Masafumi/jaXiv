# Secret Manager secrets for application configuration
resource "google_secret_manager_secret" "supabase_url" {
  secret_id = "${var.app_name}-supabase-url"
  
  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "supabase_url" {
  secret      = google_secret_manager_secret.supabase_url.id
  secret_data = var.supabase_url
}

resource "google_secret_manager_secret" "supabase_key" {
  secret_id = "${var.app_name}-supabase-key"
  
  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "supabase_key" {
  secret      = google_secret_manager_secret.supabase_key.id
  secret_data = var.supabase_key
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "${var.app_name}-database-url"
  
  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = var.database_url
} 
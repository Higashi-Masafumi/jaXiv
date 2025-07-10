variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "asia-northeast1"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "jaxiv"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "backend_image" {
  description = "Backend Docker image URI"
  type        = string
  default     = "gcr.io/cloudrun/hello"  # ダミーイメージ（Cloud Buildで更新される）
}

variable "frontend_image" {
  description = "Frontend Docker image URI"
  type        = string
  default     = "gcr.io/cloudrun/hello"  # ダミーイメージ（Cloud Buildで更新される）
}

# Secrets for the application
variable "supabase_url" {
  description = "Supabase URL"
  type        = string
  sensitive   = true
}

variable "supabase_key" {
  description = "Supabase Key"
  type        = string
  sensitive   = true
}

variable "database_url" {
  description = "Database connection URL"
  type        = string
  sensitive   = true
} 
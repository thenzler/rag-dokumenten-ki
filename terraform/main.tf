# Cloud Storage Buckets
resource "google_storage_bucket" "upload_bucket" {
  name          = "${var.project_id}-rag-uploads"
  location      = var.region
  storage_class = "STANDARD"
  
  # Uniform bucket-level access aktivieren (empfohlen)
  uniform_bucket_level_access = true
  
  # Objektversionierung (optional)
  versioning {
    enabled = true
  }
}

resource "google_storage_bucket" "processed_bucket" {
  name          = "${var.project_id}-rag-processed"
  location      = var.region
  storage_class = "STANDARD"
  
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "tfstate_bucket" {
  name          = "${var.project_id}-tf-state"
  location      = var.region
  storage_class = "STANDARD"
  
  uniform_bucket_level_access = true
  
  # Versionierung für Terraform State aktivieren
  versioning {
    enabled = true
  }
}

# PostgreSQL Cloud SQL Instanz
resource "google_sql_database_instance" "postgres" {
  name             = "rag-postgres-instance"
  database_version = var.db_version
  region           = var.region
  
  settings {
    tier = var.db_tier
    
    # Backup-Konfiguration
    backup_configuration {
      enabled            = true
      start_time         = "02:00" # 2 AM
      binary_log_enabled = false
    }
    
    # IP-Konfiguration (für Produktion anpassen)
    ip_configuration {
      ipv4_enabled        = true
      require_ssl         = true
      private_network     = null # Für Private Service Connect oder VPC-Peering
    }
    
    # Aktiviere pgvector-Erweiterung via database flags
    database_flags {
      name  = "cloudsql.enable_pgvector"
      value = "on"
    }
  }
  
  # Löschschutz (für Produktion auf true setzen)
  deletion_protection = false
}

# Datenbank erstellen
resource "google_sql_database" "rag_database" {
  name     = "rag_db"
  instance = google_sql_database_instance.postgres.name
}

# Datenbankbenutzer erstellen
resource "google_sql_user" "rag_user" {
  name     = "rag_user"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

# Zufälliges Passwort generieren
resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Passwort in Secret Manager speichern
resource "google_secret_manager_secret" "db_password_secret" {
  secret_id = "rag-db-password"
  
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "db_password_version" {
  secret      = google_secret_manager_secret.db_password_secret.id
  secret_data = random_password.db_password.result
}

# Vertex AI Vector Search Index
resource "google_vertex_ai_index" "vector_index" {
  provider    = google-beta
  display_name = "rag-document-vector-index"
  description = "Vector index for document embeddings"
  region      = var.region
  
  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.processed_bucket.name}/vectors"
    config {
      dimensions = var.embedding_dimension  # Für textembedding-gecko
      approximate_neighbors_count = 20
      distance_measure_type = "DOT_PRODUCT_DISTANCE"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 500
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }
}

# Vector Search Endpoint
resource "google_vertex_ai_index_endpoint" "vector_endpoint" {
  provider     = google-beta
  display_name = "rag-vector-endpoint"
  region       = var.region
  
  network      = "projects/${var.project_id}/global/networks/default"
}

# Deployment des Index auf dem Endpoint
resource "google_vertex_ai_index_endpoint_deployment" "deployment" {
  provider            = google-beta
  index_endpoint      = google_vertex_ai_index_endpoint.vector_endpoint.id
  
  deployed_index {
    index           = google_vertex_ai_index.vector_index.id
    display_name    = "rag-deployed-index"
    
    # Automatische Ressourcenanpassung
    automatic_resources {
      min_replica_count = 1
      max_replica_count = 2
    }
  }
}

# Artifact Registry Repository für Docker-Images
resource "google_artifact_registry_repository" "docker_repo" {
  provider      = google-beta
  location      = var.region
  repository_id = "rag-docker-repo"
  description   = "Docker repository for RAG applications"
  format        = "DOCKER"
}

# Service Accounts
resource "google_service_account" "cloud_function_sa" {
  account_id   = var.cloud_function_sa_name
  display_name = "Service Account for RAG Document Processor"
  description  = "Used by Cloud Functions to process documents, access GCS, Document AI, Vertex AI and Cloud SQL"
}

resource "google_service_account" "cloudrun_sa" {
  account_id   = var.cloudrun_sa_name
  display_name = "Service Account for RAG API"
  description  = "Used by Cloud Run to serve the RAG API, access Vector Search, Cloud SQL and Vertex AI"
}

# IAM Berechtigungen für Cloud Function Service Account
resource "google_project_iam_member" "cf_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

resource "google_project_iam_member" "cf_document_ai_user" {
  project = var.project_id
  role    = "roles/documentai.user"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

resource "google_project_iam_member" "cf_ai_platform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

resource "google_project_iam_member" "cf_cloud_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

resource "google_project_iam_member" "cf_secretmanager_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# IAM Berechtigungen für Cloud Run Service Account
resource "google_project_iam_member" "cr_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

resource "google_project_iam_member" "cr_ai_platform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

resource "google_project_iam_member" "cr_cloud_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

resource "google_project_iam_member" "cr_secretmanager_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

locals {
  organization                     = "strisys"
  project_tag                      = "aisearch"
  azure_location                   = "eastus"
  azure_resource_group_name        = "rg-${local.organization}-${local.project_tag}"
  azure_resource_group_name_shared = "rg-shared"
  date_tag                         = formatdate("YYYYMMDD", timestamp())
  time_tag                         = formatdate("HHmmss", timestamp())
  datetime_tag                     = formatdate("YYYYMMDD-HHmmss", timestamp())
  current_date_est                 = formatdate("YYYYMMDD", timeadd(timestamp(), "-5h"))
  azure_web_app_ip                 = "38.140.3.2"

  container_names = [
    "hoisington",
    "taxes",
  ]

  openai_account_name     = "${local.organization}-${local.project_tag}-aisearch"
  openai_embedding_model  = "text-embedding-ada-002"
  openai_embedding_deploy = "embeddings"

  search_service_name = "${local.organization}-${local.project_tag}-aisearch"
  #   search_data_source_name = "ds-blob-docs"
  #   search_indexer_name     = "idx-blob-docs"

  search_api_version = "2024-07-01" # Microsoft.Search (indexes/indexers/dataSources/skillsets)
  openai_api_version = "2024-06-01"
}


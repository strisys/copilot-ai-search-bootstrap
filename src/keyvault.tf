locals {
  _target_container       = contains(local.container_names, "docsearch") ? "docsearch" : local.container_names[0]
  search_index_name       = "${replace(local._target_container, "[^a-zA-Z0-9-_]", "-")}-index"
  openai_api_version_default = "2024-06-01"
  max_chars_default          = 1200
  overlap_default            = 200
}

resource "azurerm_key_vault" "app_kv" {
  provider                   = azurerm.azure-default
  name                       = "kv-${local.organization}-${local.project_tag}"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  purge_protection_enabled   = true
  soft_delete_retention_days = 7
  public_network_access_enabled = true
  enabled_for_disk_encryption = true

  tags = {
    environment = var.environment
    organization = local.organization
    project      = local.project_tag
    date         = local.date_tag
  }
}

locals {
  search_endpoint = "https://${azurerm_search_service.search.name}.search.windows.net"
}

resource "azurerm_key_vault_secret" "azure_search_endpoint" {
  provider     = azurerm.azure-default
  name         = "AZURE-SEARCH-ENDPOINT"
  value        = local.search_endpoint
  key_vault_id = azurerm_key_vault.app_kv.id
}

resource "azurerm_key_vault_secret" "azure_search_api_key" {
  provider     = azurerm.azure-default
  name         = "AZURE-SEARCH-API-KEY"
  value        = azurerm_search_service.search.primary_key
  key_vault_id = azurerm_key_vault.app_kv.id
}

# Choose the index derived from the preferred container ("docsearch" -> "docsearch-index")
resource "azurerm_key_vault_secret" "azure_search_index" {
  provider     = azurerm.azure-default
  name         = "AZURE-SEARCH-INDEX"
  value        = local.search_index_name
  key_vault_id = azurerm_key_vault.app_kv.id
}

resource "azurerm_key_vault_secret" "azure_search_semantic_configuration" {
  provider     = azurerm.azure-default
  name         = "AZURE-SEARCH-SEMANTIC-SEARCH-CONFIGURATION"
  value        = "default"
  key_vault_id = azurerm_key_vault.app_kv.id
}


resource "azurerm_key_vault_secret" "azure_openai_endpoint" {
  provider     = azurerm.azure-default
  name         = "AZURE-OPENAI-ENDPOINT"
  value        = azurerm_cognitive_account.openai.endpoint
  key_vault_id = azurerm_key_vault.app_kv.id
}

resource "azurerm_key_vault_secret" "azure_openai_api_key" {
  provider     = azurerm.azure-default
  name         = "AZURE-OPENAI-API-KEY"
  value        = azurerm_cognitive_account.openai.primary_access_key
  key_vault_id = azurerm_key_vault.app_kv.id
}

resource "azurerm_key_vault_secret" "azure_openai_embeddings_deployment" {
  provider     = azurerm.azure-default
  name         = "AZURE-OPENAI-EMBEDDINGS-DEPLOYMENT"
  value        = azurerm_cognitive_deployment.embedding.name
  key_vault_id = azurerm_key_vault.app_kv.id
}

resource "azurerm_key_vault_secret" "azure_openai_api_version" {
  provider     = azurerm.azure-default
  name         = "AZURE-OPENAI-API-VERSION"
  value        = local.openai_api_version_default
  key_vault_id = azurerm_key_vault.app_kv.id
}

resource "azurerm_key_vault_secret" "max_chars" {
  provider     = azurerm.azure-default
  name         = "MAX-CHARS"
  value        = tostring(local.max_chars_default)
  key_vault_id = azurerm_key_vault.app_kv.id
}

resource "azurerm_key_vault_secret" "overlap" {
  provider     = azurerm.azure-default
  name         = "OVERLAP"
  value        = tostring(local.overlap_default)
  key_vault_id = azurerm_key_vault.app_kv.id
}

output "key_vault_name" {
  value       = azurerm_key_vault.app_kv.name
  description = "Name of the created Key Vault."
}

output "key_vault_uri" {
  value       = azurerm_key_vault.app_kv.vault_uri
  description = "URI of the created Key Vault."
}

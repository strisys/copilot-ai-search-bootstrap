locals {
  location          = azurerm_resource_group.rg.location
  rg_name           = azurerm_resource_group.rg.name
  scripts_base_path = "${path.module}/scripts/11.5.3"
}

resource "azurerm_search_service" "search" {
  provider            = azurerm.azure-default
  name                = local.search_service_name
  location            = local.location
  resource_group_name = local.rg_name
  sku                 = "standard"
  partition_count     = 1
  replica_count       = 1
  semantic_search_sku = "standard"

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_role_assignment" "search_sa_reader" {
  provider             = azurerm.azure-default
  scope                = azurerm_storage_account.storage_account.id
  principal_id         = azurerm_search_service.search.identity[0].principal_id
  role_definition_name = "Storage Blob Data Reader"
}

resource "azurerm_role_assignment" "search_can_use_openai" {
  provider             = azurerm.azure-default
  scope                = azurerm_cognitive_account.openai.id
  principal_id         = azurerm_search_service.search.identity[0].principal_id
  role_definition_name = "Cognitive Services OpenAI Contributor"
}

locals {
  datasource_script = "${local.scripts_base_path}/create_search_datasource.py"
  index_script      = "${local.scripts_base_path}/create_search_index.py"
  skillset_script   = "${local.scripts_base_path}/create_search_skillset.py"
  indexer_script    = "${local.scripts_base_path}/create_search_indexer.py"

  datasource_script_hash = filesha256(local.datasource_script)
  index_script_hash      = filesha256(local.index_script)
  skillset_script_hash   = filesha256(local.skillset_script)
  indexer_script_hash    = filesha256(local.indexer_script)

  datasource_config = {
    for container in local.container_names : container => {
      subscription_id     = data.azurerm_client_config.current.subscription_id
      name                = "${replace(container, "[^a-zA-Z0-9-_]", "-")}-ds"
      container_name      = container
      storage_account_id  = azurerm_storage_account.storage_account.id
      search_service_name = azurerm_search_service.search.name
      resource_group_name = azurerm_search_service.search.resource_group_name
    }
  }

  index_config = {
    for container in local.container_names : container => {
      subscription_id         = data.azurerm_client_config.current.subscription_id
      name                    = "${replace(container, "[^a-zA-Z0-9-_]", "-")}-index"
      container_name          = "${container}"
      search_service_name     = azurerm_search_service.search.name
      resource_group_name     = azurerm_search_service.search.resource_group_name
      azure_openai_endpoint   = azurerm_cognitive_account.openai.endpoint
      embedding_deployment_id = azurerm_cognitive_deployment.embedding.name
      embedding_model_name    = azurerm_cognitive_deployment.embedding.model[0].name
    }
  }

  skillset_config = {
    for container in local.container_names : container => {
      subscription_id         = data.azurerm_client_config.current.subscription_id
      name                    = "${replace(container, "[^a-zA-Z0-9-_]", "-")}-skillset"
      index_name              = "${replace(container, "[^a-zA-Z0-9-_]", "-")}-index"
      search_service_name     = azurerm_search_service.search.name
      resource_group_name     = azurerm_search_service.search.resource_group_name
      azure_openai_endpoint   = azurerm_cognitive_account.openai.endpoint
      azure_openai_key        = azurerm_cognitive_account.openai.primary_access_key
      embedding_deployment_id = azurerm_cognitive_deployment.embedding.name
      embedding_model_name    = azurerm_cognitive_deployment.embedding.model[0].name
    }
  }

  indexer_config = {
    for container in local.container_names : container => {
      subscription_id     = data.azurerm_client_config.current.subscription_id
      name                = "${replace(container, "[^a-zA-Z0-9-_]", "-")}-indexer"
      datasource_name     = "${replace(container, "[^a-zA-Z0-9-_]", "-")}-ds"
      skillset_name       = "${replace(container, "[^a-zA-Z0-9-_]", "-")}-skillset"
      index_name          = "${replace(container, "[^a-zA-Z0-9-_]", "-")}-index"
      search_service_name = azurerm_search_service.search.name
      resource_group_name = azurerm_search_service.search.resource_group_name
    }
  }

  # Create a combined hash of scripts + config for change detection
  combined_hash = sha256(jsonencode({
    data_source_script_hash = local.datasource_script_hash
    index_script_hash       = local.index_script_hash
    skillset_script_hash    = local.skillset_script_hash
    indexer_script_hash     = local.indexer_script_hash
    datasource_config       = local.datasource_config
    index_config            = local.index_config
    skillset_config         = local.skillset_config
    indexer_config          = local.indexer_config
  }))
}

resource "null_resource" "search_datasources" {
  for_each = local.datasource_config

  triggers = {
    script_path         = local.datasource_script
    script_hash         = local.datasource_script_hash
    config_hash         = sha256(jsonencode(each.value))
    combined_hash       = local.combined_hash
    search_service      = azurerm_search_service.search.id
    storage_account     = azurerm_storage_account.storage_account.id
    search_service_name = each.value.search_service_name
    resource_group_name = each.value.resource_group_name
    datasource_name     = each.value.name
    subscription_id     = each.value.subscription_id
  }

  provisioner "local-exec" {
    command = "python3 ${local.datasource_script}"

    environment = {
      AZURE_SUBSCRIPTION_ID = each.value.subscription_id
      SEARCH_SERVICE_NAME   = each.value.search_service_name
      RESOURCE_GROUP_NAME   = each.value.resource_group_name
      DATASOURCE_NAME       = each.value.name
      CONTAINER_NAME        = each.value.container_name
      STORAGE_ACCOUNT_ID    = each.value.storage_account_id
      OPERATION             = "create"
    }
  }

  provisioner "local-exec" {
    when    = destroy
    command = "python3 ${self.triggers.script_path}"

    environment = {
      AZURE_SUBSCRIPTION_ID = self.triggers.subscription_id
      SEARCH_SERVICE_NAME   = self.triggers.search_service_name
      RESOURCE_GROUP_NAME   = self.triggers.resource_group_name
      DATASOURCE_NAME       = self.triggers.datasource_name
      OPERATION             = "delete"
    }

    on_failure = continue
  }

  depends_on = [
    azurerm_search_service.search,
    azurerm_storage_account.storage_account
  ]
}

resource "null_resource" "search_indexes" {
  for_each = local.index_config

  triggers = {
    script_path           = local.index_script
    script_hash           = local.index_script_hash
    config_hash           = sha256(jsonencode(each.value))
    combined_hash         = local.combined_hash
    search_service        = azurerm_search_service.search.id
    azure_openai_endpoint = each.value.azure_openai_endpoint
    search_service_name   = each.value.search_service_name
    resource_group_name   = each.value.resource_group_name
    index_name            = each.value.name
    subscription_id       = each.value.subscription_id
  }

  provisioner "local-exec" {
    command = "python3 ${local.index_script}"

    environment = {
      AZURE_SUBSCRIPTION_ID   = each.value.subscription_id
      SEARCH_SERVICE_NAME     = each.value.search_service_name
      RESOURCE_GROUP_NAME     = each.value.resource_group_name
      INDEX_NAME              = each.value.name
      CONTAINER_NAME          = each.value.container_name
      AZURE_OPENAI_ENDPOINT   = each.value.azure_openai_endpoint
      EMBEDDING_DEPLOYMENT_ID = each.value.embedding_deployment_id
      EMBEDDING_MODEL_NAME    = each.value.embedding_model_name
      OPERATION               = "create"
    }
  }

  provisioner "local-exec" {
    when    = destroy
    command = "python3 ${self.triggers.script_path}"

    environment = {
      AZURE_SUBSCRIPTION_ID = self.triggers.subscription_id
      SEARCH_SERVICE_NAME   = self.triggers.search_service_name
      RESOURCE_GROUP_NAME   = self.triggers.resource_group_name
      INDEX_NAME            = self.triggers.index_name
      OPERATION             = "delete"
    }
  }

  depends_on = [
    azurerm_search_service.search,
    null_resource.search_datasources
  ]
}

resource "null_resource" "search_skillsets" {
  for_each = local.skillset_config

  triggers = {
    script_path         = local.skillset_script
    script_hash         = local.skillset_script_hash
    config_hash         = sha256(jsonencode(each.value))
    combined_hash       = local.combined_hash
    search_service      = azurerm_search_service.search.id
    index_name          = each.value.index_name
    search_service_name = each.value.search_service_name
    resource_group_name = each.value.resource_group_name
    skillset_name       = each.value.name
    subscription_id     = each.value.subscription_id
  }

  provisioner "local-exec" {
    command = "python3 ${local.skillset_script}"

    environment = {
      AZURE_SUBSCRIPTION_ID   = each.value.subscription_id
      SEARCH_SERVICE_NAME     = each.value.search_service_name
      RESOURCE_GROUP_NAME     = each.value.resource_group_name
      SKILLSET_NAME           = each.value.name
      INDEX_NAME              = each.value.index_name
      AZURE_OPENAI_ENDPOINT   = each.value.azure_openai_endpoint
      AZURE_OPENAI_API_KEY    = each.value.azure_openai_key
      EMBEDDING_DEPLOYMENT_ID = each.value.embedding_deployment_id
      EMBEDDING_MODEL_NAME    = each.value.embedding_model_name
      OPERATION               = "create"
    }
  }

  provisioner "local-exec" {
    when    = destroy
    command = "python3 ${self.triggers.script_path}"

    environment = {
      AZURE_SUBSCRIPTION_ID = self.triggers.subscription_id
      SEARCH_SERVICE_NAME   = self.triggers.search_service_name
      RESOURCE_GROUP_NAME   = self.triggers.resource_group_name
      SKILLSET_NAME         = self.triggers.skillset_name
      OPERATION             = "delete"
    }
  }

  depends_on = [
    azurerm_search_service.search,
    null_resource.search_indexes,
    null_resource.search_datasources
  ]
}

resource "null_resource" "search_indexers" {
  for_each = local.indexer_config

  triggers = {
    script_path         = local.skillset_script
    script_hash         = local.indexer_script_hash
    config_hash         = sha256(jsonencode(each.value))
    combined_hash       = local.combined_hash
    search_service      = azurerm_search_service.search.id
    storage_account     = azurerm_storage_account.storage_account.id
    search_service_name = each.value.search_service_name
    resource_group_name = each.value.resource_group_name
    indexer_name        = each.value.name
    subscription_id     = each.value.subscription_id
  }

  # Create the indexer
  provisioner "local-exec" {
    command = "python3 ${local.indexer_script}"

    environment = {
      AZURE_SUBSCRIPTION_ID = each.value.subscription_id
      SEARCH_SERVICE_NAME   = each.value.search_service_name
      RESOURCE_GROUP_NAME   = each.value.resource_group_name
      INDEXER_NAME          = each.value.name
      DATASOURCE_NAME       = each.value.datasource_name
      SKILLSET_NAME         = each.value.skillset_name
      INDEX_NAME            = each.value.index_name
      OPERATION             = "create"
    }
  }

  # Clean up on destroy
  provisioner "local-exec" {
    when    = destroy
    command = "python3 ${self.triggers.script_path}"

    environment = {
      AZURE_SUBSCRIPTION_ID = self.triggers.subscription_id
      SEARCH_SERVICE_NAME   = self.triggers.search_service_name
      RESOURCE_GROUP_NAME   = self.triggers.resource_group_name
      INDEXER_NAME          = self.triggers.indexer_name
      OPERATION             = "delete"
    }
  }

  depends_on = [
    null_resource.search_skillsets,
    null_resource.search_indexes,
    null_resource.search_datasources
  ]
}

# # Output the skillset information
# output "search_skillsets" {
#   value = {
#     for k, v in null_resource.search_skillsets : k => {
#       name          = local.skillset_config[k].name
#       index_name    = local.skillset_config[k].index_name
#       triggers_hash = v.triggers.combined_hash
#     }
#   }
# }

# # Output the datasource information
# output "search_datasources" {
#   value = {
#     for k, v in null_resource.search_datasources : k => {
#       name           = local.datasource_config[k].name
#       container_name = local.datasource_config[k].container_name
#       triggers_hash  = v.triggers.combined_hash
#     }
#   }
# }
resource "azurerm_cognitive_account" "openai" {
  provider              = azurerm.azure-default
  name                  = local.openai_account_name
  custom_subdomain_name = local.openai_account_name
  location              = azurerm_resource_group.rg.location
  resource_group_name   = azurerm_resource_group.rg.name
  kind                  = "OpenAI"
  sku_name              = "S0"
}

resource "azurerm_cognitive_deployment" "embedding" {
  provider             = azurerm.azure-default
  name                 = local.openai_embedding_deploy
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = local.openai_embedding_model
    version = "1"
  }

  sku {
    name     = "Standard"
    capacity = 10
  }
}

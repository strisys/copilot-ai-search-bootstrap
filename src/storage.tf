resource "azurerm_storage_account" "storage_account" {
  provider                        = azurerm.azure-default
  name                            = "${local.organization}${local.project_tag}"
  resource_group_name             = azurerm_resource_group.rg.name
  location                        = azurerm_resource_group.rg.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  allow_nested_items_to_be_public = false
  min_tls_version                 = "TLS1_2"
}

resource "azurerm_storage_container" "containers" {
  for_each              = toset(local.container_names)
  provider              = azurerm.azure-default
  storage_account_id    = azurerm_storage_account.storage_account.id
  name                  = each.value
  container_access_type = "private"
}
